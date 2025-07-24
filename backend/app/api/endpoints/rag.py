"""
RAG (Retrieval-Augmented Generation) API endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import logging

from app.services.rag_service import rag_service
from app.models.schemas import RAGQuery, RAGResponse, BaseResponse
from app.core.exceptions import SearchError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=Dict[str, Any])
async def rag_query(
    query: str = Query(..., min_length=1, max_length=1000, description="Question to answer"),
    mode: str = Query("hybrid", regex="^(naive|local|global|hybrid|mix)$", description="RAG mode"),
    max_tokens: int = Query(2000, ge=100, le=8000, description="Maximum tokens for response"),
    include_sources: bool = Query(True, description="Include source citations"),
    use_cache: bool = Query(True, description="Use cached results if available"),
    conversation_history: Optional[List[Dict[str, str]]] = Body(None, description="Previous conversation turns")
):
    """
    Process a RAG query with comprehensive context retrieval and answer generation.
    
    Supports multiple RAG modes:
    - naive: Simple retrieval without graph context
    - local: Local knowledge graph traversal
    - global: Global knowledge graph analysis
    - hybrid: Combines local and global approaches
    - mix: Advanced mixed retrieval strategy
    """
    try:
        logger.info(f"RAG query request: '{query[:50]}...' (mode: {mode})")
        
        response = await rag_service.process_rag_query(
            query=query,
            mode=mode,
            max_tokens=max_tokens,
            include_sources=include_sources,
            conversation_history=conversation_history,
            use_cache=use_cache
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


@router.post("/conversation", response_model=Dict[str, Any])
async def rag_conversation(
    messages: List[Dict[str, str]] = Body(..., description="Conversation messages"),
    mode: str = Query("hybrid", regex="^(naive|local|global|hybrid|mix)$", description="RAG mode"),
    max_tokens: int = Query(2000, ge=100, le=8000, description="Maximum tokens for response"),
    include_sources: bool = Query(True, description="Include source citations")
):
    """
    Process a conversational RAG query with full conversation history.
    
    Expected message format:
    [
        {"role": "user", "content": "What is machine learning?"},
        {"role": "assistant", "content": "Machine learning is..."},
        {"role": "user", "content": "How does it work?"}
    ]
    """
    try:
        if not messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        # Extract the latest user message as the query
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user messages found")
        
        latest_query = user_messages[-1]["content"]
        
        # Use all messages except the latest as conversation history
        conversation_history = messages[:-1] if len(messages) > 1 else None
        
        logger.info(f"Conversational RAG query: '{latest_query[:50]}...'")
        
        response = await rag_service.process_rag_query(
            query=latest_query,
            mode=mode,
            max_tokens=max_tokens,
            include_sources=include_sources,
            conversation_history=conversation_history,
            use_cache=True
        )
        
        return {
            "success": True,
            "response": response.dict(),
            "conversation_context": {
                "total_messages": len(messages),
                "history_messages": len(conversation_history) if conversation_history else 0
            }
        }
        
    except HTTPException:
        raise
    except SearchError as e:
        logger.error(f"Conversational RAG query failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in conversational RAG query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history", response_model=Dict[str, Any])
async def get_rag_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of history entries"),
    mode_filter: Optional[str] = Query(None, regex="^(naive|local|global|hybrid|mix)$", description="Filter by RAG mode")
):
    """
    Get RAG query history.
    
    Returns recent RAG queries with their answers, processing times, and metadata.
    """
    try:
        history = await rag_service.get_query_history(
            limit=limit,
            mode_filter=mode_filter
        )
        
        return {
            "success": True,
            "history": history,
            "total": len(history),
            "filters": {
                "mode": mode_filter,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get RAG history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=Dict[str, Any])
async def get_rag_stats():
    """
    Get RAG service statistics.
    
    Returns information about query counts, performance metrics,
    and system status.
    """
    try:
        stats = await rag_service.get_rag_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cache/clear", response_model=BaseResponse)
async def clear_rag_cache():
    """
    Clear the RAG query cache.
    
    This will force all subsequent queries to be processed fresh
    without using cached results.
    """
    try:
        await rag_service.clear_cache()
        
        return BaseResponse(
            success=True,
            message="RAG query cache cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to clear RAG cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/modes", response_model=Dict[str, Any])
async def get_rag_modes():
    """
    Get information about available RAG modes.
    
    Returns descriptions and use cases for each RAG mode.
    """
    try:
        modes = {
            "naive": {
                "name": "Naive",
                "description": "Simple retrieval without knowledge graph context",
                "use_case": "Quick answers from document content",
                "performance": "Fast",
                "accuracy": "Basic"
            },
            "local": {
                "name": "Local",
                "description": "Local knowledge graph traversal around query entities",
                "use_case": "Detailed answers about specific topics",
                "performance": "Medium",
                "accuracy": "Good"
            },
            "global": {
                "name": "Global",
                "description": "Global knowledge graph analysis and summarization",
                "use_case": "Comprehensive overviews and connections",
                "performance": "Slow",
                "accuracy": "High"
            },
            "hybrid": {
                "name": "Hybrid",
                "description": "Combines local and global knowledge graph approaches",
                "use_case": "Balanced accuracy and performance",
                "performance": "Medium",
                "accuracy": "High"
            },
            "mix": {
                "name": "Mix",
                "description": "Advanced mixed retrieval strategy with adaptive selection",
                "use_case": "Complex queries requiring multiple perspectives",
                "performance": "Variable",
                "accuracy": "Highest"
            }
        }
        
        return {
            "success": True,
            "modes": modes,
            "default_mode": "hybrid",
            "recommended_modes": {
                "quick_facts": "naive",
                "detailed_analysis": "local",
                "comprehensive_overview": "global",
                "general_purpose": "hybrid",
                "complex_research": "mix"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get RAG modes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=Dict[str, Any])
async def rag_health():
    """
    Check RAG service health.
    
    Returns the status of RAG components including LightRAG,
    knowledge graph, and caching system.
    """
    try:
        health_status = {
            "rag_service": "healthy",
            "lightrag": "healthy" if rag_service.lightrag_available else "unavailable",
            "knowledge_graph": "healthy",
            "cache": "healthy"
        }
        
        # Test knowledge graph connection
        try:
            if rag_service.knowledge_graph.graph.number_of_nodes() >= 0:
                pass  # Graph is accessible
        except Exception:
            health_status["knowledge_graph"] = "unhealthy"
        
        # Test cache
        try:
            cache_size = len(rag_service.cache.cache)
            health_status["cache_size"] = cache_size
        except Exception:
            health_status["cache"] = "unhealthy"
        
        overall_status = "healthy" if all(
            status in ["healthy", "unavailable"] for status in health_status.values() if isinstance(status, str)
        ) else "unhealthy"
        
        return {
            "success": True,
            "status": overall_status,
            "components": health_status,
            "timestamp": "2025-07-24T21:00:00Z"  # Current timestamp would be added here
        }
        
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }