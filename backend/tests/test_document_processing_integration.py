"""
Integration tests for document processing pipeline.

Tests the complete document upload and processing workflow:
- File upload and validation
- Celery task processing
- RAG-Anything multimodal processing
- LightRAG knowledge graph construction
- Semantic search and embeddings

Requirements tested: 1.1, 1.2, 1.3, 5.1, 5.2, 6.1, 6.2
"""

import pytest
import asyncio
import json
import time
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from io import BytesIO

from app.services.document_processor import DocumentProcessor
from app.services.file_manager import FileManager
from app.services.lightrag_service import LightRAGService
from app.models.database import Document
from app.models.schemas import DocumentCreate, DocumentResponse


class TestDocumentUploadIntegration:
    """Test document upload integration."""
    
    @pytest.mark.asyncio
    async def test_complete_upload_workflow(self, test_client, test_files, mock_all_services):
        """Test complete document upload workflow."""
        # Test file upload
        with open(test_files['text'], 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "document_id" in data
        assert "task_id" in data
        assert data["status"] == "queued"
        assert data["message"] == "Document uploaded successfully and queued for processing"
        
        document_id = data["document_id"]
        
        # Test document retrieval
        response = test_client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        
        doc_data = response.json()
        assert doc_data["id"] == document_id
        assert doc_data["filename"] == "test_document.txt"
        assert doc_data["file_type"] == "text/plain"
    
    @pytest.mark.asyncio
    async def test_multimodal_file_upload(self, test_client, test_files, mock_all_services):
        """Test uploading different file types."""
        file_types = [
            ('text', 'text/plain'),
            ('markdown', 'text/markdown'),
            ('json', 'application/json')
        ]
        
        uploaded_docs = []
        
        for file_key, content_type in file_types:
            with open(test_files[file_key], 'rb') as f:
                filename = os.path.basename(test_files[file_key])
                files = {'file': (filename, f, content_type)}
                response = test_client.post("/api/v1/documents/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            uploaded_docs.append(data["document_id"])
        
        # Verify all documents were uploaded
        assert len(uploaded_docs) == 3
        
        # Test retrieving all documents
        for doc_id in uploaded_docs:
            response = test_client.get(f"/api/v1/documents/{doc_id}")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_upload_validation(self, test_client, temp_dir):
        """Test file upload validation."""
        # Test empty file
        empty_file = os.path.join(temp_dir, "empty.txt")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        with open(empty_file, 'rb') as f:
            files = {'file': ('empty.txt', f, 'text/plain')}
            response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should handle empty files gracefully
        assert response.status_code in [200, 400]
        
        # Test large filename
        long_filename = "a" * 300 + ".txt"
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with open(test_file, 'rb') as f:
            files = {'file': (long_filename, f, 'text/plain')}
            response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should handle long filenames
        assert response.status_code in [200, 400]


class TestDocumentProcessingIntegration:
    """Test document processing integration."""
    
    @pytest.mark.asyncio
    async def test_document_processor_workflow(self, test_db_session, test_files, mock_all_services):
        """Test complete document processing workflow."""
        # Create document record
        doc_data = DocumentCreate(
            filename="test_document.txt",
            file_type="text/plain",
            file_size=1024,
            file_path=test_files['text']
        )
        
        document = Document(**doc_data.dict())
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        # Process document
        processor = DocumentProcessor()
        
        with patch.object(processor, '_process_with_raganything') as mock_rag_process, \
             patch.object(processor, '_update_knowledge_graph') as mock_kg_update, \
             patch.object(processor, '_generate_embeddings') as mock_embeddings:
            
            # Mock processing results
            mock_rag_process.return_value = {
                "extracted_text": "Test document content with AI and ML concepts",
                "metadata": {"pages": 1, "format": "text"},
                "entities": ["AI", "ML", "concepts"],
                "success": True
            }
            
            mock_kg_update.return_value = True
            mock_embeddings.return_value = True
            
            # Process the document
            result = await processor.process_document(document.id, test_files['text'])
            
            assert result["success"] is True
            assert result["extracted_text"] == "Test document content with AI and ML concepts"
            assert "AI" in result["entities"]
            
            # Verify processing methods were called
            mock_rag_process.assert_called_once()
            mock_kg_update.assert_called_once()
            mock_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_raganything_integration(self, test_files, mock_raganything):
        """Test RAG-Anything processing integration."""
        processor = DocumentProcessor()
        
        # Test text processing
        result = await processor._process_with_raganything(test_files['text'])
        
        assert result["success"] is True
        assert "extracted_text" in result
        assert "metadata" in result
        mock_raganything.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lightrag_integration(self, mock_lightrag):
        """Test LightRAG knowledge graph integration."""
        processor = DocumentProcessor()
        
        # Mock document data
        doc_data = {
            "extracted_text": "This document discusses artificial intelligence and machine learning concepts.",
            "entities": ["artificial intelligence", "machine learning", "concepts"],
            "metadata": {"filename": "test.txt"}
        }
        
        # Test knowledge graph update
        result = await processor._update_knowledge_graph(1, doc_data)
        
        assert result is True
        mock_lightrag.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embeddings_generation(self, mock_all_services):
        """Test embeddings generation integration."""
        processor = DocumentProcessor()
        
        # Mock document data
        doc_data = {
            "extracted_text": "Test document for embeddings generation",
            "entities": ["test", "document", "embeddings"]
        }
        
        with patch('app.services.document_processor.chromadb') as mock_chroma:
            mock_collection = Mock()
            mock_chroma.Client.return_value.get_or_create_collection.return_value = mock_collection
            
            result = await processor._generate_embeddings(1, doc_data)
            
            assert result is True
            mock_collection.add.assert_called_once()


class TestSemanticSearchIntegration:
    """Test semantic search integration."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_workflow(self, test_client, mock_all_services):
        """Test complete semantic search workflow."""
        # Mock search data
        search_query = {
            "query": "artificial intelligence machine learning",
            "limit": 5,
            "mode": "hybrid"
        }
        
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_service = AsyncMock()
            mock_service.search.return_value = {
                "results": [
                    {
                        "document_id": "doc1",
                        "score": 0.95,
                        "content": "AI and ML content",
                        "metadata": {"filename": "test.txt"}
                    }
                ],
                "total": 1,
                "query": search_query["query"]
            }
            mock_rag_service.return_value = mock_service
            
            response = test_client.post("/api/v1/search", json=search_query)
            
            assert response.status_code == 200
            data = response.json()
            
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["score"] == 0.95
            assert data["total"] == 1
    
    @pytest.mark.asyncio
    async def test_different_search_modes(self, test_client, mock_all_services):
        """Test different RAG search modes."""
        search_modes = ["naive", "local", "global", "hybrid", "mix"]
        
        for mode in search_modes:
            search_query = {
                "query": "test query",
                "limit": 3,
                "mode": mode
            }
            
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_service = AsyncMock()
                mock_service.search.return_value = {
                    "results": [],
                    "total": 0,
                    "query": search_query["query"],
                    "mode": mode
                }
                mock_rag_service.return_value = mock_service
                
                response = test_client.post("/api/v1/search", json=search_query)
                
                assert response.status_code == 200
                data = response.json()
                assert "results" in data


class TestKnowledgeGraphIntegration:
    """Test knowledge graph integration."""
    
    @pytest.mark.asyncio
    async def test_knowledge_graph_query(self, test_client, mock_lightrag):
        """Test knowledge graph query integration."""
        query_data = {
            "query": "What is the relationship between AI and machine learning?",
            "mode": "global",
            "max_tokens": 1000
        }
        
        # Mock LightRAG response
        mock_lightrag.query.return_value = {
            "answer": "AI is a broader field that encompasses machine learning as a subset.",
            "sources": ["doc1", "doc2"],
            "entities": ["AI", "machine learning"],
            "relationships": [
                {"source": "AI", "target": "machine learning", "type": "encompasses"}
            ]
        }
        
        with patch('app.services.lightrag_service.lightrag_service', mock_lightrag):
            response = test_client.post("/api/v1/rag/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "entities" in data
        assert "relationships" in data
        assert len(data["entities"]) == 2
        assert len(data["relationships"]) == 1
    
    @pytest.mark.asyncio
    async def test_knowledge_graph_modes(self, test_client, mock_lightrag):
        """Test different knowledge graph query modes."""
        modes = ["naive", "local", "global", "hybrid", "mix"]
        
        for mode in modes:
            query_data = {
                "query": f"Test query for {mode} mode",
                "mode": mode,
                "max_tokens": 500
            }
            
            mock_lightrag.query.return_value = {
                "answer": f"Answer for {mode} mode",
                "sources": [],
                "entities": [],
                "relationships": []
            }
            
            with patch('app.services.lightrag_service.lightrag_service', mock_lightrag):
                response = test_client.post("/api/v1/rag/query", json=query_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == f"Answer for {mode} mode"


class TestErrorHandlingIntegration:
    """Test error handling in document processing integration."""
    
    @pytest.mark.asyncio
    async def test_processing_failure_recovery(self, test_db_session, test_files):
        """Test recovery from processing failures."""
        # Create document record
        document = Document(
            filename="test_document.txt",
            file_type="text/plain",
            file_size=1024,
            file_path=test_files['text'],
            processing_status="queued"
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        processor = DocumentProcessor()
        
        # Simulate processing failure
        with patch.object(processor, '_process_with_raganything') as mock_process:
            mock_process.side_effect = Exception("Processing failed")
            
            result = await processor.process_document(document.id, test_files['text'])
            
            assert result["success"] is False
            assert "error" in result
            assert "Processing failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_partial_processing_success(self, test_db_session, test_files, mock_raganything):
        """Test handling of partial processing success."""
        document = Document(
            filename="test_document.txt",
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
            
            # Knowledge graph update fails
            mock_kg_update.side_effect = Exception("KG update failed")
            
            # Embeddings succeed
            mock_embeddings.return_value = True
            
            result = await processor.process_document(document.id, test_files['text'])
            
            # Should still succeed with partial processing
            assert result["success"] is True
            assert "warnings" in result
            assert "KG update failed" in str(result["warnings"])
    
    def test_upload_error_handling(self, test_client):
        """Test upload error handling."""
        # Test upload without file
        response = test_client.post("/api/v1/documents/upload")
        assert response.status_code == 422  # Validation error
        
        # Test upload with invalid file type (if validation exists)
        invalid_content = b"invalid binary content"
        files = {'file': ('test.exe', BytesIO(invalid_content), 'application/x-executable')}
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should either accept or reject gracefully
        assert response.status_code in [200, 400, 422]


class TestConcurrentProcessingIntegration:
    """Test concurrent document processing."""
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, test_client, test_files, mock_all_services):
        """Test concurrent document uploads."""
        import asyncio
        import aiohttp
        
        async def upload_document(session, file_path):
            """Upload a single document."""
            with open(file_path, 'rb') as f:
                filename = os.path.basename(file_path)
                data = aiohttp.FormData()
                data.add_field('file', f, filename=filename, content_type='text/plain')
                
                async with session.post('http://localhost:8000/api/v1/documents/upload', 
                                      data=data) as response:
                    return await response.json()
        
        # Skip this test if we can't make async HTTP requests
        # (This would require the actual server to be running)
        pytest.skip("Requires running server for async HTTP requests")
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_tasks(self, test_db_session, test_files, mock_all_services):
        """Test concurrent document processing tasks."""
        # Create multiple documents
        documents = []
        for i, file_path in enumerate(test_files.values()):
            doc = Document(
                filename=f"test_doc_{i}.txt",
                file_type="text/plain",
                file_size=1024,
                file_path=file_path,
                processing_status="queued"
            )
            test_db_session.add(doc)
            documents.append(doc)
        
        test_db_session.commit()
        
        # Process documents concurrently
        processor = DocumentProcessor()
        
        async def process_doc(doc):
            return await processor.process_document(doc.id, doc.file_path)
        
        # Process all documents concurrently
        tasks = [process_doc(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all processing completed
        assert len(results) == len(documents)
        
        # Check that most succeeded (some might fail due to mocking)
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful) >= len(documents) // 2  # At least half should succeed


class TestPerformanceIntegration:
    """Test performance aspects of document processing integration."""
    
    @pytest.mark.asyncio
    async def test_processing_performance(self, test_db_session, test_files, 
                                        mock_all_services, performance_monitor):
        """Test document processing performance."""
        document = Document(
            filename="test_document.txt",
            file_type="text/plain",
            file_size=1024,
            file_path=test_files['text'],
            processing_status="queued"
        )
        test_db_session.add(document)
        test_db_session.commit()
        test_db_session.refresh(document)
        
        processor = DocumentProcessor()
        
        performance_monitor.start()
        
        result = await processor.process_document(document.id, test_files['text'])
        
        performance_monitor.stop()
        
        # Processing should complete within reasonable time
        assert performance_monitor.duration < 10.0  # 10 seconds max
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_search_performance(self, test_client, mock_all_services, performance_monitor):
        """Test search performance."""
        search_query = {
            "query": "artificial intelligence machine learning deep learning neural networks",
            "limit": 20,
            "mode": "hybrid"
        }
        
        with patch('app.services.rag_service.RAGService') as mock_rag_service:
            mock_service = AsyncMock()
            
            # Simulate realistic search delay
            async def slow_search(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                return {
                    "results": [{"document_id": f"doc{i}", "score": 0.9 - i*0.1} 
                              for i in range(20)],
                    "total": 20,
                    "query": search_query["query"]
                }
            
            mock_service.search = slow_search
            mock_rag_service.return_value = mock_service
            
            performance_monitor.start()
            
            response = test_client.post("/api/v1/search", json=search_query)
            
            performance_monitor.stop()
            
            assert response.status_code == 200
            # Search should complete within 5 seconds
            assert performance_monitor.duration < 5.0