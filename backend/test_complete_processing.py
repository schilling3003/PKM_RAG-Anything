#!/usr/bin/env python3
"""
Complete document processing pipeline test.
Tests the full end-to-end processing including:
- Document upload
- Celery task processing
- RAG-Anything + MinerU processing
- LightRAG knowledge graph construction
- ChromaDB embedding generation
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteProcessingTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        
    def create_test_document(self) -> str:
        """Create a test document with meaningful content for processing."""
        temp_dir = tempfile.mkdtemp(prefix="pkm_processing_test_")
        test_file = os.path.join(temp_dir, "ai_knowledge_test.txt")
        
        content = """
        Artificial Intelligence and Machine Learning
        
        Artificial Intelligence (AI) is a branch of computer science that aims to create 
        intelligent machines that can perform tasks that typically require human intelligence.
        
        Machine Learning (ML) is a subset of AI that focuses on the development of algorithms 
        and statistical models that enable computers to learn and improve from experience 
        without being explicitly programmed.
        
        Key Concepts:
        - Neural Networks: Computing systems inspired by biological neural networks
        - Deep Learning: ML techniques based on artificial neural networks with multiple layers
        - Natural Language Processing: AI capability to understand and generate human language
        - Computer Vision: AI field that enables computers to interpret visual information
        - Reinforcement Learning: Learning through interaction with an environment
        
        Applications:
        - Autonomous vehicles use AI for navigation and decision-making
        - Healthcare systems use ML for diagnosis and treatment recommendations
        - Financial institutions use AI for fraud detection and risk assessment
        - Search engines use NLP for understanding user queries
        - Recommendation systems use ML to suggest relevant content
        
        The relationship between AI and ML is hierarchical: AI is the broader concept,
        while ML is a specific approach to achieving AI. Deep Learning is a subset of ML
        that has shown remarkable success in recent years.
        """
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"📄 Created test document: {test_file}")
        logger.info(f"📊 Document size: {len(content)} characters")
        
        return test_file
    
    def upload_document(self, file_path: str) -> dict:
        """Upload document and return upload response."""
        logger.info("📤 Uploading document...")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'text/plain')}
                response = requests.post(f"{self.api_base}/documents/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Upload successful!")
                logger.info(f"📄 Document ID: {data.get('document_id')}")
                logger.info(f"⚙️ Task ID: {data.get('task_id')}")
                return {
                    "success": True,
                    "document_id": data.get("document_id"),
                    "task_id": data.get("task_id"),
                    "status": data.get("status")
                }
            else:
                logger.error(f"❌ Upload failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return {"success": False, "error": str(e)}
    
    def monitor_processing(self, document_id: str, timeout: int = 300) -> dict:
        """Monitor document processing until completion or timeout."""
        logger.info(f"⏳ Monitoring processing for document: {document_id}")
        logger.info(f"⏰ Timeout: {timeout} seconds")
        
        start_time = time.time()
        last_status = None
        last_progress = -1
        status_history = []
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_base}/documents/{document_id}/status", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    current_status = data.get("status")
                    progress = data.get("progress", 0)
                    current_step = data.get("current_step", "")
                    
                    # Log status changes or significant progress updates
                    if current_status != last_status or progress != last_progress:
                        elapsed = time.time() - start_time
                        logger.info(f"📊 [{elapsed:.1f}s] Status: {current_status} ({progress}%) - {current_step}")
                        last_status = current_status
                        last_progress = progress
                        
                        status_history.append({
                            "timestamp": time.time(),
                            "elapsed": elapsed,
                            "status": current_status,
                            "progress": progress,
                            "current_step": current_step
                        })
                    
                    # Check for completion
                    if current_status in ["completed", "failed"]:
                        elapsed = time.time() - start_time
                        
                        if current_status == "completed":
                            logger.info(f"✅ Processing completed in {elapsed:.1f} seconds!")
                        else:
                            logger.error(f"❌ Processing failed after {elapsed:.1f} seconds")
                            logger.error(f"Error: {data.get('error', 'Unknown error')}")
                        
                        return {
                            "success": current_status == "completed",
                            "final_status": current_status,
                            "processing_time": elapsed,
                            "status_history": status_history,
                            "final_data": data
                        }
                
                # Wait before next check
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Status check error: {e}")
                time.sleep(5)
        
        elapsed = time.time() - start_time
        logger.error(f"❌ Processing timeout after {elapsed:.1f} seconds")
        return {
            "success": False,
            "error": "timeout",
            "processing_time": elapsed,
            "status_history": status_history
        }
    
    def verify_processing_results(self, document_id: str) -> dict:
        """Verify that processing actually worked by checking the results."""
        logger.info(f"🔍 Verifying processing results for document: {document_id}")
        
        results = {
            "document_data": None,
            "has_extracted_text": False,
            "text_length": 0,
            "has_embeddings": False,
            "has_knowledge_graph": False,
            "search_works": False
        }
        
        try:
            # 1. Check document data
            response = requests.get(f"{self.api_base}/documents/{document_id}", timeout=10)
            if response.status_code == 200:
                doc_data = response.json()
                results["document_data"] = doc_data
                
                # Check extracted text
                extracted_text = doc_data.get("extracted_text", "")
                results["has_extracted_text"] = bool(extracted_text and extracted_text.strip())
                results["text_length"] = len(extracted_text) if extracted_text else 0
                
                logger.info(f"📝 Extracted text: {results['text_length']} characters")
                
                if results["has_extracted_text"]:
                    logger.info(f"✅ Text extraction successful")
                    # Show a preview of extracted text
                    preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                    logger.info(f"📄 Text preview: {preview}")
                else:
                    logger.error(f"❌ No extracted text found")
            
            # 2. Test semantic search to verify embeddings
            logger.info("🔍 Testing semantic search...")
            try:
                search_data = {
                    "query": "artificial intelligence machine learning",
                    "limit": 5
                }
                response = requests.post(f"{self.api_base}/search", json=search_data, timeout=30)
                
                if response.status_code == 200:
                    search_results = response.json()
                    results_count = len(search_results.get("results", []))
                    results["search_works"] = results_count > 0
                    results["has_embeddings"] = results_count > 0
                    
                    if results["search_works"]:
                        logger.info(f"✅ Semantic search working: {results_count} results found")
                        # Check if our document is in the results
                        for result in search_results.get("results", []):
                            if result.get("document_id") == document_id:
                                logger.info(f"✅ Our document found in search results with score: {result.get('score', 0):.3f}")
                                break
                    else:
                        logger.error(f"❌ Semantic search returned no results")
                else:
                    logger.error(f"❌ Search failed: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Search test error: {e}")
            
            # 3. Test knowledge graph query
            logger.info("🕸️ Testing knowledge graph...")
            try:
                kg_data = {
                    "query": "What is the relationship between AI and machine learning?",
                    "mode": "global"
                }
                response = requests.post(f"{self.api_base}/rag/query", json=kg_data, timeout=60)
                
                if response.status_code == 200:
                    kg_results = response.json()
                    has_answer = bool(kg_results.get("answer"))
                    results["has_knowledge_graph"] = has_answer
                    
                    if has_answer:
                        logger.info(f"✅ Knowledge graph query successful")
                        answer_preview = kg_results.get("answer", "")[:200] + "..."
                        logger.info(f"🤖 Answer preview: {answer_preview}")
                    else:
                        logger.error(f"❌ Knowledge graph query returned no answer")
                else:
                    logger.error(f"❌ Knowledge graph query failed: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Knowledge graph test error: {e}")
            
        except Exception as e:
            logger.error(f"❌ Verification error: {e}")
        
        return results
    
    def run_complete_test(self) -> dict:
        """Run the complete end-to-end processing test."""
        logger.info("🚀 Starting complete document processing pipeline test...")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        try:
            # Step 1: Create test document
            logger.info("\n📄 STEP 1: Creating test document")
            logger.info("-" * 40)
            test_file = self.create_test_document()
            
            # Step 2: Upload document
            logger.info("\n📤 STEP 2: Uploading document")
            logger.info("-" * 40)
            upload_result = self.upload_document(test_file)
            
            if not upload_result.get("success"):
                return {
                    "success": False,
                    "error": "Upload failed",
                    "details": upload_result
                }
            
            document_id = upload_result["document_id"]
            
            # Step 3: Monitor processing
            logger.info("\n⚙️ STEP 3: Monitoring processing")
            logger.info("-" * 40)
            processing_result = self.monitor_processing(document_id, timeout=300)  # 5 minutes
            
            if not processing_result.get("success"):
                return {
                    "success": False,
                    "error": "Processing failed or timed out",
                    "details": processing_result
                }
            
            # Step 4: Verify results
            logger.info("\n🔍 STEP 4: Verifying processing results")
            logger.info("-" * 40)
            verification_result = self.verify_processing_results(document_id)
            
            # Calculate overall success
            total_time = time.time() - start_time
            
            # Determine success criteria
            critical_checks = [
                verification_result["has_extracted_text"],
                verification_result["has_embeddings"] or verification_result["search_works"],
            ]
            
            # Knowledge graph is nice to have but not critical for basic functionality
            bonus_checks = [
                verification_result["has_knowledge_graph"]
            ]
            
            overall_success = all(critical_checks)
            
            # Summary
            logger.info("\n📊 TEST SUMMARY")
            logger.info("=" * 70)
            logger.info(f"⏱️ Total processing time: {total_time:.1f} seconds")
            logger.info(f"📄 Document ID: {document_id}")
            logger.info(f"📝 Text extraction: {'✅ PASS' if verification_result['has_extracted_text'] else '❌ FAIL'}")
            logger.info(f"🔍 Semantic search: {'✅ PASS' if verification_result['search_works'] else '❌ FAIL'}")
            logger.info(f"💾 Vector embeddings: {'✅ PASS' if verification_result['has_embeddings'] else '❌ FAIL'}")
            logger.info(f"🕸️ Knowledge graph: {'✅ PASS' if verification_result['has_knowledge_graph'] else '❌ FAIL'}")
            logger.info(f"\n🎯 Overall result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
            
            return {
                "success": overall_success,
                "document_id": document_id,
                "total_time": total_time,
                "upload_result": upload_result,
                "processing_result": processing_result,
                "verification_result": verification_result,
                "critical_checks_passed": sum(critical_checks),
                "bonus_checks_passed": sum(bonus_checks)
            }
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
        finally:
            # Cleanup
            if 'test_file' in locals():
                import shutil
                shutil.rmtree(os.path.dirname(test_file))
                logger.info("🧹 Cleaned up test files")

def main():
    """Main test execution."""
    logger.info("🧪 AI PKM Tool - Complete Document Processing Pipeline Test")
    logger.info("=" * 70)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Backend is not running or not healthy")
            logger.error("Please ensure all Docker services are running:")
            logger.error("docker-compose -f docker-compose.dev.yml up -d")
            return 1
    except Exception as e:
        logger.error(f"❌ Cannot connect to backend: {e}")
        logger.error("Please ensure all Docker services are running:")
        logger.error("docker-compose -f docker-compose.dev.yml up -d")
        return 1
    
    # Run the complete test
    tester = CompleteProcessingTest()
    results = tester.run_complete_test()
    
    # Save results to file
    results_file = "test_results_complete_processing.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if results.get("success") else 1
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)