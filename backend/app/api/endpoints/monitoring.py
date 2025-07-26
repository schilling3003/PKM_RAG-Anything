"""
Monitoring and health check endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.exceptions import error_monitor, ErrorSeverity
from app.models.schemas import HealthResponse
from app.services.openai_service import get_openai_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    health_status = error_monitor.get_health_status()
    
    return HealthResponse(
        status=health_status["status"],
        service="ai-pkm-backend",
        version="1.0.0",
        details={
            "error_summary": {
                "total_errors": health_status["total_errors"],
                "critical_errors": health_status["critical_errors"],
                "high_severity_errors": health_status["high_severity_errors"]
            },
            "recommendations": health_status["recommendations"]
        }
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with error statistics."""
    health_status = error_monitor.get_health_status()
    error_stats = error_monitor.get_error_stats()
    
    return {
        "health": health_status,
        "error_statistics": error_stats,
        "system_status": {
            "status": health_status["status"],
            "uptime": "N/A",  # Could be implemented with startup time tracking
            "memory_usage": "N/A",  # Could be implemented with psutil
            "disk_usage": "N/A"  # Could be implemented with psutil
        }
    }


@router.get("/errors/stats")
async def get_error_statistics():
    """Get error statistics and metrics."""
    return error_monitor.get_error_stats()


@router.get("/errors/recent")
async def get_recent_errors(limit: int = 50):
    """Get recent error occurrences."""
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100"
        )
    
    stats = error_monitor.get_error_stats()
    recent_errors = stats["recent_errors"]
    
    # Return only the most recent errors up to the limit
    return {
        "errors": recent_errors[-limit:] if len(recent_errors) > limit else recent_errors,
        "total_count": len(error_monitor.error_history),
        "showing": min(limit, len(recent_errors))
    }


@router.post("/errors/clear")
async def clear_error_history():
    """Clear error history (admin function)."""
    error_monitor.error_history.clear()
    error_monitor.error_counts.clear()
    
    return {
        "message": "Error history cleared successfully",
        "timestamp": error_monitor.error_history
    }


@router.get("/errors/categories")
async def get_error_categories():
    """Get error breakdown by category."""
    stats = error_monitor.get_error_stats()
    
    return {
        "category_distribution": stats["category_distribution"],
        "severity_distribution": stats["severity_distribution"],
        "total_errors": stats["total_errors"]
    }


@router.get("/health/openai")
async def openai_health_check():
    """Check OpenAI API health and connectivity."""
    openai_service = get_openai_service()
    
    # Get current health status
    health = openai_service.health_check()
    
    # If not configured, try to configure now
    if not health["configured"]:
        openai_service.configure()
        health = openai_service.health_check()
    
    # If configured but not tested, run connectivity test
    if health["configured"] and not health["last_test"]:
        await openai_service.test_connectivity()
        health = openai_service.health_check()
    
    return health


@router.get("/health/openai/test")
async def test_openai_connectivity():
    """Test OpenAI API connectivity and model access."""
    openai_service = get_openai_service()
    
    # Configure if not already configured
    if not openai_service._api_key:
        configured = openai_service.configure()
        if not configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured"
            )
    
    # Run connectivity test
    test_result = await openai_service.test_connectivity()
    
    if not test_result["connectivity_test"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OpenAI API connectivity test failed: {test_result.get('error', 'Unknown error')}"
        )
    
    return test_result


@router.get("/system/status")
async def get_system_status():
    """Get overall system status."""
    health_status = error_monitor.get_health_status()
    
    # Check OpenAI service status
    openai_service = get_openai_service()
    openai_health = openai_service.health_check()
    
    # Determine overall system status
    status_mapping = {
        "healthy": "operational",
        "warning": "degraded_performance",
        "degraded": "partial_outage",
        "critical": "major_outage"
    }
    
    return {
        "status": status_mapping.get(health_status["status"], "unknown"),
        "health_check": health_status,
        "services": {
            "api": "operational",
            "database": "operational",  # Could be enhanced with actual checks
            "file_storage": "operational",  # Could be enhanced with actual checks
            "task_queue": "operational",  # Could be enhanced with actual checks
            "openai": "operational" if openai_health["available"] else "degraded"
        },
        "openai_status": {
            "configured": openai_health["configured"],
            "available": openai_health["available"],
            "fallback_enabled": openai_health["fallback_enabled"]
        },
        "last_updated": error_monitor.error_history[-1]["timestamp"] if error_monitor.error_history else None
    }