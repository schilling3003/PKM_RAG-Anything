"""
Service health monitoring and availability checks.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
import structlog

from app.core.config import settings
from app.core.exceptions import ExternalServiceError, ConfigurationError

logger = structlog.get_logger(__name__)


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealthCheck:
    """Service health check result."""
    service_name: str
    status: ServiceStatus
    response_time: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    last_checked: datetime = None
    
    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.utcnow()


class ServiceHealthMonitor:
    """
    Monitors health of external services and provides availability checks.
    """
    
    def __init__(self):
        self.health_cache = {}
        self.cache_ttl = 30  # seconds
        self.circuit_breakers = {}
        self.retry_configs = {
            "redis": {"max_retries": 3, "backoff_factor": 1.5},
            "celery": {"max_retries": 2, "backoff_factor": 2.0},
            "openai": {"max_retries": 3, "backoff_factor": 2.0},
            "lightrag": {"max_retries": 2, "backoff_factor": 1.0},
            "database": {"max_retries": 3, "backoff_factor": 1.5},
            "storage": {"max_retries": 2, "backoff_factor": 1.0}
        }
    
    async def check_service_health(self, service_name: str, force_check: bool = False) -> ServiceHealthCheck:
        """
        Check health of a specific service with caching.
        
        Args:
            service_name: Name of the service to check
            force_check: Force a fresh check bypassing cache
            
        Returns:
            ServiceHealthCheck result
        """
        # Check cache first unless forced
        if not force_check and service_name in self.health_cache:
            cached_result = self.health_cache[service_name]
            if (datetime.utcnow() - cached_result.last_checked).seconds < self.cache_ttl:
                return cached_result
        
        # Perform health check
        start_time = time.time()
        
        try:
            if service_name == "redis":
                result = await self._check_redis_health()
            elif service_name == "celery":
                result = await self._check_celery_health()
            elif service_name == "openai":
                result = await self._check_openai_health()
            elif service_name == "lightrag":
                result = await self._check_lightrag_health()
            elif service_name == "database":
                result = await self._check_database_health()
            elif service_name == "storage":
                result = await self._check_storage_health()
            elif service_name == "raganything":
                result = await self._check_raganything_health()
            else:
                result = ServiceHealthCheck(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    response_time=0,
                    error=f"Unknown service: {service_name}"
                )
        
        except Exception as e:
            logger.error(f"Health check failed for {service_name}", error=str(e))
            result = ServiceHealthCheck(
                service_name=service_name,
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        # Cache result
        self.health_cache[service_name] = result
        
        # Log health status
        logger.info(
            f"Service health check completed",
            service=service_name,
            status=result.status.value,
            response_time=result.response_time,
            error=result.error
        )
        
        return result
    
    async def _check_redis_health(self) -> ServiceHealthCheck:
        """Check Redis connectivity and performance."""
        start_time = time.time()
        
        try:
            # Create Redis connection
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"
            
            # Set and get test value
            redis_client.set(test_key, test_value, ex=10)
            retrieved_value = redis_client.get(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Redis read/write test failed")
            
            # Clean up test key
            redis_client.delete(test_key)
            
            # Get Redis info
            info = redis_client.info()
            
            response_time = time.time() - start_time
            
            # Determine status based on response time and memory usage
            if response_time > 1.0:
                status = ServiceStatus.DEGRADED
            elif info.get('used_memory_rss', 0) > 1024 * 1024 * 1024:  # 1GB
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.HEALTHY
            
            return ServiceHealthCheck(
                service_name="redis",
                status=status,
                response_time=response_time,
                details={
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "uptime": info.get("uptime_in_seconds")
                }
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="redis",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _check_celery_health(self) -> ServiceHealthCheck:
        """Check Celery worker availability."""
        start_time = time.time()
        
        try:
            from app.core.celery_app import celery_app
            
            # Check active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if not active_workers:
                return ServiceHealthCheck(
                    service_name="celery",
                    status=ServiceStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    error="No active Celery workers found"
                )
            
            # Get worker stats
            stats = inspect.stats()
            
            response_time = time.time() - start_time
            
            # Determine status based on worker count and queue length
            worker_count = len(active_workers)
            if worker_count < 1:
                status = ServiceStatus.UNHEALTHY
            elif response_time > 2.0:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.HEALTHY
            
            return ServiceHealthCheck(
                service_name="celery",
                status=status,
                response_time=response_time,
                details={
                    "active_workers": worker_count,
                    "worker_names": list(active_workers.keys()),
                    "stats": stats
                }
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="celery",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _check_openai_health(self) -> ServiceHealthCheck:
        """Check OpenAI API availability."""
        start_time = time.time()
        
        try:
            if not settings.OPENAI_API_KEY:
                return ServiceHealthCheck(
                    service_name="openai",
                    status=ServiceStatus.DEGRADED,
                    response_time=0,
                    error="OpenAI API key not configured",
                    details={"configured": False}
                )
            
            import openai
            
            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            
            # Test with a minimal request
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            response_time = time.time() - start_time
            
            # Determine status based on response time
            if response_time > 5.0:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.HEALTHY
            
            return ServiceHealthCheck(
                service_name="openai",
                status=status,
                response_time=response_time,
                details={
                    "configured": True,
                    "model": settings.LLM_MODEL,
                    "base_url": settings.OPENAI_BASE_URL or "default"
                }
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="openai",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e),
                details={"configured": bool(settings.OPENAI_API_KEY)}
            )
    
    async def _check_lightrag_health(self) -> ServiceHealthCheck:
        """Check LightRAG availability."""
        start_time = time.time()
        
        try:
            from app.services.lightrag_service import lightrag_service
            
            # Check if LightRAG is initialized
            if not hasattr(lightrag_service, 'lightrag') or not lightrag_service.lightrag:
                return ServiceHealthCheck(
                    service_name="lightrag",
                    status=ServiceStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    error="LightRAG not initialized"
                )
            
            # Test basic functionality
            test_result = await lightrag_service.test_connection()
            
            response_time = time.time() - start_time
            
            if test_result.get("success", False):
                status = ServiceStatus.HEALTHY
            else:
                status = ServiceStatus.DEGRADED
            
            return ServiceHealthCheck(
                service_name="lightrag",
                status=status,
                response_time=response_time,
                details=test_result
            )
            
        except ImportError:
            return ServiceHealthCheck(
                service_name="lightrag",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error="LightRAG not installed"
            )
        except Exception as e:
            return ServiceHealthCheck(
                service_name="lightrag",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _check_database_health(self) -> ServiceHealthCheck:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            try:
                # Test basic query
                from sqlalchemy import text
                result = db.execute(text("SELECT 1")).fetchone()
                if not result:
                    raise Exception("Database query test failed")
                
                response_time = time.time() - start_time
                
                # Determine status based on response time
                if response_time > 1.0:
                    status = ServiceStatus.DEGRADED
                else:
                    status = ServiceStatus.HEALTHY
                
                return ServiceHealthCheck(
                    service_name="database",
                    status=status,
                    response_time=response_time,
                    details={
                        "database_url": settings.DATABASE_URL.split("://")[0] + "://***",
                        "connection_test": "passed"
                    }
                )
                
            finally:
                db.close()
                
        except Exception as e:
            return ServiceHealthCheck(
                service_name="database",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _check_storage_health(self) -> ServiceHealthCheck:
        """Check file storage accessibility."""
        start_time = time.time()
        
        try:
            import os
            import tempfile
            
            # Test write access to upload directory
            test_file = os.path.join(settings.UPLOAD_DIR, f"health_check_{int(time.time())}.tmp")
            
            with open(test_file, 'w') as f:
                f.write("health check test")
            
            # Test read access
            with open(test_file, 'r') as f:
                content = f.read()
                if content != "health check test":
                    raise Exception("Storage read test failed")
            
            # Clean up
            os.remove(test_file)
            
            # Get storage stats
            upload_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(settings.UPLOAD_DIR)
                for filename in filenames
            )
            
            response_time = time.time() - start_time
            
            return ServiceHealthCheck(
                service_name="storage",
                status=ServiceStatus.HEALTHY,
                response_time=response_time,
                details={
                    "upload_dir": settings.UPLOAD_DIR,
                    "upload_dir_size": upload_size,
                    "write_test": "passed",
                    "read_test": "passed"
                }
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="storage",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _check_raganything_health(self) -> ServiceHealthCheck:
        """Check RAG-Anything availability."""
        start_time = time.time()
        
        try:
            from app.services.document_processor import document_processor
            
            # Check if RAG-Anything is initialized
            if not hasattr(document_processor, 'rag_anything') or not document_processor.rag_anything:
                return ServiceHealthCheck(
                    service_name="raganything",
                    status=ServiceStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    error="RAG-Anything not initialized"
                )
            
            response_time = time.time() - start_time
            
            return ServiceHealthCheck(
                service_name="raganything",
                status=ServiceStatus.HEALTHY,
                response_time=response_time,
                details={
                    "initialized": True,
                    "mineru_device": settings.MINERU_DEVICE,
                    "mineru_backend": settings.MINERU_BACKEND
                }
            )
            
        except ImportError:
            return ServiceHealthCheck(
                service_name="raganything",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error="RAG-Anything not installed"
            )
        except Exception as e:
            return ServiceHealthCheck(
                service_name="raganything",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def check_all_services(self) -> Dict[str, ServiceHealthCheck]:
        """Check health of all services."""
        services = ["redis", "celery", "database", "storage", "openai", "lightrag", "raganything"]
        
        results = {}
        for service in services:
            results[service] = await self.check_service_health(service)
        
        return results
    
    def is_service_available(self, service_name: str) -> bool:
        """
        Quick check if service is available (uses cached result).
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service is healthy or degraded, False if unhealthy
        """
        if service_name not in self.health_cache:
            # If not cached, assume unavailable for safety
            return False
        
        cached_result = self.health_cache[service_name]
        
        # Check if cache is still valid
        if (datetime.utcnow() - cached_result.last_checked).seconds > self.cache_ttl * 2:
            return False
        
        return cached_result.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    async def ensure_service_available(self, service_name: str, operation_name: str = None) -> ServiceHealthCheck:
        """
        Ensure service is available before performing an operation.
        
        Args:
            service_name: Name of the service to check
            operation_name: Optional name of the operation being performed
            
        Returns:
            ServiceHealthCheck result
            
        Raises:
            ExternalServiceError: If service is not available
        """
        health_check = await self.check_service_health(service_name)
        
        if health_check.status == ServiceStatus.UNHEALTHY:
            operation_context = f" for {operation_name}" if operation_name else ""
            raise ExternalServiceError(
                message=f"Service {service_name} is unavailable{operation_context}",
                service_name=service_name,
                details={
                    "health_check": health_check.__dict__,
                    "operation": operation_name
                },
                user_message=f"The {service_name} service is currently unavailable. Please try again later."
            )
        
        return health_check
    
    def get_retry_config(self, service_name: str) -> Dict[str, Any]:
        """Get retry configuration for a service."""
        return self.retry_configs.get(service_name, {"max_retries": 2, "backoff_factor": 1.5})
    
    def clear_health_cache(self, service_name: str = None):
        """Clear health check cache."""
        if service_name:
            self.health_cache.pop(service_name, None)
        else:
            self.health_cache.clear()
        
        logger.info(f"Health cache cleared", service=service_name or "all")


# Global instance
service_health_monitor = ServiceHealthMonitor()