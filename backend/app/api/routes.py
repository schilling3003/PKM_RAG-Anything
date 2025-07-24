"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

# Import individual routers (will be created in subsequent tasks)
# from app.api.endpoints import notes, documents, search, graph

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def api_health():
    """API health check."""
    return {"status": "healthy", "component": "api"}

# Include individual routers (will be uncommented as they're implemented)
# api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(search.router, prefix="/search", tags=["search"])
# api_router.include_router(graph.router, prefix="/graph", tags=["graph"])