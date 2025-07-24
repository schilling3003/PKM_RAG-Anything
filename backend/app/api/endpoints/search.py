"""
Search API endpoints for semantic search and RAG queries.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
import logging

from app.services.semantic_search import semantic_search_service
from app.models.schemas import (
    SearchQuery, SearchResult, SearchResponse, 
    RAGQuery, RAGResponse, BaseResponse
)
from app.core.exceptions import SearchError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=Dict[str, Any])
async def semantic_search(
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    content_types: Optional[List[str]] = Query(None, description="Filter by content types"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    include_metadata: bool = Query(True, description="Include metadata in results")
):
    """
    Perform semantic search using vector similarity.
    
    Returns documents and notes ranked by semantic similarity to the query.
    """
    try:
        logger.info(f"Semantic search request: '{query[:50]}...'")
        
        results = await semantic_search_service.semantic_search(
            query=query,
            limit=limit,
            content_types=content_types,
            similarity_threshold=similarity_threshold,
            include_metadata=include_metadata
        )
        
        return {
            "success": True,
            "query": query,
            "results": [result.dict() for result in results],
            "total": len(results),
            "parameters": {
                "limit": limit,
                "content_types": content_types,
                "similarity_threshold": similarity_threshold
            }
        }
        
    except SearchError as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in semantic search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/rag", response_model=Dict[str, Any])
async def rag_query(
    query: str = Query(..., min_length=1, max_length=1000, description="Question to answer"),
    mode: str = Query("hybrid", regex="^(naive|local|global|hybrid|mix)$", description="RAG mode"),
    max_tokens: int = Query(2000, ge=100, le=8000, description="Maximum tokens for response"),
    include_sources: bool = Query(True, description="Include source citations"),
    conversation_history: Optional[str] = Query(None, description="JSON string of conversation history")
):
    """
    Perform RAG-based question answering.
    
    Uses LightRAG to generate comprehensive answers based on the knowledge graph
    and document collection.
    """
    try:
        logger.info(f"RAG query request: '{query[:50]}...' (mode: {mode})")
        
        # Parse conversation history if provided
        history = None
        if conversation_history:
            import json
            try:
                history = json.loads(conversation_history)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid conversation history JSON")
        
        response = await semantic_search_service.rag_query(
            query=query,
            mode=mode,
            max_tokens=max_tokens,
            include_sources=include_sources,
            conversation_history=history
        )
        
        return {
            "success": True,
            "response": response.dict()
        }
        
    except SearchError as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in RAG query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/hybrid", response_model=Dict[str, Any])
async def hybrid_search(
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    semantic_limit: int = Query(5, ge=1, le=50, description="Number of semantic results"),
    rag_mode: str = Query("hybrid", regex="^(naive|local|global|hybrid|mix)$", description="RAG mode"),
    include_semantic_results: bool = Query(True, description="Include semantic search results"),
    include_rag_answer: bool = Query(True, description="Include RAG answer")
):
    """
    Perform hybrid search combining semantic search and RAG query.
    
    Returns both semantically similar documents and a comprehensive RAG answer.
    """
    try:
        logger.info(f"Hybrid search request: '{query[:50]}...'")
        
        results = await semantic_search_service.hybrid_search(
            query=query,
            semantic_limit=semantic_limit,
            rag_mode=rag_mode,
            include_semantic_results=include_semantic_results,
            include_rag_answer=include_rag_answer
        )
        
        return {
            "success": True,
            **results
        }
        
    except SearchError as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in hybrid search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suggestions", response_model=Dict[str, Any])
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions")
):
    """
    Get search suggestions based on partial query.
    
    Returns suggested search terms and phrases based on existing content.
    """
    try:
        suggestions = await semantic_search_service.get_search_suggestions(
            partial_query=q,
            limit=limit
        )
        
        return {
            "success": True,
            "query": q,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Failed to get search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=Dict[str, Any])
async def get_search_stats():
    """
    Get search system statistics.
    
    Returns information about the vector database, knowledge graph,
    and search system status.
    """
    try:
        stats = await semantic_search_service.get_search_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reindex", response_model=BaseResponse)
async def reindex_search():
    """
    Trigger a full reindex of the search system.
    
    Rebuilds all embeddings and knowledge graph data.
    """
    try:
        # Import here to avoid circular imports
        from app.tasks.search_tasks import rebuild_all_embeddings_task
        
        # Queue the reindex task
        task = rebuild_all_embeddings_task.delay()
        
        return BaseResponse(
            success=True,
            message=f"Search reindex started. Task ID: {task.id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start search reindex: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=Dict[str, Any])
async def search_health():
    """
    Check search system health.
    
    Returns the status of vector database and LightRAG components.
    """
    try:
        health_status = {
            "vector_db": "healthy",
            "lightrag": "healthy" if semantic_search_service.lightrag_available else "unavailable",
            "knowledge_graph": "healthy"
        }
        
        # Test vector database connection
        try:
            await semantic_search_service.vector_db.get_collection_stats()
        except Exception:
            health_status["vector_db"] = "unhealthy"
        
        # Test knowledge graph
        try:
            if semantic_search_service.knowledge_graph.graph.number_of_nodes() >= 0:
                pass  # Graph is accessible
        except Exception:
            health_status["knowledge_graph"] = "unhealthy"
        
        overall_status = "healthy" if all(
            status in ["healthy", "unavailable"] for status in health_status.values()
        ) else "unhealthy"
        
        return {
            "success": True,
            "status": overall_status,
            "components": health_status
        }
        
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }