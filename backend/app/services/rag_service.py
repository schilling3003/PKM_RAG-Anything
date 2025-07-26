"""
RAG (Retrieval-Augmented Generation) service for question answering.
"""

import os
import json
import asyncio
import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib

from app.core.config import settings
from app.services.knowledge_graph import knowledge_graph_service
from app.services.semantic_search import semantic_search_service
from app.core.database import get_db
from app.models.database import RAGQueryHistory
from app.models.schemas import RAGQuery, RAGResponse
from app.core.exceptions import SearchError, ExternalServiceError, DatabaseError
from app.core.service_health import service_health_monitor
from app.core.retry_utils import (
    retry_with_backoff, 
    RetryConfig, 
    with_graceful_degradation,
    retry_database_operation
)

logger = structlog.get_logger(__name__)


@dataclass
class RAGContext:
    """Context information for RAG queries."""
    query: str
    mode: str
    retrieved_chunks: List[Dict[str, Any]]
    knowledge_graph_context: List[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, str]]]
    timestamp: datetime


class RAGQueryCache:
    """Simple in-memory cache for RAG query results."""
    
    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        self.cache = {}
        self.max_size = max_size
        self.ttl_hours = ttl_hours
    
    def _generate_key(self, query: str, mode: str, context_hash: str) -> str:
        """Generate cache key for query."""
        combined = f"{query}:{mode}:{context_hash}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, query: str, mode: str, context_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        key = self._generate_key(query, mode, context_hash)
        
        if key in self.cache:
            cached_item = self.cache[key]
            if datetime.utcnow() - cached_item["timestamp"] < timedelta(hours=self.ttl_hours):
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_item["result"]
            else:
                # Remove expired item
                del self.cache[key]
        
        return None
    
    def set(self, query: str, mode: str, context_hash: str, result: Dict[str, Any]):
        """Cache query result."""
        key = self._generate_key(query, mode, context_hash)
        
        # Remove oldest item if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "result": result,
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Cached result for query: {query[:50]}...")
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
        logger.info("RAG query cache cleared")


class RAGService:
    """
    RAG service for comprehensive question answering using multiple retrieval modes.
    """
    
    def __init__(self):
        """Initialize the RAG service."""
        self.knowledge_graph = knowledge_graph_service
        self.semantic_search = semantic_search_service
        self.cache = RAGQueryCache()
        self._initialize_lightrag()
    
    def _initialize_lightrag(self):
        """Initialize LightRAG query capabilities."""
        try:
            from lightrag import QueryParam
            self.QueryParam = QueryParam
            self.lightrag_available = True
            logger.info("RAG service initialized with LightRAG support")
        except ImportError:
            logger.warning("LightRAG not available for RAG queries")
            self.lightrag_available = False
    
    @retry_with_backoff(
        config=RetryConfig(max_retries=2, backoff_factor=1.5),
        service_name="lightrag",
        operation_name="rag_query"
    )
    async def process_rag_query(
        self,
        query: str,
        mode: str = "hybrid",
        max_tokens: int = 2000,
        include_sources: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_cache: bool = True
    ) -> RAGResponse:
        """
        Process a RAG query with comprehensive context retrieval and answer generation.
        
        Args:
            query: The question to answer
            mode: RAG mode ('naive', 'local', 'global', 'hybrid', 'mix')
            max_tokens: Maximum tokens for the response
            include_sources: Whether to include source citations
            conversation_history: Previous conversation turns
            use_cache: Whether to use cached results
            
        Returns:
            RAG response with answer and sources
        """
        start_time = datetime.utcnow()
        
        query_context = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "mode": mode,
            "max_tokens": max_tokens,
            "include_sources": include_sources,
            "has_conversation_history": bool(conversation_history),
            "use_cache": use_cache,
            "operation": "rag_query"
        }
        
        try:
            logger.info("Processing RAG query", **query_context)
            
            # Validate query
            if not query or not query.strip():
                raise SearchError(
                    "Empty query provided",
                    details=query_context,
                    user_message="Please provide a question to search for.",
                    recovery_suggestions=[
                        "Enter a specific question or search term",
                        "Try asking about topics in your knowledge base",
                        "Use keywords related to your documents"
                    ]
                )
            
            # Check if query is too long
            if len(query) > 1000:
                raise SearchError(
                    "Query too long",
                    details=query_context,
                    user_message="Your question is too long. Please make it more concise.",
                    recovery_suggestions=[
                        "Shorten your question to the main points",
                        "Break complex questions into simpler parts",
                        "Focus on the most important aspects"
                    ]
                )
            
            # Generate context hash for caching
            context_hash = self._generate_context_hash(conversation_history)
            query_context["context_hash"] = context_hash
            
            # Check cache first
            if use_cache:
                try:
                    cached_result = self.cache.get(query, mode, context_hash)
                    if cached_result:
                        logger.info("Returning cached RAG result", **query_context)
                        return RAGResponse(**cached_result)
                except Exception as e:
                    logger.warning("Cache retrieval failed", error=str(e), **query_context)
            
            # Build comprehensive context
            context = await self._build_rag_context(
                query=query,
                mode=mode,
                conversation_history=conversation_history
            )
            
            # Generate answer using LightRAG
            answer = await self._generate_rag_answer(
                context=context,
                max_tokens=max_tokens
            )
            
            # Extract and format sources
            sources = []
            if include_sources:
                try:
                    sources = await self._extract_and_format_sources(context)
                except Exception as e:
                    logger.warning("Source extraction failed", error=str(e), **query_context)
                    sources = []
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create response
            response = RAGResponse(
                query=query,
                answer=answer,
                mode=mode,
                sources=sources,
                processing_time=processing_time,
                token_count=len(answer.split()) if isinstance(answer, str) else 0
            )
            
            # Cache the result
            if use_cache:
                try:
                    self.cache.set(query, mode, context_hash, response.dict())
                except Exception as e:
                    logger.warning("Cache storage failed", error=str(e), **query_context)
            
            # Save to query history
            try:
                await self._save_query_history(query, mode, response)
            except Exception as e:
                logger.warning("Query history save failed", error=str(e), **query_context)
            
            logger.info("RAG query completed successfully", 
                       processing_time=processing_time,
                       answer_length=len(answer),
                       sources_count=len(sources),
                       **query_context)
            
            return response
            
        except SearchError:
            # Re-raise SearchError with context
            raise
        except Exception as e:
            logger.error("RAG query failed", error=str(e), **query_context)
            raise SearchError(
                f"RAG query failed: {str(e)}",
                details=query_context,
                user_message="Failed to process your question. Please try again with a different query.",
                recovery_suggestions=[
                    "Try rephrasing your question",
                    "Use simpler language or keywords",
                    "Check if your knowledge base contains relevant content",
                    "Contact support if the issue persists"
                ]
            )
    
    async def _build_rag_context(
        self,
        query: str,
        mode: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGContext:
        """Build comprehensive context for RAG query."""
        try:
            # Retrieve relevant chunks using semantic search
            semantic_results = await self.semantic_search.semantic_search(
                query=query,
                limit=10,
                similarity_threshold=0.6
            )
            
            retrieved_chunks = []
            for result in semantic_results:
                retrieved_chunks.append({
                    "content": result.content,
                    "source": result.id,
                    "content_type": result.content_type,
                    "similarity_score": result.similarity_score,
                    "metadata": result.metadata
                })
            
            # Get knowledge graph context (if available)
            kg_context = []
            try:
                # This would involve querying the knowledge graph for related entities
                # For now, we'll use a simplified approach
                kg_context = await self._get_knowledge_graph_context(query)
            except Exception as e:
                logger.warning(f"Failed to get knowledge graph context: {e}")
            
            return RAGContext(
                query=query,
                mode=mode,
                retrieved_chunks=retrieved_chunks,
                knowledge_graph_context=kg_context,
                conversation_history=conversation_history,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to build RAG context: {e}")
            raise
    
    async def _generate_rag_answer(
        self,
        context: RAGContext,
        max_tokens: int = 2000
    ) -> str:
        """Generate answer using LightRAG."""
        try:
            if not self.lightrag_available:
                return await self._generate_fallback_answer(context)
            
            if not self.knowledge_graph.lightrag:
                return await self._generate_fallback_answer(context)
            
            # Ensure LightRAG is properly initialized
            if not hasattr(self.knowledge_graph.lightrag, '_initialized'):
                success = await self.knowledge_graph._initialize_lightrag_async()
                if success:
                    self.knowledge_graph.lightrag._initialized = True
                else:
                    return await self._generate_fallback_answer(context)
            
            # Prepare query parameters
            query_param = self.QueryParam(
                mode=context.mode,
                only_need_context=False,
                response_type="Multiple Paragraphs",
                stream=False
            )
            
            # Add conversation history if provided
            if context.conversation_history:
                query_param.conversation_history = context.conversation_history
                query_param.history_turns = min(len(context.conversation_history), 5)
            
            # Perform RAG query using LightRAG
            if hasattr(self.knowledge_graph.lightrag, 'aquery') and hasattr(self.knowledge_graph.lightrag, '_initialized'):
                response = await self.knowledge_graph.lightrag.aquery(
                    context.query, 
                    param=query_param
                )
            elif hasattr(self.knowledge_graph.lightrag, 'query'):
                response = self.knowledge_graph.lightrag.query(
                    context.query, 
                    param=query_param
                )
            else:
                return await self._generate_fallback_answer(context)
            
            return response if isinstance(response, str) else str(response)
            
        except Exception as e:
            logger.warning(f"LightRAG answer generation failed: {e}")
            return await self._generate_fallback_answer(context)
    
    async def _generate_fallback_answer(self, context: RAGContext) -> str:
        """Generate a fallback answer when LightRAG is not available."""
        try:
            # Simple fallback: summarize the most relevant chunks
            if not context.retrieved_chunks:
                return "I don't have enough information to answer that question."
            
            # Get the top 3 most relevant chunks
            top_chunks = sorted(
                context.retrieved_chunks,
                key=lambda x: x.get("similarity_score", 0),
                reverse=True
            )[:3]
            
            # Create a simple answer based on retrieved content
            answer_parts = [
                f"Based on the available information, here's what I found:"
            ]
            
            for i, chunk in enumerate(top_chunks, 1):
                content = chunk["content"][:300] + "..." if len(chunk["content"]) > 300 else chunk["content"]
                answer_parts.append(f"\n{i}. {content}")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Fallback answer generation failed: {e}")
            return "I encountered an error while processing your question. Please try again."
    
    async def _get_knowledge_graph_context(self, query: str) -> List[Dict[str, Any]]:
        """Get relevant context from the knowledge graph."""
        try:
            # This is a simplified implementation
            # In a full implementation, you would:
            # 1. Extract entities from the query
            # 2. Find related entities in the knowledge graph
            # 3. Get relationship paths and context
            
            # For now, return empty context
            return []
            
        except Exception as e:
            logger.warning(f"Failed to get knowledge graph context: {e}")
            return []
    
    async def _extract_and_format_sources(self, context: RAGContext) -> List[Dict[str, Any]]:
        """Extract and format source citations."""
        try:
            sources = []
            
            for chunk in context.retrieved_chunks[:5]:  # Top 5 sources
                source = {
                    "id": chunk["source"],
                    "content_type": chunk["content_type"],
                    "similarity_score": chunk["similarity_score"],
                    "snippet": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
                }
                
                # Add metadata based on content type
                if chunk.get("metadata"):
                    metadata = chunk["metadata"]
                    if chunk["content_type"] == "document":
                        source.update({
                            "filename": metadata.get("filename", ""),
                            "file_type": metadata.get("file_type", "")
                        })
                    elif chunk["content_type"] == "note":
                        source.update({
                            "title": metadata.get("title", ""),
                            "tags": metadata.get("tags", [])
                        })
                
                sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.warning(f"Failed to extract sources: {e}")
            return []
    
    def _generate_context_hash(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Generate hash for conversation context."""
        if not conversation_history:
            return "no_history"
        
        history_str = json.dumps(conversation_history, sort_keys=True)
        return hashlib.md5(history_str.encode()).hexdigest()[:8]
    
    async def _save_query_history(self, query: str, mode: str, response: RAGResponse):
        """Save query to history database."""
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            
            history_entry = RAGQueryHistory(
                query=query,
                mode=mode,
                answer=response.answer,
                sources_count=len(response.sources),
                processing_time=response.processing_time,
                token_count=response.token_count
            )
            
            db.add(history_entry)
            db.commit()
            
        except Exception as e:
            logger.warning(f"Failed to save query history: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    async def get_query_history(
        self,
        limit: int = 50,
        mode_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get query history."""
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            
            query = db.query(RAGQueryHistory)
            
            if mode_filter:
                query = query.filter(RAGQueryHistory.mode == mode_filter)
            
            history = query.order_by(RAGQueryHistory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": entry.id,
                    "query": entry.query,
                    "mode": entry.mode,
                    "answer": entry.answer[:200] + "..." if len(entry.answer) > 200 else entry.answer,
                    "sources_count": entry.sources_count,
                    "processing_time": entry.processing_time,
                    "token_count": entry.token_count,
                    "created_at": entry.created_at.isoformat()
                }
                for entry in history
            ]
            
        except Exception as e:
            logger.error(f"Failed to get query history: {e}")
            return []
        finally:
            if 'db' in locals():
                db.close()
    
    async def clear_cache(self):
        """Clear the query cache."""
        self.cache.clear()
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics."""
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            
            # Get query counts by mode
            mode_counts = {}
            for mode in ["naive", "local", "global", "hybrid", "mix"]:
                count = db.query(RAGQueryHistory).filter(RAGQueryHistory.mode == mode).count()
                mode_counts[mode] = count
            
            # Get recent activity
            recent_queries = db.query(RAGQueryHistory).filter(
                RAGQueryHistory.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            total_queries = db.query(RAGQueryHistory).count()
            
            return {
                "total_queries": total_queries,
                "recent_queries_7d": recent_queries,
                "queries_by_mode": mode_counts,
                "cache_size": len(self.cache.cache),
                "lightrag_available": self.lightrag_available,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {}
        finally:
            if 'db' in locals():
                db.close()


# Global instance
rag_service = RAGService()