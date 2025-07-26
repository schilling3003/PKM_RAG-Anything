"""
Comprehensive health check endpoints for all system services.
"""

import os
import redis
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.openai_service import get_openai_service
from app.services.lightrag_service import get_lightrag_service

router = APIRouter()


class ServiceHealthResponse(BaseModel):
    """Individual service health response."""
    service: str
    status: str  # healthy, degraded, unhealthy
    details: Dict[str, Any] = {}
    timestamp: datetime
    response_time_ms: Optional[float] = None


class ComprehensiveHealthResponse(BaseModel):
    """Comprehensive health check response."""
    overall_status: str
    services: Dict[str, ServiceHealthResponse]
    timestamp: datetime
    summary: Dict[str, int]


async def check_redis_health() -> ServiceHealthResponse:
    """Check Redis connectivity and status."""
    start_time = datetime.utcnow()
    
    try:
        # Parse Redis URL
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        # Test basic connectivity
        ping_result = redis_client.ping()
        
        # Get Redis info
        info = redis_client.info()
        
        # Test set/get operations
        test_key = "health_check_test"
        redis_client.set(test_key, "test_value", ex=60)  # Expire in 60 seconds
        test_value = redis_client.get(test_key)
        redis_client.delete(test_key)
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ServiceHealthResponse(
            service="redis",
            status="healthy",
            details={
                "ping": ping_result,
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "test_operations": "passed"
            },
            timestamp=datetime.utcnow(),
            response_time_ms=response_time
        )
        
    except redis.ConnectionError as e:
        return ServiceHealthResponse(
            service="redis",
            status="unhealthy",
            details={
                "error": "Connection failed",
                "message": str(e),
                "redis_url": settings.REDIS_URL.split('@')[-1] if '@' in settings.REDIS_URL else settings.REDIS_URL
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ServiceHealthResponse(
            service="redis",
            status="unhealthy",
            details={
                "error": "Unexpected error",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )


async def check_celery_health() -> ServiceHealthResponse:
    """Check Celery worker status."""
    start_time = datetime.utcnow()
    
    try:
        from app.core.celery_app import celery_app
        
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()
        
        if not active_workers:
            return ServiceHealthResponse(
                service="celery",
                status="unhealthy",
                details={
                    "error": "No active workers found",
                    "active_workers": 0,
                    "suggestion": "Start Celery worker with: celery -A app.core.celery_app worker --loglevel=info"
                },
                timestamp=datetime.utcnow()
            )
        
        # Test task submission (simple ping task)
        try:
            from app.tasks.maintenance import ping_task
            result = ping_task.delay()
            task_result = result.get(timeout=5)  # Wait up to 5 seconds
            task_test_passed = task_result == "pong"
        except Exception as task_error:
            task_test_passed = False
            task_error_msg = str(task_error)
        else:
            task_error_msg = None
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        worker_count = len(active_workers)
        total_tasks = sum(len(tasks) for tasks in registered_tasks.values()) if registered_tasks else 0
        
        return ServiceHealthResponse(
            service="celery",
            status="healthy" if task_test_passed else "degraded",
            details={
                "active_workers": worker_count,
                "worker_names": list(active_workers.keys()),
                "total_registered_tasks": total_tasks,
                "task_test": "passed" if task_test_passed else "failed",
                "task_test_error": task_error_msg,
                "stats": stats
            },
            timestamp=datetime.utcnow(),
            response_time_ms=response_time
        )
        
    except ImportError as e:
        return ServiceHealthResponse(
            service="celery",
            status="unhealthy",
            details={
                "error": "Celery not properly configured",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ServiceHealthResponse(
            service="celery",
            status="unhealthy",
            details={
                "error": "Unexpected error",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )


async def check_lightrag_health() -> ServiceHealthResponse:
    """Check LightRAG functionality."""
    start_time = datetime.utcnow()
    
    try:
        lightrag_service = await get_lightrag_service()
        
        # Test LightRAG initialization
        if not lightrag_service.is_initialized():
            # Try to initialize
            success = await lightrag_service.initialize()
            if not success:
                return ServiceHealthResponse(
                    service="lightrag",
                    status="unhealthy",
                    details={
                        "error": "Failed to initialize LightRAG",
                        "working_dir": settings.RAG_STORAGE_DIR,
                        "suggestion": "Check if LightRAG is properly installed and configured"
                    },
                    timestamp=datetime.utcnow()
                )
        
        # Test basic functionality
        health_check = lightrag_service.health_check()
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine status based on health check results
        if health_check["initialized"] and health_check["working_dir_exists"]:
            status = "healthy"
        elif health_check["working_dir_exists"]:
            status = "degraded"
        else:
            status = "unhealthy"
        
        # Add status to details
        health_check["status"] = status
        
        return ServiceHealthResponse(
            service="lightrag",
            status=status,
            details=health_check,
            timestamp=datetime.utcnow(),
            response_time_ms=response_time
        )
        
    except ImportError as e:
        return ServiceHealthResponse(
            service="lightrag",
            status="unhealthy",
            details={
                "error": "LightRAG not installed",
                "message": str(e),
                "suggestion": "Install LightRAG with: pip install lightrag"
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ServiceHealthResponse(
            service="lightrag",
            status="unhealthy",
            details={
                "error": "Unexpected error",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )


async def check_raganything_mineru_health() -> ServiceHealthResponse:
    """Check RAG-Anything and MinerU availability."""
    start_time = datetime.utcnow()
    
    try:
        # Test RAG-Anything import
        try:
            import raganything
            raganything_version = getattr(raganything, '__version__', 'unknown')
        except ImportError as e:
            return ServiceHealthResponse(
                service="raganything_mineru",
                status="unhealthy",
                details={
                    "error": "RAG-Anything not installed",
                    "message": str(e),
                    "suggestion": "Install RAG-Anything with: pip install raganything"
                },
                timestamp=datetime.utcnow()
            )
        
        # Test MinerU integration
        try:
            from raganything.parser import MineruParser
            mineru_available = True
            mineru_error = None
        except ImportError as e:
            mineru_available = False
            mineru_error = str(e)
        
        # Check CUDA availability for GPU acceleration
        cuda_available = False
        cuda_version = None
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_version = torch.version.cuda
        except ImportError:
            pass
        
        # Check MinerU configuration file
        config_file = "backend/magic-pdf.json"
        config_exists = os.path.exists(config_file)
        
        # Test basic MinerU functionality if available
        mineru_test_passed = False
        mineru_test_error = None
        
        if mineru_available:
            try:
                # Try to create a MinerU parser instance
                parser = MineruParser()
                mineru_test_passed = True
            except Exception as e:
                mineru_test_error = str(e)
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine overall status
        if not mineru_available:
            status = "unhealthy"
        elif not mineru_test_passed:
            status = "degraded"
        else:
            status = "healthy"
        
        return ServiceHealthResponse(
            service="raganything_mineru",
            status=status,
            details={
                "raganything_version": raganything_version,
                "mineru_available": mineru_available,
                "mineru_error": mineru_error,
                "mineru_test_passed": mineru_test_passed,
                "mineru_test_error": mineru_test_error,
                "cuda_available": cuda_available,
                "cuda_version": cuda_version,
                "device_setting": settings.MINERU_DEVICE,
                "config_file_exists": config_exists,
                "config_file_path": config_file
            },
            timestamp=datetime.utcnow(),
            response_time_ms=response_time
        )
        
    except Exception as e:
        return ServiceHealthResponse(
            service="raganything_mineru",
            status="unhealthy",
            details={
                "error": "Unexpected error",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )


async def check_openai_health() -> ServiceHealthResponse:
    """Check OpenAI API validation."""
    start_time = datetime.utcnow()
    
    try:
        openai_service = get_openai_service()
        
        # Get health check from service
        health_check = openai_service.health_check()
        
        # If configured, test connectivity
        if health_check["configured"]:
            connectivity_result = await openai_service.test_connectivity()
            health_check.update(connectivity_result)
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine status
        if not health_check["configured"]:
            status = "degraded"  # Not configured but system can work with fallbacks
        elif health_check.get("connectivity_test", False):
            status = "healthy"
        else:
            status = "unhealthy"
        
        return ServiceHealthResponse(
            service="openai",
            status=status,
            details=health_check,
            timestamp=datetime.utcnow(),
            response_time_ms=response_time
        )
        
    except Exception as e:
        return ServiceHealthResponse(
            service="openai",
            status="unhealthy",
            details={
                "error": "Unexpected error",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )


async def check_storage_health() -> ServiceHealthResponse:
    """Check storage accessibility."""
    start_time = datetime.utcnow()
    
    try:
        storage_checks = {}
        overall_healthy = True
        
        # Check all required directories
        directories = {
            "upload_dir": settings.UPLOAD_DIR,
            "processed_dir": settings.PROCESSED_DIR,
            "rag_storage_dir": settings.RAG_STORAGE_DIR,
            "chroma_db_path": settings.CHROMA_DB_PATH
        }
        
        for dir_name, dir_path in directories.items():
            try:
                # Check if directory exists
                exists = os.path.exists(dir_path)
                
                # Check if directory is writable
                writable = os.access(dir_path, os.W_OK) if exists else False
                
                # Try to create directory if it doesn't exist
                if not exists:
                    os.makedirs(dir_path, exist_ok=True)
                    exists = os.path.exists(dir_path)
                    writable = os.access(dir_path, os.W_OK)
                
                # Test write operation
                test_file = os.path.join(dir_path, ".health_check_test")
                write_test_passed = False
                try:
                    with open(test_file, 'w') as f:
                        f.write("health_check")
                    with open(test_file, 'r') as f:
                        content = f.read()
                    os.remove(test_file)
                    write_test_passed = content == "health_check"
                except Exception:
                    write_test_passed = False
                
                # Get directory size info
                try:
                    total_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(dir_path)
                        for filename in filenames
                    )
                    file_count = sum(
                        len(filenames)
                        for dirpath, dirnames, filenames in os.walk(dir_path)
                    )
                except Exception:
                    total_size = 0
                    file_count = 0
                
                storage_checks[dir_name] = {
                    "path": dir_path,
                    "exists": exists,
                    "writable": writable,
                    "write_test_passed": write_test_passed,
                    "total_size_bytes": total_size,
                    "file_count": file_count
                }
                
                if not (exists and writable and write_test_passed):
                    overall_healthy = False
                    
            except Exception as e:
                storage_checks[dir_name] = {
                    "path": dir_path,
                    "error": str(e)
                }
                overall_healthy = False
        
        # Check database file
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        
        try:
            db_exists = os.path.exists(db_path)
            db_dir_writable = os.access(db_dir, os.W_OK)
            
            storage_checks["database"] = {
                "path": db_path,
                "exists": db_exists,
                "directory_writable": db_dir_writable,
                "size_bytes": os.path.getsize(db_path) if db_exists else 0
            }
            
            if not db_dir_writable:
                overall_healthy = False
                
        except Exception as e:
            storage_checks["database"] = {
                "path": db_path,
                "error": str(e)
            }
            overall_healthy = False
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ServiceHealthResponse(
            service="storage",
            status="healthy" if overall_healthy else "unhealthy",
            details=storage_checks,
            timestamp=datetime.utcnow(),
            response_time_ms=response_time
        )
        
    except Exception as e:
        return ServiceHealthResponse(
            service="storage",
            status="unhealthy",
            details={
                "error": "Unexpected error",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )


@router.get("/health/redis", response_model=ServiceHealthResponse)
async def redis_health():
    """Redis connectivity health check."""
    return await check_redis_health()


@router.get("/health/celery", response_model=ServiceHealthResponse)
async def celery_health():
    """Celery worker status health check."""
    return await check_celery_health()


@router.get("/health/lightrag", response_model=ServiceHealthResponse)
async def lightrag_health():
    """LightRAG functionality health check."""
    return await check_lightrag_health()


@router.get("/health/raganything", response_model=ServiceHealthResponse)
async def raganything_health():
    """RAG-Anything and MinerU availability health check."""
    return await check_raganything_mineru_health()


@router.get("/health/openai", response_model=ServiceHealthResponse)
async def openai_health():
    """OpenAI API validation health check."""
    return await check_openai_health()


@router.get("/health/storage", response_model=ServiceHealthResponse)
async def storage_health():
    """Storage accessibility health check."""
    return await check_storage_health()


@router.get("/health/comprehensive", response_model=ComprehensiveHealthResponse)
async def comprehensive_health():
    """Comprehensive health check for all services with enhanced error monitoring."""
    start_time = datetime.utcnow()
    
    # Run all health checks concurrently
    health_checks = await asyncio.gather(
        check_redis_health(),
        check_celery_health(),
        check_lightrag_health(),
        check_raganything_mineru_health(),
        check_openai_health(),
        check_storage_health(),
        return_exceptions=True
    )
    
    services = {}
    status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}
    
    service_names = ["redis", "celery", "lightrag", "raganything_mineru", "openai", "storage"]
    
    for i, health_check in enumerate(health_checks):
        service_name = service_names[i]
        
        if isinstance(health_check, Exception):
            # Handle exceptions from health checks
            services[service_name] = ServiceHealthResponse(
                service=service_name,
                status="unhealthy",
                details={"error": "Health check failed", "message": str(health_check)},
                timestamp=datetime.utcnow()
            )
            status_counts["unhealthy"] += 1
        else:
            services[service_name] = health_check
            status_counts[health_check.status] += 1
    
    # Add error monitoring status
    try:
        from app.core.error_monitoring import error_monitoring_service
        error_stats = error_monitoring_service.get_error_statistics()
        
        services["error_monitoring"] = ServiceHealthResponse(
            service="error_monitoring",
            status="healthy",
            details={
                "active_alerts": error_stats.get("active_alerts", 0),
                "total_errors": error_stats.get("total_errors", 0),
                "system_health": error_stats.get("system_health", {}),
                "alert_breakdown": error_stats.get("alert_breakdown", {}),
                "monitoring_enabled": True
            },
            timestamp=datetime.utcnow()
        )
        
        # Adjust overall status based on error monitoring
        if error_stats.get("alert_breakdown", {}).get("critical", 0) > 0:
            overall_status = "unhealthy"
        elif error_stats.get("active_alerts", 0) > 5 and status_counts["unhealthy"] == 0:
            overall_status = "degraded"
            
    except Exception as e:
        services["error_monitoring"] = ServiceHealthResponse(
            service="error_monitoring",
            status="degraded",
            details={
                "error": "Error monitoring service unavailable",
                "message": str(e),
                "monitoring_enabled": False
            },
            timestamp=datetime.utcnow()
        )
    
    # Determine overall status
    if status_counts["unhealthy"] > 0:
        overall_status = "unhealthy"
    elif status_counts["degraded"] > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return ComprehensiveHealthResponse(
        overall_status=overall_status,
        services=services,
        timestamp=datetime.utcnow(),
        summary=status_counts
    )


@router.get("/health/errors")
async def error_monitoring_status():
    """Get error monitoring and alerting status."""
    try:
        from app.core.error_monitoring import error_monitoring_service
        from app.core.exceptions import error_monitor
        
        # Get comprehensive error statistics
        error_stats = error_monitoring_service.get_error_statistics()
        
        # Get active alerts
        active_alerts = error_monitoring_service.get_active_alerts()
        
        # Get recent error patterns
        recent_errors = error_monitor.error_history[-10:] if error_monitor.error_history else []
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error_monitoring": {
                "enabled": True,
                "statistics": error_stats,
                "active_alerts": len(active_alerts),
                "alert_details": [alert.to_dict() for alert in active_alerts[-5:]],  # Last 5 alerts
                "recent_errors": recent_errors,
                "health_recommendations": error_stats.get("system_health", {}).get("recommendations", [])
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "error_monitoring": {
                "enabled": False,
                "message": "Error monitoring service is not available"
            }
        }