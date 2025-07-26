"""
Tests for service dependency failure scenarios.

Tests various combinations of service failures and their impact:
- Single service failures
- Multiple service failures
- Cascading failures
- Service startup order dependencies
- Recovery from dependency failures

Requirements tested: 2.2, 2.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import redis.exceptions
import celery.exceptions

from app.api.endpoints.health import comprehensive_health
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from app.models.database import Document


class TestSingleServiceFailures:
    """Test impact of individual service failures."""
    
    @pytest.mark.asyncio
    async def test_redis_failure_impact(self, test_client, mock_celery, mock_lightrag, 
                                      mock_openai, temp_dir):
        """Test system behavior when only Redis fails."""
        with patch('redis.Redis') as mock_redis_class:
            # Redis fails
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            # Other services are healthy
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                    result = await comprehensive_health()
            
            # System should be degraded but not completely unhealthy
            assert result.overall_status in ["degraded", "unhealthy"]
            assert result.services["redis"].status == "unhealthy"
            assert result.services["celery"].status == "unhealthy"  # Depends on Redis
            
            # Other services should still be healthy
            assert result.services["storage"].status == "healthy"
            assert result.services["openai"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_celery_failure_impact(self, test_client, mock_redis, mock_lightrag, 
                                       mock_openai, temp_dir):
        """Test system behavior when only Celery fails."""
        with patch('app.core.celery_app.celery_app') as mock_celery:
            # Celery fails
            mock_celery.control.inspect.side_effect = celery.exceptions.WorkerLostError("No workers")
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                    result = await comprehensive_health()
            
            # System should be degraded
            assert result.overall_status in ["degraded", "unhealthy"]
            assert result.services["celery"].status == "unhealthy"
            
            # Other services should be healthy
            assert result.services["redis"].status == "healthy"
            assert result.services["storage"].status == "healthy"
            assert result.services["openai"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_openai_failure_impact(self, test_client, mock_redis, mock_celery, 
                                       mock_lightrag, temp_dir):
        """Test system behavior when only OpenAI fails."""
        with patch('openai.OpenAI') as mock_openai_class:
            # OpenAI fails
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("OpenAI API down")
            mock_openai_class.return_value = mock_client
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                    result = await comprehensive_health()
            
            # System should be degraded but functional
            assert result.overall_status in ["degraded", "unhealthy"]
            assert result.services["openai"].status == "unhealthy"
            
            # Core services should be healthy
            assert result.services["redis"].status == "healthy"
            assert result.services["celery"].status == "healthy"
            assert result.services["storage"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_lightrag_failure_impact(self, test_client, mock_redis, mock_celery, 
                                         mock_openai, temp_dir):
        """Test system behavior when only LightRAG fails."""
        with patch('app.services.lightrag_service.lightrag_service') as mock_lightrag:
            # LightRAG fails
            mock_lightrag.is_initialized.side_effect = Exception("LightRAG service down")
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                    result = await comprehensive_health()
            
            # System should be degraded
            assert result.overall_status in ["degraded", "unhealthy"]
            assert result.services["lightrag"].status == "unhealthy"
            
            # Other services should be healthy
            assert result.services["redis"].status == "healthy"
            assert result.services["celery"].status == "healthy"
            assert result.services["openai"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_storage_failure_impact(self, test_client, mock_redis, mock_celery, 
                                        mock_lightrag, mock_openai):
        """Test system behavior when storage fails."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:
            
            # Storage fails
            mock_exists.return_value = False
            mock_makedirs.side_effect = PermissionError("Storage access denied")
            
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                result = await comprehensive_health()
            
            # System should be unhealthy (storage is critical)
            assert result.overall_status == "unhealthy"
            assert result.services["storage"].status == "unhealthy"
            
            # Other services should be healthy
            assert result.services["redis"].status == "healthy"
            assert result.services["celery"].status == "healthy"
            assert result.services["openai"].status == "healthy"


class TestMultipleServiceFailures:
    """Test impact of multiple simultaneous service failures."""
    
    @pytest.mark.asyncio
    async def test_redis_and_celery_failure(self, test_client, temp_dir):
        """Test system behavior when both Redis and Celery fail."""
        with patch('redis.Redis') as mock_redis_class, \
             patch('app.core.celery_app.celery_app') as mock_celery:
            
            # Both Redis and Celery fail
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            mock_celery.control.inspect.side_effect = celery.exceptions.WorkerLostError("No workers")
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                result = await comprehensive_health()
            
            # System should be severely degraded
            assert result.overall_status == "unhealthy"
            assert result.services["redis"].status == "unhealthy"
            assert result.services["celery"].status == "unhealthy"
            
            # Background processing should be completely unavailable
            assert "background processing" in result.summary.lower() or "task queue" in result.summary.lower()
    
    @pytest.mark.asyncio
    async def test_ai_services_failure(self, test_client, mock_redis, mock_celery, temp_dir):
        """Test system behavior when AI services (OpenAI + LightRAG) fail."""
        with patch('openai.OpenAI') as mock_openai_class, \
             patch('app.services.lightrag_service.lightrag_service') as mock_lightrag:
            
            # AI services fail
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("OpenAI API down")
            mock_openai_class.return_value = mock_client
            
            mock_lightrag.is_initialized.side_effect = Exception("LightRAG down")
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                    result = await comprehensive_health()
            
            # System should be degraded but basic functionality available
            assert result.overall_status in ["degraded", "unhealthy"]
            assert result.services["openai"].status == "unhealthy"
            assert result.services["lightrag"].status == "unhealthy"
            
            # Core infrastructure should be healthy
            assert result.services["redis"].status == "healthy"
            assert result.services["celery"].status == "healthy"
            assert result.services["storage"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_critical_services_failure(self, test_client):
        """Test system behavior when critical services fail."""
        with patch('redis.Redis') as mock_redis_class, \
             patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:
            
            # Critical services fail
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            mock_exists.return_value = False
            mock_makedirs.side_effect = PermissionError("Storage access denied")
            
            result = await comprehensive_health()
            
            # System should be completely unhealthy
            assert result.overall_status == "unhealthy"
            assert result.services["redis"].status == "unhealthy"
            assert result.services["storage"].status == "unhealthy"
            assert result.services["celery"].status == "unhealthy"  # Depends on Redis
    
    @pytest.mark.asyncio
    async def test_all_services_failure(self, test_client):
        """Test system behavior when all services fail."""
        with patch('redis.Redis') as mock_redis_class, \
             patch('app.core.celery_app.celery_app') as mock_celery, \
             patch('openai.OpenAI') as mock_openai_class, \
             patch('app.services.lightrag_service.lightrag_service') as mock_lightrag, \
             patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:
            
            # All services fail
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            mock_celery.control.inspect.side_effect = celery.exceptions.WorkerLostError("No workers")
            
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("OpenAI API down")
            mock_openai_class.return_value = mock_client
            
            mock_lightrag.is_initialized.side_effect = Exception("LightRAG down")
            
            mock_exists.return_value = False
            mock_makedirs.side_effect = PermissionError("Storage access denied")
            
            result = await comprehensive_health()
            
            # System should be completely unhealthy
            assert result.overall_status == "unhealthy"
            assert all(service.status == "unhealthy" for service in result.services.values())
            assert "critical" in result.summary.lower()


class TestCascadingFailures:
    """Test cascading failures between dependent services."""
    
    @pytest.mark.asyncio
    async def test_redis_failure_cascades_to_celery(self, test_client, temp_dir):
        """Test that Redis failure causes Celery to fail."""
        with patch('redis.Redis') as mock_redis_class:
            # Redis fails
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            # Celery should also fail due to Redis dependency
            with patch('app.core.celery_app.celery_app') as mock_celery:
                mock_celery.control.inspect.side_effect = Exception("Cannot connect to Redis")
                
                with patch('app.core.config.settings') as mock_settings:
                    mock_settings.UPLOAD_DIR = temp_dir
                    mock_settings.RAG_STORAGE_DIR = temp_dir
                    mock_settings.CHROMA_DB_PATH = temp_dir
                    
                    result = await comprehensive_health()
                
                # Both should be unhealthy
                assert result.services["redis"].status == "unhealthy"
                assert result.services["celery"].status == "unhealthy"
                assert result.overall_status == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_storage_failure_cascades_to_processing(self, test_db_session, test_files):
        """Test that storage failure prevents document processing."""
        document = Document(
            filename="test.txt",
            file_type="text/plain",
            file_size=1024,
            file_path=test_files['text'],
            processing_status="queued"
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        processor = DocumentProcessor()
        
        # Simulate storage failure
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # File doesn't exist
            
            result = await processor.process_document(document.id, "/nonexistent/file.txt")
            
            # Processing should fail due to storage issue
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_openai_failure_degrades_search(self, test_client, mock_redis, mock_celery):
        """Test that OpenAI failure degrades search functionality."""
        with patch('openai.OpenAI') as mock_openai_class:
            # OpenAI fails
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("OpenAI API down")
            mock_openai_class.return_value = mock_client
            
            # Search should still work but in degraded mode
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_service = AsyncMock()
                mock_service.search.return_value = {
                    "results": [{"document_id": "doc1", "score": 0.5, "content": "basic search"}],
                    "total": 1,
                    "query": "test query",
                    "mode": "basic",  # Degraded mode
                    "warnings": ["OpenAI unavailable, using basic search"]
                }
                mock_rag_service.return_value = mock_service
                
                response = test_client.post("/api/v1/search", json={
                    "query": "test query",
                    "limit": 5,
                    "mode": "hybrid"
                })
                
                assert response.status_code == 200
                data = response.json()
                
                # Should work but indicate degraded functionality
                assert "results" in data
                assert data.get("mode") == "basic" or "warnings" in data


class TestServiceStartupDependencies:
    """Test service startup order and dependencies."""
    
    @pytest.mark.asyncio
    async def test_service_initialization_order(self, mock_all_services):
        """Test that services initialize in correct order."""
        initialization_order = []
        
        # Mock service initialization to track order
        original_redis_ping = mock_all_services["redis"].ping
        original_celery_inspect = mock_all_services["celery"].control.inspect
        
        def track_redis_init():
            initialization_order.append("redis")
            return original_redis_ping()
        
        def track_celery_init():
            initialization_order.append("celery")
            return original_celery_inspect()
        
        mock_all_services["redis"].ping = track_redis_init
        mock_all_services["celery"].control.inspect = track_celery_init
        
        # Run health check which should initialize services
        result = await comprehensive_health()
        
        # Redis should be checked before Celery (dependency order)
        if "redis" in initialization_order and "celery" in initialization_order:
            redis_index = initialization_order.index("redis")
            celery_index = initialization_order.index("celery")
            assert redis_index < celery_index
    
    @pytest.mark.asyncio
    async def test_service_dependency_validation(self, test_client):
        """Test that service dependencies are properly validated."""
        # Test Celery without Redis
        with patch('redis.Redis') as mock_redis_class, \
             patch('app.core.celery_app.celery_app') as mock_celery:
            
            # Redis is down
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            # Celery should detect Redis dependency failure
            mock_celery.control.inspect.side_effect = Exception("Redis connection required")
            
            response = test_client.get("/api/v1/health/celery")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "redis" in data["details"]["error"].lower() or "connection" in data["details"]["error"].lower()


class TestServiceRecoveryScenarios:
    """Test recovery from service dependency failures."""
    
    @pytest.mark.asyncio
    async def test_service_recovery_detection(self, test_client):
        """Test detection of service recovery."""
        # First check - Redis is down
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            response1 = test_client.get("/api/v1/health/redis")
            assert response1.json()["status"] == "unhealthy"
        
        # Second check - Redis recovers
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.info.return_value = {"redis_version": "7.0.0"}
            mock_redis_class.return_value = mock_redis_instance
            
            response2 = test_client.get("/api/v1/health/redis")
            assert response2.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_dependent_service_recovery(self, test_client, temp_dir):
        """Test that dependent services recover when dependencies recover."""
        # First check - Redis down, Celery should also be down
        with patch('redis.Redis') as mock_redis_class, \
             patch('app.core.celery_app.celery_app') as mock_celery:
            
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            mock_celery.control.inspect.side_effect = Exception("Cannot connect to Redis")
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                result1 = await comprehensive_health()
            
            assert result1.services["redis"].status == "unhealthy"
            assert result1.services["celery"].status == "unhealthy"
        
        # Second check - Redis recovers, Celery should also recover
        with patch('redis.Redis') as mock_redis_class, \
             patch('app.core.celery_app.celery_app') as mock_celery:
            
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.info.return_value = {"redis_version": "7.0.0"}
            mock_redis_class.return_value = mock_redis_instance
            
            mock_inspect = Mock()
            mock_inspect.active.return_value = {"worker1": []}
            mock_inspect.registered.return_value = {"worker1": ["app.tasks.process_document"]}
            mock_celery.control.inspect.return_value = mock_inspect
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                result2 = await comprehensive_health()
            
            assert result2.services["redis"].status == "healthy"
            assert result2.services["celery"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_partial_recovery_handling(self, test_client, temp_dir):
        """Test handling of partial service recovery."""
        # Some services recover, others don't
        with patch('redis.Redis') as mock_redis_class, \
             patch('openai.OpenAI') as mock_openai_class:
            
            # Redis recovers
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.info.return_value = {"redis_version": "7.0.0"}
            mock_redis_class.return_value = mock_redis_instance
            
            # OpenAI still down
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("OpenAI still down")
            mock_openai_class.return_value = mock_client
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                    result = await comprehensive_health()
            
            # Should show mixed health status
            assert result.services["redis"].status == "healthy"
            assert result.services["openai"].status == "unhealthy"
            assert result.overall_status in ["degraded", "unhealthy"]


class TestServiceDependencyMapping:
    """Test understanding of service dependency relationships."""
    
    @pytest.mark.asyncio
    async def test_dependency_graph_validation(self, test_client, temp_dir):
        """Test that service dependency graph is correctly understood."""
        # Test known dependencies:
        # - Celery depends on Redis
        # - Document processing depends on storage
        # - AI features depend on OpenAI/LightRAG
        
        with patch('redis.Redis') as mock_redis_class:
            # Redis fails
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
            mock_redis_class.return_value = mock_redis_instance
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.UPLOAD_DIR = temp_dir
                mock_settings.RAG_STORAGE_DIR = temp_dir
                mock_settings.CHROMA_DB_PATH = temp_dir
                
                result = await comprehensive_health()
            
            # Verify dependency relationships
            assert result.services["redis"].status == "unhealthy"
            
            # Celery should also be unhealthy due to Redis dependency
            assert result.services["celery"].status == "unhealthy"
            
            # Independent services should still be healthy
            assert result.services["storage"].status == "healthy"
    
    @pytest.mark.asyncio
    async def test_circular_dependency_handling(self, test_client):
        """Test that circular dependencies are handled gracefully."""
        # This test ensures the health check system doesn't get stuck
        # in circular dependency loops
        
        start_time = asyncio.get_event_loop().time()
        
        result = await comprehensive_health()
        
        end_time = asyncio.get_event_loop().time()
        
        # Health check should complete quickly without infinite loops
        assert end_time - start_time < 10.0  # Should complete within 10 seconds
        assert hasattr(result, 'overall_status')
        assert len(result.services) == 6  # All expected services


class TestServiceFailureImpactAnalysis:
    """Test analysis of service failure impact on system functionality."""
    
    @pytest.mark.asyncio
    async def test_upload_functionality_with_service_failures(self, test_client, test_files):
        """Test upload functionality under various service failure scenarios."""
        # Test upload with different service failure combinations
        failure_scenarios = [
            ("redis_only", {"redis": True}),
            ("celery_only", {"celery": True}),
            ("openai_only", {"openai": True}),
            ("storage_only", {"storage": True}),
        ]
        
        for scenario_name, failures in failure_scenarios:
            with patch('redis.Redis') as mock_redis_class, \
                 patch('app.core.celery_app.celery_app') as mock_celery, \
                 patch('openai.OpenAI') as mock_openai_class, \
                 patch('os.path.exists') as mock_exists:
                
                # Configure failures based on scenario
                if failures.get("redis"):
                    mock_redis_instance = Mock()
                    mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Redis down")
                    mock_redis_class.return_value = mock_redis_instance
                else:
                    mock_redis_instance = Mock()
                    mock_redis_instance.ping.return_value = True
                    mock_redis_class.return_value = mock_redis_instance
                
                if failures.get("celery"):
                    mock_celery.send_task.side_effect = Exception("Celery down")
                else:
                    mock_celery.send_task.return_value = Mock(id="task-123")
                
                if failures.get("openai"):
                    mock_client = Mock()
                    mock_client.models.list.side_effect = Exception("OpenAI down")
                    mock_openai_class.return_value = mock_client
                else:
                    mock_client = Mock()
                    mock_client.models.list.return_value.data = [Mock(id="gpt-4o-mini")]
                    mock_openai_class.return_value = mock_client
                
                if failures.get("storage"):
                    mock_exists.return_value = False
                else:
                    mock_exists.return_value = True
                
                # Test upload
                with open(test_files['text'], 'rb') as f:
                    files = {'file': ('test.txt', f, 'text/plain')}
                    response = test_client.post("/api/v1/documents/upload", files=files)
                
                # Analyze impact based on failure type
                if failures.get("storage"):
                    # Storage failure should prevent upload
                    assert response.status_code in [400, 500, 503]
                elif failures.get("redis") or failures.get("celery"):
                    # Task queue failure might allow upload but prevent background processing
                    assert response.status_code in [200, 202, 503]
                else:
                    # Other failures shouldn't prevent basic upload
                    assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_search_functionality_with_service_failures(self, test_client):
        """Test search functionality under various service failure scenarios."""
        search_query = {
            "query": "test search",
            "limit": 5,
            "mode": "hybrid"
        }
        
        # Test search with OpenAI failure
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("OpenAI down")
            mock_openai_class.return_value = mock_client
            
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_service = AsyncMock()
                mock_service.search.return_value = {
                    "results": [],
                    "total": 0,
                    "query": search_query["query"],
                    "mode": "basic",  # Degraded mode
                    "warnings": ["AI features unavailable"]
                }
                mock_rag_service.return_value = mock_service
                
                response = test_client.post("/api/v1/search", json=search_query)
                
                # Should work in degraded mode
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert data.get("mode") == "basic" or "warnings" in data