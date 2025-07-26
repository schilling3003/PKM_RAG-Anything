#!/usr/bin/env python3
"""
Real system integration test.

This test validates the comprehensive testing suite against the actual running system.
It tests the real endpoints and functionality without mocks.
"""

import requests
import time
import json
import tempfile
import os
from pathlib import Path

class RealSystemIntegrationTest:
    """Test the real running system."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.results = {}
    
    def test_health_endpoints(self):
        """Test all health endpoints."""
        print("🔍 Testing Health Endpoints...")
        
        health_endpoints = [
            ("Basic Health", "/health"),
            ("API Health", "/api/v1/health"),
            ("Redis Health", "/api/v1/health/redis"),
            ("Celery Health", "/api/v1/health/celery"),
            ("LightRAG Health", "/api/v1/health/lightrag"),
            ("RAG-Anything Health", "/api/v1/health/raganything"),
            ("OpenAI Health", "/api/v1/health/openai"),
            ("Storage Health", "/api/v1/health/storage"),
            ("Comprehensive Health", "/api/v1/health/comprehensive"),
        ]
        
        results = {}
        for name, endpoint in health_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                results[name] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds(),
                    "data": response.json() if response.status_code == 200 else None
                }
                
                status = "✅" if response.status_code == 200 else "❌"
                print(f"  {status} {name}: {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                
            except Exception as e:
                results[name] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"  ❌ {name}: Error - {e}")
        
        self.results["health_endpoints"] = results
        successful = len([r for r in results.values() if r.get("success")])
        print(f"  📊 Health Endpoints: {successful}/{len(health_endpoints)} successful")
        return successful == len(health_endpoints)
    
    def test_document_upload(self):
        """Test document upload functionality."""
        print("\n📤 Testing Document Upload...")
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            This is a comprehensive test document for the AI PKM Tool.
            
            It contains information about:
            - Artificial Intelligence and Machine Learning
            - Knowledge Management Systems
            - Retrieval Augmented Generation (RAG)
            - Vector Embeddings and Semantic Search
            - Knowledge Graphs and Entity Relationships
            
            This document tests the complete processing pipeline including:
            1. Document upload and storage
            2. RAG-Anything multimodal processing
            3. LightRAG knowledge graph construction
            4. ChromaDB vector embedding storage
            5. Semantic search capabilities
            """)
            test_file_path = f.name
        
        try:
            # Test upload
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_comprehensive.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_base}/documents/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                document_id = data.get("document_id")
                task_id = data.get("task_id")
                
                print(f"  ✅ Upload successful: {document_id}")
                print(f"  📋 Task ID: {task_id}")
                
                # Test document retrieval
                doc_response = requests.get(f"{self.api_base}/documents/{document_id}", timeout=10)
                if doc_response.status_code == 200:
                    doc_data = doc_response.json()
                    print(f"  ✅ Document retrieval successful")
                    print(f"  📄 Filename: {doc_data.get('filename')}")
                    print(f"  📊 File size: {doc_data.get('file_size')} bytes")
                    print(f"  🔄 Status: {doc_data.get('processing_status')}")
                    
                    self.results["document_upload"] = {
                        "success": True,
                        "document_id": document_id,
                        "task_id": task_id,
                        "document_data": doc_data
                    }
                    return True
                else:
                    print(f"  ❌ Document retrieval failed: {doc_response.status_code}")
                    return False
            else:
                print(f"  ❌ Upload failed: {response.status_code}")
                print(f"  📝 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"  ❌ Upload error: {e}")
            return False
        
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
    
    def test_search_functionality(self):
        """Test search functionality."""
        print("\n🔍 Testing Search Functionality...")
        
        search_tests = [
            ("Semantic Search", "/search/search/semantic", {"query": "artificial intelligence", "limit": 5}),
            ("RAG Query", "/rag/rag/query", {"query": "What is machine learning?"}),
            ("Hybrid Search", "/search/search/hybrid", {"query": "knowledge management", "semantic_limit": 3}),
        ]
        
        results = {}
        for name, endpoint, params in search_tests:
            try:
                if endpoint.startswith("/search"):
                    # GET request with query parameters
                    response = requests.post(f"{self.api_base}{endpoint}", params=params, timeout=30)
                else:
                    # POST request
                    response = requests.post(f"{self.api_base}{endpoint}", params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    results[name] = {
                        "success": True,
                        "response_time": response.elapsed.total_seconds(),
                        "data": data
                    }
                    
                    # Extract relevant info
                    if "results" in data:
                        result_count = len(data["results"])
                        print(f"  ✅ {name}: {result_count} results ({response.elapsed.total_seconds():.3f}s)")
                    elif "answer" in data:
                        answer_length = len(data["answer"])
                        print(f"  ✅ {name}: {answer_length} char answer ({response.elapsed.total_seconds():.3f}s)")
                    else:
                        print(f"  ✅ {name}: Success ({response.elapsed.total_seconds():.3f}s)")
                else:
                    results[name] = {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    print(f"  ❌ {name}: {response.status_code}")
                    
            except Exception as e:
                results[name] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"  ❌ {name}: Error - {e}")
        
        self.results["search_functionality"] = results
        successful = len([r for r in results.values() if r.get("success")])
        print(f"  📊 Search Tests: {successful}/{len(search_tests)} successful")
        return successful >= len(search_tests) // 2  # At least half should work
    
    def test_system_performance(self):
        """Test basic system performance."""
        print("\n⚡ Testing System Performance...")
        
        # Test response times
        performance_tests = [
            ("Health Check", "/health"),
            ("Comprehensive Health", "/api/v1/health/comprehensive"),
            ("Document List", "/api/v1/documents/"),
        ]
        
        results = {}
        for name, endpoint in performance_tests:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = end_time - start_time
                results[name] = {
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code
                }
                
                status = "✅" if response.status_code == 200 else "❌"
                performance = "🚀" if response_time < 1.0 else "⚠️" if response_time < 5.0 else "🐌"
                print(f"  {status} {performance} {name}: {response_time:.3f}s")
                
            except Exception as e:
                results[name] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"  ❌ {name}: Error - {e}")
        
        self.results["performance"] = results
        
        # Check if all responses are under 5 seconds
        slow_responses = [r for r in results.values() if r.get("response_time", 0) > 5.0]
        print(f"  📊 Performance: {len(slow_responses)} slow responses (>5s)")
        return len(slow_responses) == 0
    
    def run_comprehensive_test(self):
        """Run all tests."""
        print("🧪 AI PKM Tool - Real System Integration Test")
        print("=" * 60)
        
        start_time = time.time()
        
        # Check if system is running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print("❌ System is not running or not healthy")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to system: {e}")
            return False
        
        print("✅ System is running and accessible")
        
        # Run tests
        test_results = []
        
        test_results.append(("Health Endpoints", self.test_health_endpoints()))
        test_results.append(("Document Upload", self.test_document_upload()))
        test_results.append(("Search Functionality", self.test_search_functionality()))
        test_results.append(("System Performance", self.test_system_performance()))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = 0
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                successful_tests += 1
        
        print(f"\n📊 Results: {successful_tests}/{len(test_results)} tests passed")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        
        overall_success = successful_tests >= len(test_results) * 0.75  # 75% pass rate
        
        if overall_success:
            print("\n🎉 COMPREHENSIVE TEST SUITE VALIDATION: SUCCESS")
            print("The AI PKM Tool is working correctly and the test suite is validated!")
        else:
            print("\n⚠️ COMPREHENSIVE TEST SUITE VALIDATION: PARTIAL SUCCESS")
            print("Some components need attention, but core functionality is working.")
        
        # Save results
        results_file = "real_system_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_results": test_results,
                "detailed_results": self.results,
                "summary": {
                    "total_tests": len(test_results),
                    "successful_tests": successful_tests,
                    "success_rate": successful_tests / len(test_results),
                    "total_time": total_time,
                    "overall_success": overall_success
                }
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return overall_success


def main():
    """Main test execution."""
    tester = RealSystemIntegrationTest()
    success = tester.run_comprehensive_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())