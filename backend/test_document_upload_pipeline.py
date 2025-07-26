#!/usr/bin/env python3
"""
Comprehensive test for document upload and processing pipeline.

This test verifies:
1. Basic document upload with all services running
2. Celery task processing works end-to-end
3. Advanced document processing with RAG-Anything and MinerU
4. Knowledge graph construction with LightRAG
5. Semantic search and embedding generation

Requirements tested: 1.1, 1.2, 1.3, 5.1, 5.2, 6.1, 6.2
"""

import os
import sys
import time
import json
import asyncio
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentUploadPipelineTest:
    """Comprehensive test suite for document upload and processing pipeline."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.test_results = {}
        self.test_files = []
        
    def create_test_files(self) -> List[str]:
        """Create test files for different document types."""
        test_files = []
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="pkm_test_")
        logger.info(f"Created test directory: {self.temp_dir}")
        
        # 1. Text file
        text_file = os.path.join(self.temp_dir, "test_document.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("""
            This is a test document for the AI PKM Tool.
            
            It contains information about artificial intelligence, machine learning, and knowledge management.
            
            Key concepts:
            - Natural Language Processing (NLP)
            - Large Language Models (LLMs)
            - Retrieval Augmented Generation (RAG)
            - Knowledge Graphs
            - Vector Embeddings
            
            This document should be processed by RAG-Anything with MinerU 2.0,
            indexed in the knowledge graph using LightRAG,
            and made searchable through semantic embeddings.
            """)
        test_files.append(text_file)
        
        # 2. Markdown file
        md_file = os.path.join(self.temp_dir, "test_notes.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("""
# AI PKM Tool Test Notes

## Overview
This is a test markdown document for the Personal Knowledge Management system.

## Features to Test
- **Document Processing**: RAG-Anything + MinerU integration
- **Knowledge Graph**: LightRAG-based relationship extraction
- **Semantic Search**: Vector embeddings and similarity search
- **Multimodal Support**: Text, images, audio, video processing

## Technical Stack
- Backend: FastAPI with Celery
- AI Processing: RAG-Anything framework
- Knowledge Graph: LightRAG
- Vector Database: ChromaDB
- Task Queue: Redis + Celery

## Test Scenarios
1. Upload and basic processing
2. Knowledge graph construction
3. Semantic search functionality
4. Error handling and recovery
            """)
        test_files.append(md_file)
        
        # 3. JSON file (structured data)
        json_file = os.path.join(self.temp_dir, "test_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "project": "AI PKM Tool",
                "version": "1.0.0",
                "components": {
                    "backend": {
                        "framework": "FastAPI",
                        "database": "SQLite",
                        "vector_db": "ChromaDB",
                        "task_queue": "Celery + Redis"
                    },
                    "ai_processing": {
                        "multimodal": "RAG-Anything",
                        "document_extraction": "MinerU 2.0",
                        "knowledge_graph": "LightRAG",
                        "embeddings": "OpenAI text-embedding-3-large"
                    }
                },
                "test_data": {
                    "entities": ["AI", "Machine Learning", "Knowledge Management", "RAG", "LLM"],
                    "relationships": [
                        {"source": "RAG", "target": "Knowledge Management", "type": "enhances"},
                        {"source": "LLM", "target": "AI", "type": "is_part_of"},
                        {"source": "Vector Embeddings", "target": "Semantic Search", "type": "enables"}
                    ]
                }
            }, f, indent=2)
        test_files.append(json_file)
        
        self.test_files = test_files
        return test_files
    
    def cleanup_test_files(self):
        """Clean up test files and directories."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up test directory: {self.temp_dir}")
    
    async def test_service_health(self) -> Dict[str, Any]:
        """Test 1: Verify all required services are running."""
        logger.info("🔍 Testing service health...")
        
        health_checks = {
            "redis": f"{self.api_base}/health/redis",
            "celery": f"{self.api_base}/health/celery", 
            "lightrag": f"{self.api_base}/health/lightrag",
            "raganything": f"{self.api_base}/health/raganything",
            "openai": f"{self.api_base}/health/openai",
            "storage": f"{self.api_base}/health/storage"
        }
        
        results = {}
        all_healthy = True
        
        for service, url in health_checks.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results[service] = {
                        "status": "healthy",
                        "details": data
                    }
                    logger.info(f"✅ {service.upper()} service is healthy")
                else:
                    results[service] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }
                    logger.error(f"❌ {service.upper()} service is unhealthy: HTTP {response.status_code}")
                    all_healthy = False
                    
            except Exception as e:
                results[service] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ {service.upper()} service error: {e}")
                all_healthy = False
        
        self.test_results["service_health"] = {
            "all_healthy": all_healthy,
            "services": results
        }
        
        return results
    
    async def test_document_upload(self, file_path: str) -> Dict[str, Any]:
        """Test 2: Basic document upload functionality."""
        logger.info(f"📤 Testing document upload: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                response = requests.post(f"{self.api_base}/documents/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Upload successful: {data.get('document_id')}")
                return {
                    "success": True,
                    "document_id": data.get("document_id"),
                    "task_id": data.get("task_id"),
                    "status": data.get("status"),
                    "message": data.get("message")
                }
            else:
                logger.error(f"❌ Upload failed: HTTP {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_processing_status(self, document_id: str, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Test 3: Monitor document processing status until completion."""
        logger.info(f"⏳ Monitoring processing status for document: {document_id}")
        
        start_time = time.time()
        last_status = None
        status_history = []
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_base}/documents/{document_id}/status", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    current_status = data.get("status")
                    progress = data.get("progress", 0)
                    current_step = data.get("current_step", "")
                    
                    if current_status != last_status:
                        logger.info(f"📊 Status: {current_status} ({progress}%) - {current_step}")
                        last_status = current_status
                        
                        status_history.append({
                            "timestamp": time.time(),
                            "status": current_status,
                            "progress": progress,
                            "current_step": current_step
                        })
                    
                    if current_status in ["completed", "failed"]:
                        if current_status == "completed":
                            logger.info(f"✅ Processing completed for document: {document_id}")
                        else:
                            logger.error(f"❌ Processing failed for document: {document_id}")
                            logger.error(f"Error: {data.get('error', 'Unknown error')}")
                        
                        return {
                            "success": current_status == "completed",
                            "final_status": current_status,
                            "processing_time": time.time() - start_time,
                            "status_history": status_history,
                            "final_data": data
                        }
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Status check error: {e}")
                await asyncio.sleep(5)
        
        logger.error(f"❌ Processing timeout after {timeout} seconds")
        return {
            "success": False,
            "error": "timeout",
            "processing_time": timeout,
            "status_history": status_history
        }
    
    async def test_document_retrieval(self, document_id: str) -> Dict[str, Any]:
        """Test 4: Verify document data was stored correctly."""
        logger.info(f"📋 Testing document retrieval: {document_id}")
        
        try:
            response = requests.get(f"{self.api_base}/documents/{document_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["id", "filename", "file_type", "file_size", "processing_status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    logger.error(f"❌ Missing required fields: {missing_fields}")
                    return {
                        "success": False,
                        "error": "missing_fields",
                        "missing_fields": missing_fields
                    }
                
                # Check if text was extracted
                has_extracted_text = bool(data.get("extracted_text"))
                text_length = len(data.get("extracted_text", ""))
                
                logger.info(f"✅ Document retrieved successfully")
                logger.info(f"📝 Extracted text: {text_length} characters")
                
                return {
                    "success": True,
                    "document_data": data,
                    "has_extracted_text": has_extracted_text,
                    "text_length": text_length,
                    "processing_status": data.get("processing_status")
                }
                
            else:
                logger.error(f"❌ Document retrieval failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Document retrieval error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_semantic_search(self, query: str = "artificial intelligence machine learning") -> Dict[str, Any]:
        """Test 5: Verify semantic search functionality."""
        logger.info(f"🔍 Testing semantic search: '{query}'")
        
        try:
            search_data = {
                "query": query,
                "limit": 5,
                "mode": "hybrid"  # Test hybrid RAG mode
            }
            
            response = requests.post(f"{self.api_base}/search", json=search_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                logger.info(f"✅ Search completed: {len(results)} results found")
                
                # Analyze results
                has_relevant_results = len(results) > 0
                avg_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0
                
                for i, result in enumerate(results[:3]):  # Show top 3
                    logger.info(f"📄 Result {i+1}: {result.get('document_id', 'N/A')} (score: {result.get('score', 0):.3f})")
                
                return {
                    "success": True,
                    "query": query,
                    "results_count": len(results),
                    "has_relevant_results": has_relevant_results,
                    "average_score": avg_score,
                    "results": results
                }
                
            else:
                logger.error(f"❌ Search failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_knowledge_graph_query(self, query: str = "What is the relationship between AI and machine learning?") -> Dict[str, Any]:
        """Test 6: Verify knowledge graph functionality with LightRAG."""
        logger.info(f"🕸️ Testing knowledge graph query: '{query}'")
        
        try:
            kg_data = {
                "query": query,
                "mode": "global",  # Test global knowledge graph mode
                "max_tokens": 1000
            }
            
            response = requests.post(f"{self.api_base}/rag/query", json=kg_data, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_answer = bool(data.get("answer"))
                has_sources = bool(data.get("sources"))
                has_entities = bool(data.get("entities"))
                has_relationships = bool(data.get("relationships"))
                
                logger.info(f"✅ Knowledge graph query completed")
                logger.info(f"📝 Answer length: {len(data.get('answer', ''))}")
                logger.info(f"📚 Sources: {len(data.get('sources', []))}")
                logger.info(f"🏷️ Entities: {len(data.get('entities', []))}")
                logger.info(f"🔗 Relationships: {len(data.get('relationships', []))}")
                
                return {
                    "success": True,
                    "query": query,
                    "has_answer": has_answer,
                    "has_sources": has_sources,
                    "has_entities": has_entities,
                    "has_relationships": has_relationships,
                    "answer_length": len(data.get("answer", "")),
                    "sources_count": len(data.get("sources", [])),
                    "entities_count": len(data.get("entities", [])),
                    "relationships_count": len(data.get("relationships", [])),
                    "response_data": data
                }
                
            else:
                logger.error(f"❌ Knowledge graph query failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Knowledge graph query error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_multimodal_processing(self) -> Dict[str, Any]:
        """Test 7: Verify RAG-Anything multimodal processing capabilities."""
        logger.info("🎭 Testing multimodal processing capabilities...")
        
        # This test checks if the system can handle different file types
        # and extract multimodal content appropriately
        
        results = {}
        
        for file_path in self.test_files:
            file_type = os.path.splitext(file_path)[1].lower()
            logger.info(f"🔍 Testing {file_type} file processing...")
            
            # Upload and process the file
            upload_result = await self.test_document_upload(file_path)
            
            if upload_result.get("success"):
                document_id = upload_result["document_id"]
                task_id = upload_result["task_id"]
                
                # Wait for processing
                processing_result = await self.test_processing_status(document_id, task_id, timeout=120)
                
                if processing_result.get("success"):
                    # Get document details to check multimodal processing
                    doc_result = await self.test_document_retrieval(document_id)
                    
                    if doc_result.get("success"):
                        doc_data = doc_result["document_data"]
                        
                        results[file_type] = {
                            "success": True,
                            "document_id": document_id,
                            "has_extracted_text": doc_result["has_extracted_text"],
                            "text_length": doc_result["text_length"],
                            "metadata": doc_data.get("doc_metadata", {})
                        }
                        
                        logger.info(f"✅ {file_type} processing successful")
                    else:
                        results[file_type] = {
                            "success": False,
                            "error": "document_retrieval_failed",
                            "details": doc_result
                        }
                else:
                    results[file_type] = {
                        "success": False,
                        "error": "processing_failed",
                        "details": processing_result
                    }
            else:
                results[file_type] = {
                    "success": False,
                    "error": "upload_failed",
                    "details": upload_result
                }
        
        successful_types = [ft for ft, result in results.items() if result.get("success")]
        
        return {
            "success": len(successful_types) > 0,
            "processed_file_types": successful_types,
            "total_file_types": len(results),
            "results": results
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete document upload and processing pipeline test."""
        logger.info("🚀 Starting comprehensive document upload and processing pipeline test...")
        
        start_time = time.time()
        
        try:
            # Create test files
            test_files = self.create_test_files()
            logger.info(f"📁 Created {len(test_files)} test files")
            
            # Test 1: Service Health
            logger.info("\n" + "="*60)
            logger.info("TEST 1: SERVICE HEALTH CHECKS")
            logger.info("="*60)
            health_results = await self.test_service_health()
            
            if not self.test_results["service_health"]["all_healthy"]:
                logger.error("❌ Some services are not healthy. Cannot proceed with full pipeline test.")
                return {
                    "success": False,
                    "error": "services_unhealthy",
                    "results": self.test_results
                }
            
            # Test 2-7: Full Pipeline Test
            logger.info("\n" + "="*60)
            logger.info("TEST 2-7: FULL DOCUMENT PROCESSING PIPELINE")
            logger.info("="*60)
            
            # Test multimodal processing
            multimodal_results = await self.test_multimodal_processing()
            self.test_results["multimodal_processing"] = multimodal_results
            
            # Test semantic search (after documents are processed)
            if multimodal_results.get("success"):
                logger.info("\n" + "-"*40)
                logger.info("TESTING SEMANTIC SEARCH")
                logger.info("-"*40)
                search_results = await self.test_semantic_search()
                self.test_results["semantic_search"] = search_results
                
                # Test knowledge graph query
                logger.info("\n" + "-"*40)
                logger.info("TESTING KNOWLEDGE GRAPH")
                logger.info("-"*40)
                kg_results = await self.test_knowledge_graph_query()
                self.test_results["knowledge_graph"] = kg_results
            
            # Calculate overall success
            total_time = time.time() - start_time
            
            # Determine overall success
            critical_tests = ["service_health", "multimodal_processing"]
            overall_success = all(
                self.test_results.get(test, {}).get("success", False) 
                for test in critical_tests
            )
            
            # Generate summary
            logger.info("\n" + "="*60)
            logger.info("TEST SUMMARY")
            logger.info("="*60)
            
            for test_name, result in self.test_results.items():
                status = "✅ PASS" if result.get("success") else "❌ FAIL"
                logger.info(f"{status} {test_name.replace('_', ' ').title()}")
            
            logger.info(f"\n⏱️ Total test time: {total_time:.2f} seconds")
            logger.info(f"🎯 Overall result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
            
            return {
                "success": overall_success,
                "total_time": total_time,
                "test_results": self.test_results,
                "summary": {
                    "services_healthy": self.test_results.get("service_health", {}).get("all_healthy", False),
                    "multimodal_processing": self.test_results.get("multimodal_processing", {}).get("success", False),
                    "semantic_search": self.test_results.get("semantic_search", {}).get("success", False),
                    "knowledge_graph": self.test_results.get("knowledge_graph", {}).get("success", False)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_results": self.test_results
            }
        
        finally:
            # Cleanup
            self.cleanup_test_files()


async def main():
    """Main test execution function."""
    print("🧪 AI PKM Tool - Document Upload and Processing Pipeline Test")
    print("=" * 70)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not running or not healthy")
            print("Please start the backend server first:")
            print("cd backend && uvicorn app.main:app --reload")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please start the backend server first:")
        print("cd backend && uvicorn app.main:app --reload")
        return
    
    # Run the comprehensive test
    tester = DocumentUploadPipelineTest()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    results_file = "test_results_document_pipeline.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if results.get("success") else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())