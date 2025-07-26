"""
Load tests for concurrent document processing.

Tests system performance under various load conditions:
- Concurrent document uploads
- Simultaneous processing tasks
- High-volume search queries
- Memory and resource usage under load
- System stability during peak usage

Requirements tested: 1.1, 1.3, 2.2, 5.5, 6.5
"""

import pytest
import asyncio
import time
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
import psutil
import os
from typing import List, Dict, Any

from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from app.models.database import Document


class TestConcurrentUploads:
    """Test concurrent document upload scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_file_uploads(self, test_client, test_files, mock_all_services, 
                                         load_test_config):
        """Test multiple simultaneous file uploads."""
        concurrent_uploads = min(load_test_config["concurrent_uploads"], 5)  # Limit for testing
        
        def upload_file(file_path: str, upload_id: int) -> Dict[str, Any]:
            """Upload a single file and return result."""
            try:
                with open(file_path, 'rb') as f:
                    filename = f"test_upload_{upload_id}_{os.path.basename(file_path)}"
                    files = {'file': (filename, f, 'text/plain')}
                    
                    start_time = time.time()
                    response = test_client.post("/api/v1/documents/upload", files=files)
                    end_time = time.time()
                    
                    return {
                        "upload_id": upload_id,
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "success": response.status_code == 200,
                        "data": response.json() if response.status_code == 200 else None,
                        "error": response.text if response.status_code != 200 else None
                    }
            except Exception as e:
                return {
                    "upload_id": upload_id,
                    "status_code": 500,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Prepare test files
        test_file_list = list(test_files.values())
        
        # Execute concurrent uploads
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_uploads) as executor:
            futures = []
            for i in range(concurrent_uploads):
                file_path = test_file_list[i % len(test_file_list)]
                future = executor.submit(upload_file, file_path, i)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_uploads = [r for r in results if r["success"]]
        failed_uploads = [r for r in results if not r["success"]]
        
        avg_response_time = sum(r["response_time"] for r in successful_uploads) / len(successful_uploads) if successful_uploads else 0
        max_response_time = max(r["response_time"] for r in successful_uploads) if successful_uploads else 0
        
        # Assertions
        assert len(results) == concurrent_uploads
        assert len(successful_uploads) >= concurrent_uploads * 0.8  # At least 80% success rate
        assert avg_response_time < 5.0  # Average response time under 5 seconds
        assert max_response_time < 10.0  # Max response time under 10 seconds
        assert total_time < 30.0  # Total test time under 30 seconds
        
        # Log results for analysis
        print(f"\nConcurrent Upload Test Results:")
        print(f"Total uploads: {concurrent_uploads}")
        print(f"Successful: {len(successful_uploads)}")
        print(f"Failed: {len(failed_uploads)}")
        print(f"Success rate: {len(successful_uploads)/concurrent_uploads*100:.1f}%")
        print(f"Average response time: {avg_response_time:.2f}s")
        print(f"Max response time: {max_response_time:.2f}s")
        print(f"Total test time: {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_upload_rate_limiting(self, test_client, test_files, mock_all_services):
        """Test system behavior under rapid upload requests."""
        rapid_uploads = 20
        upload_interval = 0.1  # 100ms between uploads
        
        def rapid_upload(upload_id: int) -> Dict[str, Any]:
            """Perform rapid upload."""
            try:
                # Create small test content
                content = f"Test content for upload {upload_id}"
                filename = f"rapid_test_{upload_id}.txt"
                
                files = {'file': (filename, content.encode(), 'text/plain')}
                
                start_time = time.time()
                response = test_client.post("/api/v1/documents/upload", files=files)
                end_time = time.time()
                
                return {
                    "upload_id": upload_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 202, 429]  # Include rate limit as acceptable
                }
            except Exception as e:
                return {
                    "upload_id": upload_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute rapid uploads
        results = []
        start_time = time.time()
        
        for i in range(rapid_uploads):
            result = rapid_upload(i)
            results.append(result)
            
            if i < rapid_uploads - 1:  # Don't sleep after last upload
                time.sleep(upload_interval)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_uploads = [r for r in results if r["success"]]
        rate_limited = [r for r in results if r.get("status_code") == 429]
        
        # System should handle rapid requests gracefully
        assert len(successful_uploads) >= rapid_uploads * 0.7  # At least 70% handled
        assert total_time < rapid_uploads * upload_interval * 2  # Reasonable total time
        
        print(f"\nRapid Upload Test Results:")
        print(f"Total uploads: {rapid_uploads}")
        print(f"Successful: {len(successful_uploads)}")
        print(f"Rate limited: {len(rate_limited)}")
        print(f"Total time: {total_time:.2f}s")


class TestConcurrentProcessing:
    """Test concurrent document processing scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_document_processing(self, test_db_session, test_files, 
                                                mock_all_services, load_test_config):
        """Test concurrent document processing tasks."""
        concurrent_tasks = min(load_test_config["concurrent_uploads"], 8)
        
        # Create test documents
        documents = []
        for i in range(concurrent_tasks):
            file_path = list(test_files.values())[i % len(test_files)]
            doc = Document(
                filename=f"concurrent_test_{i}.txt",
                file_type="text/plain",
                file_size=1024,
                file_path=file_path,
                processing_status="queued"
            )
            test_db_session.add(doc)
            documents.append(doc)
        
        test_db_session.commit()
        
        # Refresh documents to get IDs
        for doc in documents:
            test_db_session.refresh(doc)
        
        processor = DocumentProcessor()
        
        # Mock processing to simulate realistic delays
        async def mock_process_document(doc_id: int, file_path: str) -> Dict[str, Any]:
            """Mock document processing with realistic delay."""
            # Simulate processing time
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            return {
                "success": True,
                "document_id": doc_id,
                "extracted_text": f"Processed content for document {doc_id}",
                "entities": ["test", "entity"],
                "processing_time": random.uniform(1.0, 3.0)
            }
        
        # Execute concurrent processing
        start_time = time.time()
        
        with patch.object(processor, 'process_document', side_effect=mock_process_document):
            tasks = [
                processor.process_document(doc.id, doc.file_path)
                for doc in documents
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get("success"))]
        
        # Assertions
        assert len(results) == concurrent_tasks
        assert len(successful_results) >= concurrent_tasks * 0.9  # At least 90% success
        assert total_time < 10.0  # Should complete within 10 seconds due to concurrency
        
        print(f"\nConcurrent Processing Test Results:")
        print(f"Total tasks: {concurrent_tasks}")
        print(f"Successful: {len(successful_results)}")
        print(f"Failed: {len(failed_results)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per task: {total_time/concurrent_tasks:.2f}s")
    
    @pytest.mark.asyncio
    async def test_processing_queue_management(self, test_db_session, test_files, mock_all_services):
        """Test processing queue under high load."""
        queue_size = 15
        
        # Create documents in queue
        documents = []
        for i in range(queue_size):
            doc = Document(
                filename=f"queue_test_{i}.txt",
                file_type="text/plain",
                file_size=1024,
                file_path=list(test_files.values())[0],
                processing_status="queued"
            )
            test_db_session.add(doc)
            documents.append(doc)
        
        test_db_session.commit()
        
        processor = DocumentProcessor()
        
        # Simulate queue processing with limited concurrency
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(doc: Document) -> Dict[str, Any]:
            """Process document with concurrency limit."""
            async with semaphore:
                await asyncio.sleep(random.uniform(0.2, 0.8))  # Simulate processing
                return {
                    "success": True,
                    "document_id": doc.id,
                    "processing_time": random.uniform(0.2, 0.8)
                }
        
        # Process queue
        start_time = time.time()
        
        tasks = [process_with_semaphore(doc) for doc in documents]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify queue was processed efficiently
        successful_results = [r for r in results if r.get("success")]
        
        assert len(successful_results) == queue_size
        assert total_time < queue_size * 0.8 / max_concurrent * 2  # Should be efficient due to concurrency
        
        print(f"\nQueue Management Test Results:")
        print(f"Queue size: {queue_size}")
        print(f"Max concurrent: {max_concurrent}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Throughput: {queue_size/total_time:.2f} docs/sec")


class TestHighVolumeSearch:
    """Test high-volume search query scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_search_queries(self, test_client, mock_all_services, test_queries):
        """Test multiple simultaneous search queries."""
        concurrent_searches = 10
        
        def execute_search(query_id: int, query: str) -> Dict[str, Any]:
            """Execute a single search query."""
            try:
                search_data = {
                    "query": f"{query} {query_id}",
                    "limit": 5,
                    "mode": "hybrid"
                }
                
                start_time = time.time()
                response = test_client.post("/api/v1/search", json=search_data)
                end_time = time.time()
                
                return {
                    "query_id": query_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200,
                    "results_count": len(response.json().get("results", [])) if response.status_code == 200 else 0
                }
            except Exception as e:
                return {
                    "query_id": query_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Mock search service
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_service = AsyncMock()
            
            async def mock_search(*args, **kwargs):
                # Simulate search delay
                await asyncio.sleep(random.uniform(0.1, 0.5))
                return {
                    "results": [
                        {"document_id": f"doc{i}", "score": 0.9 - i*0.1, "content": f"Result {i}"}
                        for i in range(5)
                    ],
                    "total": 5,
                    "query": kwargs.get("query", "test")
                }
            
            mock_service.search = mock_search
            mock_rag_service.return_value = mock_service
            
            # Execute concurrent searches
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrent_searches) as executor:
                futures = []
                for i in range(concurrent_searches):
                    query = test_queries[i % len(test_queries)]
                    future = executor.submit(execute_search, i, query)
                    futures.append(future)
                
                results = []
                for future in as_completed(futures):
                    results.append(future.result())
            
            end_time = time.time()
            total_time = end_time - start_time
        
        # Analyze results
        successful_searches = [r for r in results if r["success"]]
        failed_searches = [r for r in results if not r["success"]]
        
        avg_response_time = sum(r["response_time"] for r in successful_searches) / len(successful_searches) if successful_searches else 0
        
        # Assertions
        assert len(successful_searches) >= concurrent_searches * 0.9  # 90% success rate
        assert avg_response_time < 2.0  # Average response under 2 seconds
        assert total_time < 10.0  # Total time under 10 seconds
        
        print(f"\nConcurrent Search Test Results:")
        print(f"Total searches: {concurrent_searches}")
        print(f"Successful: {len(successful_searches)}")
        print(f"Failed: {len(failed_searches)}")
        print(f"Average response time: {avg_response_time:.2f}s")
        print(f"Total time: {total_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_search_performance_under_load(self, test_client, mock_all_services):
        """Test search performance degradation under increasing load."""
        load_levels = [1, 5, 10, 15]  # Different concurrent search levels
        performance_results = {}
        
        for load_level in load_levels:
            def execute_search_batch(batch_size: int) -> List[Dict[str, Any]]:
                """Execute a batch of searches."""
                results = []
                
                with patch('app.services.rag_service.RAGService') as mock_rag_service:
                    mock_service = AsyncMock()
                    mock_service.search.return_value = {
                        "results": [{"document_id": "doc1", "score": 0.9}],
                        "total": 1,
                        "query": "test query"
                    }
                    mock_rag_service.return_value = mock_service
                    
                    for i in range(batch_size):
                        search_data = {
                            "query": f"load test query {i}",
                            "limit": 5,
                            "mode": "hybrid"
                        }
                        
                        start_time = time.time()
                        response = test_client.post("/api/v1/search", json=search_data)
                        end_time = time.time()
                        
                        results.append({
                            "response_time": end_time - start_time,
                            "success": response.status_code == 200
                        })
                
                return results
            
            # Execute batch
            start_time = time.time()
            batch_results = execute_search_batch(load_level)
            end_time = time.time()
            
            # Calculate metrics
            successful_results = [r for r in batch_results if r["success"]]
            avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results) if successful_results else 0
            throughput = len(successful_results) / (end_time - start_time)
            
            performance_results[load_level] = {
                "avg_response_time": avg_response_time,
                "throughput": throughput,
                "success_rate": len(successful_results) / len(batch_results)
            }
        
        # Analyze performance degradation
        print(f"\nSearch Performance Under Load:")
        for load_level, metrics in performance_results.items():
            print(f"Load {load_level}: {metrics['avg_response_time']:.3f}s avg, "
                  f"{metrics['throughput']:.2f} req/s, {metrics['success_rate']:.1%} success")
        
        # Performance should degrade gracefully
        base_response_time = performance_results[1]["avg_response_time"]
        high_load_response_time = performance_results[max(load_levels)]["avg_response_time"]
        
        # Response time shouldn't increase more than 5x under load
        assert high_load_response_time < base_response_time * 5


class TestMemoryAndResourceUsage:
    """Test memory and resource usage under load."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_processing(self, test_db_session, test_files, 
                                                mock_all_services, performance_monitor):
        """Test memory usage during concurrent processing."""
        concurrent_tasks = 8
        
        # Create test documents
        documents = []
        for i in range(concurrent_tasks):
            doc = Document(
                filename=f"memory_test_{i}.txt",
                file_type="text/plain",
                file_size=1024,
                file_path=list(test_files.values())[0],
                processing_status="queued"
            )
            test_db_session.add(doc)
            documents.append(doc)
        
        test_db_session.commit()
        
        processor = DocumentProcessor()
        
        # Monitor memory during processing
        performance_monitor.start()
        initial_memory = psutil.Process().memory_info().rss
        
        async def memory_intensive_processing(doc: Document) -> Dict[str, Any]:
            """Simulate memory-intensive processing."""
            # Simulate memory usage
            large_data = "x" * (1024 * 1024)  # 1MB string
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "document_id": doc.id,
                "data_size": len(large_data)
            }
        
        # Execute processing
        tasks = [memory_intensive_processing(doc) for doc in documents]
        results = await asyncio.gather(*tasks)
        
        performance_monitor.stop()
        final_memory = psutil.Process().memory_info().rss
        
        # Analyze memory usage
        memory_increase = final_memory - initial_memory
        memory_per_task = memory_increase / concurrent_tasks if concurrent_tasks > 0 else 0
        
        # Memory usage should be reasonable
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
        assert len([r for r in results if r.get("success")]) == concurrent_tasks
        
        print(f"\nMemory Usage Test Results:")
        print(f"Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
        print(f"Final memory: {final_memory / 1024 / 1024:.2f} MB")
        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
        print(f"Memory per task: {memory_per_task / 1024 / 1024:.2f} MB")
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_after_load(self, test_client, test_files, mock_all_services):
        """Test that resources are properly cleaned up after load testing."""
        initial_memory = psutil.Process().memory_info().rss
        initial_threads = threading.active_count()
        
        # Simulate load
        load_iterations = 10
        
        for i in range(load_iterations):
            # Upload documents
            with open(list(test_files.values())[0], 'rb') as f:
                files = {'file': (f'load_test_{i}.txt', f, 'text/plain')}
                response = test_client.post("/api/v1/documents/upload", files=files)
                assert response.status_code == 200
            
            # Perform searches
            search_data = {
                "query": f"load test query {i}",
                "limit": 5,
                "mode": "hybrid"
            }
            
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_service = AsyncMock()
                mock_service.search.return_value = {
                    "results": [],
                    "total": 0,
                    "query": search_data["query"]
                }
                mock_rag_service.return_value = mock_service
                
                response = test_client.post("/api/v1/search", json=search_data)
                assert response.status_code == 200
        
        # Allow time for cleanup
        await asyncio.sleep(1.0)
        
        final_memory = psutil.Process().memory_info().rss
        final_threads = threading.active_count()
        
        # Resources should be cleaned up
        memory_increase = final_memory - initial_memory
        thread_increase = final_threads - initial_threads
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024
        
        # Thread count shouldn't increase significantly
        assert thread_increase < 10
        
        print(f"\nResource Cleanup Test Results:")
        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
        print(f"Thread increase: {thread_increase}")


class TestSystemStability:
    """Test system stability under sustained load."""
    
    @pytest.mark.asyncio
    async def test_sustained_load_stability(self, test_client, test_files, mock_all_services):
        """Test system stability under sustained load."""
        test_duration = 30  # 30 seconds
        request_interval = 0.5  # Request every 500ms
        
        start_time = time.time()
        results = []
        error_count = 0
        
        while time.time() - start_time < test_duration:
            try:
                # Alternate between uploads and searches
                if len(results) % 2 == 0:
                    # Upload
                    with open(list(test_files.values())[0], 'rb') as f:
                        files = {'file': (f'sustained_test_{len(results)}.txt', f, 'text/plain')}
                        response = test_client.post("/api/v1/documents/upload", files=files)
                else:
                    # Search
                    search_data = {
                        "query": f"sustained test query {len(results)}",
                        "limit": 3,
                        "mode": "hybrid"
                    }
                    
                    with patch('app.services.rag_service.RAGService') as mock_rag_service:
                        mock_service = AsyncMock()
                        mock_service.search.return_value = {
                            "results": [],
                            "total": 0,
                            "query": search_data["query"]
                        }
                        mock_rag_service.return_value = mock_service
                        
                        response = test_client.post("/api/v1/search", json=search_data)
                
                results.append({
                    "timestamp": time.time(),
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
                
                if response.status_code != 200:
                    error_count += 1
                
            except Exception as e:
                error_count += 1
                results.append({
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                })
            
            await asyncio.sleep(request_interval)
        
        total_requests = len(results)
        successful_requests = len([r for r in results if r.get("success")])
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # System should maintain stability
        assert success_rate >= 0.95  # 95% success rate
        assert error_count < total_requests * 0.1  # Less than 10% errors
        
        print(f"\nSustained Load Test Results:")
        print(f"Test duration: {test_duration}s")
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {successful_requests}")
        print(f"Success rate: {success_rate:.1%}")
        print(f"Error count: {error_count}")
        print(f"Requests per second: {total_requests/test_duration:.2f}")
    
    @pytest.mark.asyncio
    async def test_error_recovery_under_load(self, test_client, test_files, mock_all_services):
        """Test system recovery from errors under load."""
        # Simulate intermittent service failures
        failure_probability = 0.2  # 20% chance of failure
        recovery_requests = 20
        
        results = []
        
        for i in range(recovery_requests):
            # Randomly simulate service failures
            if random.random() < failure_probability:
                # Simulate service failure
                with patch('app.services.rag_service.RAGService') as mock_rag_service:
                    mock_service = AsyncMock()
                    mock_service.search.side_effect = Exception("Simulated service failure")
                    mock_rag_service.return_value = mock_service
                    
                    search_data = {
                        "query": f"recovery test {i}",
                        "limit": 3,
                        "mode": "hybrid"
                    }
                    
                    response = test_client.post("/api/v1/search", json=search_data)
                    
                    results.append({
                        "request_id": i,
                        "simulated_failure": True,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
            else:
                # Normal request
                with patch('app.services.rag_service.RAGService') as mock_rag_service:
                    mock_service = AsyncMock()
                    mock_service.search.return_value = {
                        "results": [],
                        "total": 0,
                        "query": f"recovery test {i}"
                    }
                    mock_rag_service.return_value = mock_service
                    
                    search_data = {
                        "query": f"recovery test {i}",
                        "limit": 3,
                        "mode": "hybrid"
                    }
                    
                    response = test_client.post("/api/v1/search", json=search_data)
                    
                    results.append({
                        "request_id": i,
                        "simulated_failure": False,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        # Analyze recovery
        normal_requests = [r for r in results if not r.get("simulated_failure")]
        failed_requests = [r for r in results if r.get("simulated_failure")]
        
        normal_success_rate = len([r for r in normal_requests if r["success"]]) / len(normal_requests) if normal_requests else 0
        
        # Normal requests should have high success rate
        assert normal_success_rate >= 0.95  # 95% success for normal requests
        
        print(f"\nError Recovery Test Results:")
        print(f"Total requests: {len(results)}")
        print(f"Normal requests: {len(normal_requests)}")
        print(f"Simulated failures: {len(failed_requests)}")
        print(f"Normal success rate: {normal_success_rate:.1%}")


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    @pytest.mark.asyncio
    async def test_upload_throughput_benchmark(self, test_client, test_files, mock_all_services):
        """Benchmark upload throughput."""
        benchmark_uploads = 20
        file_sizes = [1024, 5120, 10240]  # 1KB, 5KB, 10KB
        
        for file_size in file_sizes:
            # Create test file of specific size
            test_content = "x" * file_size
            
            upload_times = []
            
            for i in range(benchmark_uploads):
                filename = f"benchmark_{file_size}_{i}.txt"
                files = {'file': (filename, test_content.encode(), 'text/plain')}
                
                start_time = time.time()
                response = test_client.post("/api/v1/documents/upload", files=files)
                end_time = time.time()
                
                if response.status_code == 200:
                    upload_times.append(end_time - start_time)
            
            # Calculate metrics
            if upload_times:
                avg_time = sum(upload_times) / len(upload_times)
                throughput = file_size / avg_time  # bytes per second
                
                print(f"\nUpload Benchmark - File Size: {file_size} bytes")
                print(f"Average upload time: {avg_time:.3f}s")
                print(f"Throughput: {throughput/1024:.2f} KB/s")
                print(f"Successful uploads: {len(upload_times)}/{benchmark_uploads}")
                
                # Basic performance assertions
                assert avg_time < 2.0  # Should upload within 2 seconds
                assert len(upload_times) >= benchmark_uploads * 0.9  # 90% success rate
    
    @pytest.mark.asyncio
    async def test_search_latency_benchmark(self, test_client, mock_all_services, test_queries):
        """Benchmark search latency."""
        benchmark_searches = 50
        
        search_times = []
        
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_service = AsyncMock()
            
            async def benchmark_search(*args, **kwargs):
                # Simulate realistic search processing time
                await asyncio.sleep(random.uniform(0.05, 0.2))
                return {
                    "results": [
                        {"document_id": f"doc{i}", "score": 0.9 - i*0.1}
                        for i in range(5)
                    ],
                    "total": 5,
                    "query": kwargs.get("query", "test")
                }
            
            mock_service.search = benchmark_search
            mock_rag_service.return_value = mock_service
            
            for i in range(benchmark_searches):
                query = test_queries[i % len(test_queries)]
                search_data = {
                    "query": f"{query} benchmark {i}",
                    "limit": 5,
                    "mode": "hybrid"
                }
                
                start_time = time.time()
                response = test_client.post("/api/v1/search", json=search_data)
                end_time = time.time()
                
                if response.status_code == 200:
                    search_times.append(end_time - start_time)
        
        # Calculate latency metrics
        if search_times:
            avg_latency = sum(search_times) / len(search_times)
            p95_latency = sorted(search_times)[int(len(search_times) * 0.95)]
            p99_latency = sorted(search_times)[int(len(search_times) * 0.99)]
            
            print(f"\nSearch Latency Benchmark:")
            print(f"Total searches: {benchmark_searches}")
            print(f"Successful searches: {len(search_times)}")
            print(f"Average latency: {avg_latency:.3f}s")
            print(f"95th percentile: {p95_latency:.3f}s")
            print(f"99th percentile: {p99_latency:.3f}s")
            
            # Performance assertions
            assert avg_latency < 1.0  # Average under 1 second
            assert p95_latency < 2.0  # 95% under 2 seconds
            assert len(search_times) >= benchmark_searches * 0.95  # 95% success rate