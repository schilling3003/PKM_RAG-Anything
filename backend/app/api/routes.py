"""
Main API router that includes all endpoint routers.
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models.schemas import HealthResponse
from app.core.websocket import manager, handle_websocket_message

# Import individual routers (will be created in subsequent tasks)
# from app.api.endpoints import notes, documents, search, graph

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health", response_model=HealthResponse)
async def api_health():
    """API health check."""
    return HealthResponse(
        status="healthy",
        service="api-component"
    )

# Database health check endpoint
@api_router.get("/health/database")
async def database_health():
    """Database health check."""
    try:
        from app.core.database import DatabaseManager
        from app.core.vector_db import vector_db
        
        # Check SQLite database
        db_info = DatabaseManager.get_database_info()
        
        # Check ChromaDB
        vector_info = vector_db.get_collection_info()
        
        return {
            "status": "healthy",
            "databases": {
                "sqlite": {
                    "status": "connected",
                    "tables": len(db_info["tables"]),
                    "engine": db_info["engine"]
                },
                "chromadb": {
                    "status": "connected",
                    "collection": vector_info["name"],
                    "document_count": vector_info["count"]
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# WebSocket endpoint for real-time updates
@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Task status endpoint
@api_router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get background task status."""
    try:
        from app.core.celery_app import celery_app
        from app.core.database import SessionLocal
        from app.models.database import BackgroundTask
        
        # Get task from Celery
        celery_task = celery_app.AsyncResult(task_id)
        
        # Get task from database
        db = SessionLocal()
        try:
            db_task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        finally:
            db.close()
        
        if db_task:
            return {
                "task_id": task_id,
                "status": db_task.status,
                "progress": db_task.progress,
                "current_step": db_task.current_step,
                "result": db_task.result,
                "error": db_task.error,
                "created_at": db_task.created_at.isoformat(),
                "updated_at": db_task.updated_at.isoformat()
            }
        elif celery_task:
            return {
                "task_id": task_id,
                "status": celery_task.status,
                "result": celery_task.result,
                "info": celery_task.info
            }
        else:
            return {
                "task_id": task_id,
                "status": "not_found",
                "error": "Task not found"
            }
            
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e)
        }

# Include individual routers
from app.api.endpoints import notes, documents, knowledge_graph, search, rag

api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(knowledge_graph.router, prefix="/graph", tags=["knowledge-graph"])