"""
Unit tests for health check endpoints.

Tests all health check endpoints with various service states:
- Healthy services
- Degraded services  
- Unhealthy services
- Service failures

Requirements tested: 8.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from app.api.endpoints.health import (
    check_redis_health,
    check_celery_health,
    check_lightrag_health,
    check_raganything_mineru_health,
    check_openai_health,
    check_storage_health,
    comprehensive_health
)


class TestRedisHealthCheck:
    """Test Redis health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_redis_healthy(self, mock_redis):
        """Test Redis health check when Redis is healthy."""
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "redis_version": "7.0.0",
            "used_memory": 1024000,
            "connected_clients": 5
        }
        
        result = await check_redis_health()
        
        assert result.status == "healthy"
        assert result.service == "redis"
        assert result.response_time_ms is not None
        assert result.details["version"] == "7.0.0"
        assert result.details["memory_usage"] == 1024000
        assert result.details["connected_clients"] == 5
    
    @pytest.mark.asyncio
    async def test_redis_connection_failed(self, simulate_redis_failure):
        """Test Redis health check when connection fails."""
        result = await check_redis_health()
        
        assert result.status == "unhealthy"
        assert result.service == "redis"
        assert "error" in result.details
        assert "Redis connection failed" in result.details["error"]
    
    @pytest.mark.asyncio
    async def test_redis_degraded_performance(self, mock_redis):
        """Test Redis health check with degraded performance."""
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "redis_version": "7.0.0",
            "used_memory": 500000000,  # High memory usage
            "connected_clients": 100   # High client count
        }
        
        # Simulate slow response
        import time
        original_ping = mock_redis.ping
        def slow_ping():
            time.sleep(0.1)  # 100ms delay
            return original_ping()
        mock_redis.ping = slow_ping
        
        result = await check_redis_health()
        
        # Should still be healthy but with performance warnings
        assert result.status in ["healthy", "degraded"]
        assert result.response_time_ms > 50  # Should show increased response time


class TestCeleryHealthCheck:
    """Test Celery health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_celery_healthy(self, mock_celery):
        """Test Celery health check when workers are healthy."""
        mock_inspect = Mock()
        mock_inspect.active.return_value = {"worker1": [], "worker2": []}
        mock_inspect.registered.return_value = {
            "worker1": ["app.tasks.process_document"],
            "worker2": ["app.tasks.process_document"]
        }
        mock_inspect.stats.return_value = {
            "worker1": {"pool": {"max-concurrency": 4}},
            "worker2": {"pool": {"max-concurrency": 4}}
        }
        mock_celery.control.inspect.return_value = mock_inspect
        
        result = await check_celery_health()
        
        assert result.status == "healthy"
        assert result.service == "celery"
        assert result.details["active_workers"] == 2
        assert result.details["total_concurrency"] == 8
        assert "app.tasks.process_document" in result.details["registered_tasks"]
    
    @pytest.mark.asyncio
    async def test_celery_no_workers(self, mock_celery):
        """Test Celery health check when no workers are available."""
        mock_inspect = Mock()
        mock_inspect.active.return_value = {}
        mock_inspect.registered.return_value = {}
        mock_celery.control.inspect.return_value = mock_inspect
        
        result = await check_celery_health()
        
        assert result.status == "unhealthy"
        assert result.details["active_workers"] == 0
        assert "No active workers" in result.details["error"]
    
    @pytest.mark.asyncio
    async def test_celery_connection_failed(self, simulate_celery_failure):
        """Test Celery health check when connection fails."""
        result = await check_celery_health()
        
        assert result.status == "unhealthy"
        assert "error" in result.details
        assert "Celery connection failed" in result.details["error"]


class TestLightRAGHealthCheck:
    """Test LightRAG health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_lightrag_healthy(self, mock_lightrag):
        """Test LightRAG health check when service is healthy."""
        mock_lightrag.is_initialized.return_value = True
        mock_lightrag.get_stats.return_value = {
            "entities_count": 100,
            "relationships_count": 50,
            "storage_size": 1024000
        }
        
        with patch('app.services.lightrag_service.lightrag_service', mock_lightrag):
            result = await check_lightrag_health()
        
        assert result.status == "healthy"
        assert result.service == "lightrag"
        assert result.details["initialized"] is True
        assert result.details["entities_count"] == 100
        assert result.details["relationships_count"] == 50
    
    @pytest.mark.asyncio
    async def test_lightrag_not_initialized(self):
        """Test LightRAG health check when not initialized."""
        mock_lightrag = AsyncMock()
        mock_lightrag.is_initialized.return_value = False
        
        with patch('app.services.lightrag_service.lightrag_service', mock_lightrag):
            result = await check_lightrag_health()
        
        assert result.status == "degraded"
        assert result.details["initialized"] is False
        assert "not initialized" in result.details["warning"]
    
    @pytest.mark.asyncio
    async def test_lightrag_error(self):
        """Test LightRAG health check when service has errors."""
        mock_lightrag = AsyncMock()
        mock_lightrag.is_initialized.side_effect = Exception("LightRAG service error")
        
        with patch('app.services.lightrag_service.lightrag_service', mock_lightrag):
            result = await check_lightrag_health()
        
        assert result.status == "unhealthy"
        assert "error" in result.details
        assert "LightRAG service error" in result.details["error"]


class TestRAGAnythingHealthCheck:
    """Test RAG-Anything/MinerU health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_raganything_healthy(self):
        """Test RAG-Anything health check when service is healthy."""
        with patch('importlib.util.find_spec') as mock_find_spec, \
             patch('torch.cuda.is_available') as mock_cuda:
            
            # Mock successful imports
            mock_find_spec.return_value = Mock()
            mock_cuda.return_value = True
            
            result = await check_raganything_mineru_health()
        
        assert result.status == "healthy"
        assert result.service == "raganything_mineru"
        assert result.details["raganything_available"] is True
        assert result.details["mineru_available"] is True
        assert result.details["cuda_available"] is True
    
    @pytest.mark.asyncio
    async def test_raganything_no_cuda(self):
        """Test RAG-Anything health check without CUDA."""
        with patch('importlib.util.find_spec') as mock_find_spec, \
             patch('torch.cuda.is_available') as mock_cuda:
            
            mock_find_spec.return_value = Mock()
            mock_cuda.return_value = False
            
            result = await check_raganything_mineru_health()
        
        assert result.status == "degraded"
        assert result.details["cuda_available"] is False
        assert "CUDA not available" in result.details["warning"]
    
    @pytest.mark.asyncio
    async def test_raganything_missing_dependencies(self):
        """Test RAG-Anything health check with missing dependencies."""
        with patch('importlib.util.find_spec') as mock_find_spec:
            mock_find_spec.return_value = None
            
            result = await check_raganything_mineru_health()
        
        assert result.status == "unhealthy"
        assert result.details["raganything_available"] is False
        assert "RAG-Anything not installed" in result.details["error"]


class TestOpenAIHealthCheck:
    """Test OpenAI health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_openai_healthy(self, mock_openai):
        """Test OpenAI health check when API is healthy."""
        mock_openai.models.list.return_value.data = [
            Mock(id="gpt-4o-mini"),
            Mock(id="text-embedding-3-large")
        ]
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            result = await check_openai_health()
        
        assert result.status == "healthy"
        assert result.service == "openai"
        assert result.details["api_key_configured"] is True
        assert result.details["api_accessible"] is True
        assert "gpt-4o-mini" in result.details["available_models"]
    
    @pytest.mark.asyncio
    async def test_openai_no_api_key(self):
        """Test OpenAI health check without API key."""
        with patch.dict('os.environ', {}, clear=True):
            result = await check_openai_health()
        
        assert result.status == "degraded"
        assert result.details["api_key_configured"] is False
        assert "API key not configured" in result.details["warning"]
    
    @pytest.mark.asyncio
    async def test_openai_api_error(self, simulate_openai_failure):
        """Test OpenAI health check when API is unavailable."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            result = await check_openai_health()
        
        assert result.status == "unhealthy"
        assert result.details["api_accessible"] is False
        assert "OpenAI API unavailable" in result.details["error"]


class TestStorageHealthCheck:
    """Test storage health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_storage_healthy(self, temp_dir):
        """Test storage health check when all directories are accessible."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = temp_dir
            mock_settings.RAG_STORAGE_DIR = temp_dir
            mock_settings.CHROMA_DB_PATH = temp_dir
            
            result = await check_storage_health()
        
        assert result.status == "healthy"
        assert result.service == "storage"
        assert result.details["upload_dir"]["accessible"] is True
        assert result.details["rag_storage_dir"]["accessible"] is True
        assert result.details["chroma_db_path"]["accessible"] is True
    
    @pytest.mark.asyncio
    async def test_storage_permission_denied(self, simulate_storage_failure):
        """Test storage health check with permission errors."""
        result = await check_storage_health()
        
        assert result.status == "unhealthy"
        assert "error" in result.details
        assert any("permission" in str(detail).lower() or "access" in str(detail).lower() 
                  for detail in result.details.values() if isinstance(detail, dict))


class TestComprehensiveHealthCheck:
    """Test comprehensive health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_all_services_healthy(self, mock_all_services, temp_dir):
        """Test comprehensive health check when all services are healthy."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = temp_dir
            mock_settings.RAG_STORAGE_DIR = temp_dir
            mock_settings.CHROMA_DB_PATH = temp_dir
            
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                result = await comprehensive_health()
        
        assert result.overall_status == "healthy"
        assert len(result.services) == 6  # All 6 services
        assert all(service.status == "healthy" for service in result.services.values())
        assert "All services are healthy" in result.summary
    
    @pytest.mark.asyncio
    async def test_mixed_service_health(self, mock_redis, simulate_celery_failure, temp_dir):
        """Test comprehensive health check with mixed service states."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = temp_dir
            mock_settings.RAG_STORAGE_DIR = temp_dir
            mock_settings.CHROMA_DB_PATH = temp_dir
            
            result = await comprehensive_health()
        
        assert result.overall_status in ["degraded", "unhealthy"]
        assert len(result.services) == 6
        
        # Should have mix of healthy and unhealthy services
        statuses = [service.status for service in result.services.values()]
        assert "healthy" in statuses
        assert "unhealthy" in statuses
    
    @pytest.mark.asyncio
    async def test_all_services_unhealthy(self, simulate_redis_failure, simulate_celery_failure, 
                                        simulate_storage_failure, simulate_openai_failure):
        """Test comprehensive health check when all services are unhealthy."""
        result = await comprehensive_health()
        
        assert result.overall_status == "unhealthy"
        assert all(service.status == "unhealthy" for service in result.services.values())
        assert "critical issues" in result.summary.lower()


class TestHealthEndpointIntegration:
    """Integration tests for health endpoints via HTTP."""
    
    def test_redis_health_endpoint(self, test_client, mock_redis):
        """Test Redis health endpoint via HTTP."""
        response = test_client.get("/api/v1/health/redis")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "redis"
        assert "response_time_ms" in data
    
    def test_celery_health_endpoint(self, test_client, mock_celery):
        """Test Celery health endpoint via HTTP."""
        response = test_client.get("/api/v1/health/celery")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "celery"
        assert "active_workers" in data["details"]
    
    def test_comprehensive_health_endpoint(self, test_client, mock_all_services, temp_dir):
        """Test comprehensive health endpoint via HTTP."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = temp_dir
            mock_settings.RAG_STORAGE_DIR = temp_dir
            mock_settings.CHROMA_DB_PATH = temp_dir
            
            response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "services" in data
        assert "summary" in data
        assert len(data["services"]) == 6
    
    def test_health_endpoint_error_handling(self, test_client):
        """Test health endpoints handle errors gracefully."""
        # Test with all services failing
        response = test_client.get("/api/v1/health")
        
        # Should still return 200 but with unhealthy status
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ["degraded", "unhealthy"]


class TestHealthCheckPerformance:
    """Performance tests for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_response_time(self, mock_all_services, performance_monitor):
        """Test that health checks complete within acceptable time."""
        performance_monitor.start()
        
        result = await comprehensive_health()
        
        performance_monitor.stop()
        
        # Health checks should complete within 5 seconds
        assert performance_monitor.duration < 5.0
        assert result.overall_status in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, mock_all_services):
        """Test multiple concurrent health checks."""
        import asyncio
        
        # Run 10 concurrent health checks
        tasks = [comprehensive_health() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 10
        assert all(hasattr(result, 'overall_status') for result in results)
    
    def test_health_endpoint_caching(self, test_client, mock_all_services):
        """Test that health endpoints can handle rapid requests."""
        # Make 20 rapid requests
        responses = []
        for _ in range(20):
            response = test_client.get("/api/v1/health")
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all("overall_status" in r.json() for r in responses)