"""
Semantic search service integrating ChromaDB embeddings with LightRAG RAG capabilities.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from app.core.config import settings
from app.core.vector_db import vector_db
from app.services.knowledge_graph import knowledge_graph_service
from app.models.schemas import SearchResult, SearchQuery, RAGQuery, RAGResponse
from app.core.exceptions import SearchError

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Semantic search service that combines ChromaDB vector similarity search
    with LightRAG's RAG capabilities for comprehensive question answering.
    """
    
    def __init__(self):
        """Initialize the semantic search service."""
        self.vector_db = vector_db
        self.knowledge_graph = knowledge_graph_service
        self._initialize_lightrag_query()
    
    def _initialize_lightrag_query(self):
        """Initialize LightRAG query capabilities."""
        try:
            from lightrag import QueryParam
            self.QueryParam = QueryParam
            self.lightrag_available = True
            logger.info("LightRAG query capabilities initialized")
        except ImportError:
            logger.warning("LightRAG not available for RAG queries")
            self.lightrag_available = False
    
    async def semantic_search(
        self, 
        query: str, 
        limit: int = 10,
        content_types: Optional[List[str]] = None,
        similarity_threshold: float = 0.7,
        include_metadata: bool = True
    ) -> List[SearchResult]:
        """
        Perform semantic search using ChromaDB vector similarity.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            content_types: Filter by content types ('document', 'note')
            similarity_threshold: Minimum similarity score for results
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of search results with similarity scores
        """
        try:
            logger.info(f"Performing semantic search for query: '{query[:50]}...'")
            
            # Prepare metadata filters
            where_filters = {}
            if content_types:
                where_filters["content_type"] = {"$in": content_types}
            
            # Perform vector similarity search
            search_results = await self.vector_db.similarity_search(
                query=query,
                n_results=limit,
                where=where_filters if where_filters else None
            )
            
            if not search_results or not search_results.get("results"):
                logger.info("No search results found")
                return []
            
            # Process results
            results = []
            search_items = search_results["results"]
            
            for i, item in enumerate(search_items):
                # Get similarity score (already calculated in vector_db)
                similarity_score = item.get("relevance_score", 0.0)
                
                # Filter by similarity threshold
                if similarity_score < similarity_threshold:
                    continue
                
                # Create search result
                result = SearchResult(
                    id=item.get("id", ""),
                    content=item.get("document", ""),
                    similarity_score=similarity_score,
                    content_type=item.get("metadata", {}).get("content_type", "unknown"),
                    metadata=item.get("metadata", {}) if include_metadata else {},
                    rank=i + 1
                )
                
                results.append(result)
            
            logger.info(f"Found {len(results)} semantic search results")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise SearchError(f"Semantic search failed: {e}")
    
    async def rag_query(
        self,
        query: str,
        mode: str = "hybrid",
        max_tokens: int = 2000,
        include_sources: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """
        Perform RAG-based question answering using LightRAG.
        
        Args:
            query: Question to answer
            mode: RAG mode ('naive', 'local', 'global', 'hybrid', 'mix')
            max_tokens: Maximum tokens for response
            include_sources: Whether to include source citations
            conversation_history: Previous conversation turns
            
        Returns:
            RAG response with answer and sources
        """
        try:
            if not self.lightrag_available:
                raise SearchError("LightRAG not available for RAG queries")
            
            if not self.knowledge_graph.lightrag:
                raise SearchError("LightRAG not initialized in knowledge graph service")
            
            logger.info(f"Performing RAG query with mode '{mode}': '{query[:50]}...'")
            
            # Prepare query parameters
            query_param = self.QueryParam(
                mode=mode,
                only_need_context=False,
                response_type="Multiple Paragraphs",
                stream=False
            )
            
            # Add conversation history if provided
            if conversation_history:
                query_param.conversation_history = conversation_history
                query_param.history_turns = min(len(conversation_history), 5)
            
            # Perform RAG query
            start_time = datetime.utcnow()
            
            if hasattr(self.knowledge_graph.lightrag, 'aquery'):
                # Use async query if available
                response = await self.knowledge_graph.lightrag.aquery(query, param=query_param)
            else:
                # Fallback to sync query
                response = self.knowledge_graph.lightrag.query(query, param=query_param)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract sources if requested
            sources = []
            if include_sources:
                sources = await self._extract_rag_sources(query, mode)
            
            # Create RAG response
            rag_response = RAGResponse(
                query=query,
                answer=response,
                mode=mode,
                sources=sources,
                processing_time=processing_time,
                token_count=len(response.split()) if isinstance(response, str) else 0
            )
            
            logger.info(f"RAG query completed in {processing_time:.2f}s")
            return rag_response
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise SearchError(f"RAG query failed: {e}")
    
    async def hybrid_search(
        self,
        query: str,
        semantic_limit: int = 5,
        rag_mode: str = "hybrid",
        include_semantic_results: bool = True,
        include_rag_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining semantic search and RAG query.
        
        Args:
            query: Search query
            semantic_limit: Number of semantic search results
            rag_mode: RAG query mode
            include_semantic_results: Whether to include semantic search results
            include_rag_answer: Whether to include RAG answer
            
        Returns:
            Combined search results with both semantic matches and RAG answer
        """
        try:
            logger.info(f"Performing hybrid search for: '{query[:50]}...'")
            
            results = {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "semantic_results": [],
                "rag_response": None
            }
            
            # Perform semantic search
            if include_semantic_results:
                try:
                    semantic_results = await self.semantic_search(
                        query=query,
                        limit=semantic_limit,
                        similarity_threshold=0.6
                    )
                    results["semantic_results"] = [result.dict() for result in semantic_results]
                except Exception as e:
                    logger.warning(f"Semantic search failed in hybrid search: {e}")
                    results["semantic_results"] = []
            
            # Perform RAG query
            if include_rag_answer and self.lightrag_available:
                try:
                    rag_response = await self.rag_query(
                        query=query,
                        mode=rag_mode,
                        include_sources=True
                    )
                    results["rag_response"] = rag_response.dict()
                except Exception as e:
                    logger.warning(f"RAG query failed in hybrid search: {e}")
                    results["rag_response"] = None
            
            logger.info("Hybrid search completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise SearchError(f"Hybrid search failed: {e}")
    
    async def _extract_rag_sources(self, query: str, mode: str) -> List[Dict[str, Any]]:
        """Extract source citations from RAG query context."""
        try:
            # This is a simplified source extraction
            # In a real implementation, you'd extract this from LightRAG's context
            
            # Perform a semantic search to find relevant sources
            semantic_results = await self.semantic_search(
                query=query,
                limit=3,
                similarity_threshold=0.7
            )
            
            sources = []
            for result in semantic_results:
                source = {
                    "id": result.id,
                    "content_type": result.content_type,
                    "similarity_score": result.similarity_score,
                    "snippet": result.content[:200] + "..." if len(result.content) > 200 else result.content
                }
                
                # Add additional metadata based on content type
                if result.metadata:
                    if result.content_type == "document":
                        source.update({
                            "filename": result.metadata.get("filename", ""),
                            "file_type": result.metadata.get("file_type", "")
                        })
                    elif result.content_type == "note":
                        source.update({
                            "title": result.metadata.get("title", ""),
                            "tags": result.metadata.get("tags", [])
                        })
                
                sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.warning(f"Failed to extract RAG sources: {e}")
            return []
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on partial query.
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of search suggestions
        """
        try:
            if len(partial_query) < 2:
                return []
            
            # Perform a broad semantic search
            results = await self.semantic_search(
                query=partial_query,
                limit=limit * 2,
                similarity_threshold=0.5
            )
            
            # Extract unique terms and phrases from results
            suggestions = set()
            
            for result in results:
                content = result.content.lower()
                words = content.split()
                
                # Find phrases containing the partial query
                partial_lower = partial_query.lower()
                for i, word in enumerate(words):
                    if partial_lower in word:
                        # Add the word itself
                        suggestions.add(word)
                        
                        # Add phrases around the word
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        phrase = " ".join(words[start:end])
                        if len(phrase) <= 50:  # Reasonable phrase length
                            suggestions.add(phrase)
            
            # Convert to list and sort by relevance (length as proxy)
            suggestions_list = list(suggestions)
            suggestions_list.sort(key=len)
            
            return suggestions_list[:limit]
            
        except Exception as e:
            logger.warning(f"Failed to get search suggestions: {e}")
            return []
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search system statistics."""
        try:
            # Get vector database stats
            vector_stats = await self.vector_db.get_collection_stats()
            
            # Get knowledge graph stats
            graph_stats = {
                "nodes": self.knowledge_graph.graph.number_of_nodes(),
                "edges": self.knowledge_graph.graph.number_of_edges()
            }
            
            return {
                "vector_database": vector_stats,
                "knowledge_graph": graph_stats,
                "lightrag_available": self.lightrag_available,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {}


# Global instance
semantic_search_service = SemanticSearchService()