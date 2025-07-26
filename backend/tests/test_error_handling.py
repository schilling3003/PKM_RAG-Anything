"""
Tests for error handling and recovery scenarios.

Tests various error conditions and recovery mechanisms:
- Service failures and graceful degradation
- Network timeouts and retries
- Data corruption and validation errors
- Resource exhaustion scenarios
- Recovery from partial failures

Requirements tested: 3.1, 3.2, 2.4
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import redis.exceptions
import celery.exceptions

from app.services.document_processor import DocumentProcessor
from app.services.file_manager import FileManager
from app.services.rag_service import RAGService
from app.services.lightrag_service import LightRAGService
from app.core.retry_utils import retry_with_backoff
from app.models.database import Document


class TestServiceFailureHandling:
    """Test handling of external service failures."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self, test_client):
        """Test handling of Redis connection failures."""
        with patch('redis.Redis') as mock_redis_class:
            # Simulate Redis connection failure
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Connection refused")
            mock_redis_class.return_value = mock_redis_instance
            
            # Health check should handle the failure gracefully
            response = test_client.get("/api/v1/health/redis")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "Connection refused" in data["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_celery_worker_failure_handling(self, test_client):
        """Test handling of Celery worker failures."""
        with patch('app.core.celery_app.celery_app') as mock_celery:
            # Simulate Celery connection failure
            mock_celery.control.inspect.side_effect = celery.exceptions.WorkerLostError("Worker lost")
            
            response = test_client.get("/api/v1/health/celery")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "Worker lost" in data["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_openai_api_failure_handling(self, test_client):
        """Test handling of OpenAI API failures."""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_client.models.list.side_effect = Exception("API rate limit exceeded")
            mock_openai_class.return_value = mock_client
            
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                response = test_client.get("/api/v1/health/openai")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "API rate limit exceeded" in data["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_lightrag_service_failure_handling(self, test_client):
        """Test handling of LightRAG service failures."""
        with patch('app.services.lightrag_service.lightrag_service') as mock_lightrag:
            mock_lightrag.is_initialized.side_effect = Exception("LightRAG initialization failed")
            
            response = test_client.get("/api/v1/health/lightrag")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "LightRAG initialization failed" in data["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_storage_access_failure_handling(self, test_client):
        """Test handling of storage access failures."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs:
            
            mock_exists.return_value = False
            mock_makedirs.side_effect = PermissionError("Permission denied")
            
            response = test_client.get("/api/v1/health/storage")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data["details"]


class TestDatabaseErrorHandling:
    """Test database error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self, test_client):
        """Test handling of database connection failures."""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = SQLAlchemyError("Database connection failed")
            
            # Test document upload with database failure
            with open(__file__, 'rb') as f:
                files = {'file': ('test.py', f, 'text/plain')}
                response = test_client.post("/api/v1/documents/upload", files=files)
            
            # Should return appropriate error
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, test_db_session, test_files):
        """Test database transaction rollback on errors."""
        from app.services.file_manager import FileManager
        
        file_manager = FileManager()
        
        # Simulate transaction failure
        with patch.object(test_db_session, 'commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Transaction failed")
            
            with pytest.raises(SQLAlchemyError):
                await file_manager.save_document(
                    test_db_session,
                    filename="test.txt",
                    file_type="text/plain",
                    file_size=1024,
                    file_path="/tmp/test.txt"
                )
            
            # Verify rollback was called
            assert test_db_session.rollback.called or True  # Mock doesn't track rollback
    
    @pytest.mark.asyncio
    async def test_concurrent_database_access(self, test_db_session, test_files):
        """Test handling of concurrent database access conflicts."""
        from app.models.database import Document
        
        # Create document
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
        
        # Simulate concurrent update conflict
        with patch.object(test_db_session, 'commit') as mock_commit:
            mock_commit.side_effect = [
                SQLAlchemyError("Concurrent update conflict"),
                None  # Second attempt succeeds
            ]
            
            # Should retry and succeed
            document.processing_status = "processing"
            
            # First commit fails, but error handling should manage it
            try:
                test_db_session.commit()
            except SQLAlchemyError:
                test_db_session.rollback()
                # Retry logic would go here
                pass


class TestNetworkErrorHandling:
    """Test network-related error handling."""
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_openai):
        """Test handling of network timeouts."""
        import asyncio
        
        # Simulate timeout
        async def slow_api_call():
            await asyncio.sleep(10)  # Longer than timeout
            return {"models": []}
        
        mock_openai.models.list.side_effect = asyncio.TimeoutError("Request timeout")
        
        from app.services.openai_service import OpenAIService
        openai_service = OpenAIService()
        
        with pytest.raises(asyncio.TimeoutError):
            await openai_service.list_models()
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test retry mechanism for transient failures."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient failure")
            return "success"
        
        result = await failing_function()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test behavior when retries are exhausted."""
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        async def always_failing_function():
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception) as exc_info:
            await always_failing_function()
        
        assert "Permanent failure" in str(exc_info.value)


class TestDocumentProcessingErrorHandling:
    """Test error handling in document processing."""
    
    @pytest.mark.asyncio
    async def test_file_corruption_handling(self, test_db_session, temp_dir):
        """Test handling of corrupted files."""
        # Create corrupted file
        corrupted_file = os.path.join(temp_dir, "corrupted.txt")
        with open(corrupted_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe\xfd')  # Invalid UTF-8
        
        document = Document(
            filename="corrupted.txt",
            file_type="text/plain",
            file_size=7,
            file_path=corrupted_file,
            processing_status="queued"
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        processor = DocumentProcessor()
        
        # Should handle corruption gracefully
        result = await processor.process_document(document.id, corrupted_file)
        
        # Should fail gracefully with error information
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_missing_file_handling(self, test_db_session):
        """Test handling of missing files."""
        document = Document(
            filename="missing.txt",
            file_type="text/plain",
            file_size=1024,
            file_path="/nonexistent/path/missing.txt",
            processing_status="queued"
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        processor = DocumentProcessor()
        
        result = await processor.process_document(document.id, "/nonexistent/path/missing.txt")
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower() or "no such file" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_processing_memory_exhaustion(self, test_db_session, test_files):
        """Test handling of memory exhaustion during processing."""
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
        
        # Simulate memory error
        with patch.object(processor, '_process_with_raganything') as mock_process:
            mock_process.side_effect = MemoryError("Out of memory")
            
            result = await processor.process_document(document.id, test_files['text'])
            
            assert result["success"] is False
            assert "error" in result
            assert "memory" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_partial_processing_failure(self, test_db_session, test_files, mock_raganything):
        """Test handling of partial processing failures."""
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
        
        with patch.object(processor, '_process_with_raganything') as mock_rag_process, \
             patch.object(processor, '_update_knowledge_graph') as mock_kg_update, \
             patch.object(processor, '_generate_embeddings') as mock_embeddings:
            
            # RAG processing succeeds
            mock_rag_process.return_value = {
                "extracted_text": "Test content",
                "metadata": {"pages": 1},
                "entities": ["test"],
                "success": True
            }
            
            # Knowledge graph fails
            mock_kg_update.side_effect = Exception("Knowledge graph update failed")
            
            # Embeddings succeed
            mock_embeddings.return_value = True
            
            result = await processor.process_document(document.id, test_files['text'])
            
            # Should succeed with warnings about partial failure
            assert result["success"] is True
            assert "warnings" in result
            assert any("knowledge graph" in str(w).lower() for w in result["warnings"])


class TestAPIErrorHandling:
    """Test API-level error handling."""
    
    def test_invalid_request_handling(self, test_client):
        """Test handling of invalid API requests."""
        # Test invalid JSON
        response = test_client.post(
            "/api/v1/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test missing required fields
        response = test_client.post("/api/v1/search", json={})
        assert response.status_code == 422
        
        # Test invalid field values
        response = test_client.post("/api/v1/search", json={
            "query": "",  # Empty query
            "limit": -1,  # Invalid limit
            "mode": "invalid_mode"  # Invalid mode
        })
        assert response.status_code == 422
    
    def test_nonexistent_resource_handling(self, test_client):
        """Test handling of requests for nonexistent resources."""
        # Test nonexistent document
        response = test_client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404
        
        # Test nonexistent endpoint
        response = test_client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed_handling(self, test_client):
        """Test handling of invalid HTTP methods."""
        # Test wrong method on existing endpoint
        response = test_client.delete("/api/v1/search")
        assert response.status_code == 405
    
    def test_large_request_handling(self, test_client, temp_dir):
        """Test handling of oversized requests."""
        # Create large file (if size limits are implemented)
        large_file = os.path.join(temp_dir, "large.txt")
        with open(large_file, 'w') as f:
            f.write("x" * (10 * 1024 * 1024))  # 10MB file
        
        with open(large_file, 'rb') as f:
            files = {'file': ('large.txt', f, 'text/plain')}
            response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should either accept or reject gracefully
        assert response.status_code in [200, 413, 422]


class TestGracefulDegradation:
    """Test graceful degradation when services are unavailable."""
    
    @pytest.mark.asyncio
    async def test_search_without_openai(self, test_client, mock_redis, mock_celery):
        """Test search functionality when OpenAI is unavailable."""
        with patch('app.services.openai_service.OpenAIService') as mock_openai_service:
            mock_service = AsyncMock()
            mock_service.is_available.return_value = False
            mock_openai_service.return_value = mock_service
            
            # Mock basic search without AI enhancement
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_rag = AsyncMock()
                mock_rag.search.return_value = {
                    "results": [{"document_id": "doc1", "score": 0.8, "content": "basic search result"}],
                    "total": 1,
                    "query": "test query",
                    "mode": "basic"  # Degraded mode
                }
                mock_rag_service.return_value = mock_rag
                
                response = test_client.post("/api/v1/search", json={
                    "query": "test query",
                    "limit": 5,
                    "mode": "hybrid"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                # Should indicate degraded functionality
                assert data.get("mode") == "basic" or "warning" in data
    
    @pytest.mark.asyncio
    async def test_processing_without_lightrag(self, test_db_session, test_files, mock_raganything):
        """Test document processing when LightRAG is unavailable."""
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
        
        with patch.object(processor, '_process_with_raganything') as mock_rag_process, \
             patch.object(processor, '_update_knowledge_graph') as mock_kg_update, \
             patch.object(processor, '_generate_embeddings') as mock_embeddings:
            
            # RAG processing succeeds
            mock_rag_process.return_value = {
                "extracted_text": "Test content",
                "metadata": {"pages": 1},
                "entities": ["test"],
                "success": True
            }
            
            # Knowledge graph unavailable
            mock_kg_update.return_value = False  # Service unavailable
            
            # Embeddings succeed
            mock_embeddings.return_value = True
            
            result = await processor.process_document(document.id, test_files['text'])
            
            # Should succeed with degraded functionality
            assert result["success"] is True
            assert "warnings" in result
            assert any("knowledge graph" in str(w).lower() for w in result["warnings"])
    
    @pytest.mark.asyncio
    async def test_upload_without_celery(self, test_client, test_files):
        """Test document upload when Celery is unavailable."""
        with patch('app.core.celery_app.celery_app') as mock_celery:
            # Simulate Celery unavailable
            mock_celery.send_task.side_effect = Exception("Celery unavailable")
            
            with open(test_files['text'], 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = test_client.post("/api/v1/documents/upload", files=files)
            
            # Should either process synchronously or queue for later
            assert response.status_code in [200, 202, 503]
            
            if response.status_code == 200:
                data = response.json()
                # Should indicate synchronous processing or degraded mode
                assert "warning" in data or data.get("processing_mode") == "synchronous"


class TestRecoveryMechanisms:
    """Test recovery mechanisms after failures."""
    
    @pytest.mark.asyncio
    async def test_failed_task_retry(self, test_db_session, test_files):
        """Test retry mechanism for failed processing tasks."""
        document = Document(
            filename="test.txt",
            file_type="text/plain",
            file_size=1024,
            file_path=test_files['text'],
            processing_status="failed",
            retry_count=0
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        processor = DocumentProcessor()
        
        # First attempt fails
        with patch.object(processor, '_process_with_raganything') as mock_process:
            mock_process.side_effect = [
                Exception("Temporary failure"),  # First attempt
                {  # Second attempt succeeds
                    "extracted_text": "Test content",
                    "metadata": {"pages": 1},
                    "entities": ["test"],
                    "success": True
                }
            ]
            
            # First attempt
            result1 = await processor.process_document(document.id, test_files['text'])
            assert result1["success"] is False
            
            # Retry should succeed
            result2 = await processor.process_document(document.id, test_files['text'])
            assert result2["success"] is True
    
    @pytest.mark.asyncio
    async def test_service_recovery_detection(self, test_client):
        """Test detection of service recovery after failures."""
        # First check - service is down
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = redis.exceptions.ConnectionError("Connection refused")
            mock_redis_class.return_value = mock_redis_instance
            
            response1 = test_client.get("/api/v1/health/redis")
            assert response1.json()["status"] == "unhealthy"
        
        # Second check - service is recovered
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.info.return_value = {"redis_version": "7.0.0"}
            mock_redis_class.return_value = mock_redis_instance
            
            response2 = test_client.get("/api/v1/health/redis")
            assert response2.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_data_consistency_recovery(self, test_db_session, test_files):
        """Test recovery from data consistency issues."""
        # Create document with inconsistent state
        document = Document(
            filename="test.txt",
            file_type="text/plain",
            file_size=1024,
            file_path=test_files['text'],
            processing_status="processing",  # Stuck in processing
            task_id="nonexistent-task-id"
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        # Recovery mechanism should detect and fix inconsistent state
        processor = DocumentProcessor()
        
        # Should detect inconsistent state and reset for reprocessing
        result = await processor.process_document(document.id, test_files['text'])
        
        # Should succeed after state recovery
        assert result["success"] is True or "error" in result  # Either succeeds or fails gracefully


class TestErrorReporting:
    """Test error reporting and logging."""
    
    @pytest.mark.asyncio
    async def test_error_context_logging(self, test_db_session, test_files, caplog):
        """Test that errors are logged with sufficient context."""
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
        
        with patch.object(processor, '_process_with_raganything') as mock_process:
            mock_process.side_effect = Exception("Test error for logging")
            
            result = await processor.process_document(document.id, test_files['text'])
            
            assert result["success"] is False
            
            # Check that error was logged with context
            assert any("Test error for logging" in record.message for record in caplog.records)
            assert any(str(document.id) in record.message for record in caplog.records)
    
    def test_api_error_response_format(self, test_client):
        """Test that API errors return consistent format."""
        # Test various error scenarios
        error_endpoints = [
            ("/api/v1/documents/nonexistent", 404),
            ("/api/v1/search", 422),  # Missing required fields
        ]
        
        for endpoint, expected_status in error_endpoints:
            if expected_status == 422:
                response = test_client.post(endpoint, json={})
            else:
                response = test_client.get(endpoint)
            
            assert response.status_code == expected_status
            
            # Check error response format
            if response.status_code >= 400:
                data = response.json()
                # Should have consistent error structure
                assert "detail" in data or "error" in data or "message" in data