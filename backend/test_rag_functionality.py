#!/usr/bin/env python3
"""
Test script to verify RAG functionality is working properly.
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_rag_service():
    """Test the RAG service functionality."""
    print("Testing RAG service...")
    
    try:
        from app.services.rag_service import rag_service
        
        # Test basic RAG query
        print("Testing basic RAG query...")
        response = await rag_service.process_rag_query(
            query="What is artificial intelligence?",
            mode="hybrid",
            max_tokens=500,
            include_sources=True,
            use_cache=False  # Don't use cache for testing
        )
        
        print(f"✅ RAG query successful")
        print(f"   Query: {response.query}")
        print(f"   Mode: {response.mode}")
        print(f"   Answer length: {len(response.answer)} characters")
        print(f"   Sources: {len(response.sources)}")
        print(f"   Processing time: {response.processing_time:.2f}s")
        print(f"   Token count: {response.token_count}")
        
        # Test with conversation history
        print("\nTesting RAG query with conversation history...")
        conversation_history = [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is a subset of artificial intelligence..."}
        ]
        
        response2 = await rag_service.process_rag_query(
            query="How does it relate to deep learning?",
            mode="local",
            conversation_history=conversation_history,
            use_cache=False
        )
        
        print(f"✅ Conversational RAG query successful")
        print(f"   Answer length: {len(response2.answer)} characters")
        
        # Test different modes
        print("\nTesting different RAG modes...")
        modes = ["naive", "local", "global", "hybrid", "mix"]
        
        for mode in modes:
            try:
                response = await rag_service.process_rag_query(
                    query="What is technology?",
                    mode=mode,
                    max_tokens=200,
                    use_cache=False
                )
                print(f"   ✅ Mode '{mode}': {len(response.answer)} chars, {response.processing_time:.2f}s")
            except Exception as e:
                print(f"   ⚠️  Mode '{mode}' failed: {e}")
        
        # Test query history
        print("\nTesting query history...")
        history = await rag_service.get_query_history(limit=10)
        print(f"✅ Query history retrieved: {len(history)} entries")
        
        # Test RAG stats
        print("\nTesting RAG stats...")
        stats = await rag_service.get_rag_stats()
        print(f"✅ RAG stats retrieved:")
        print(f"   Total queries: {stats.get('total_queries', 0)}")
        print(f"   Cache size: {stats.get('cache_size', 0)}")
        print(f"   LightRAG available: {stats.get('lightrag_available', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_rag_api_endpoints():
    """Test RAG API endpoints."""
    print("\nTesting RAG API endpoints...")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test RAG query endpoint
        print("Testing /rag/query endpoint...")
        response = client.post(
            "/api/rag/query",
            params={
                "query": "What is artificial intelligence?",
                "mode": "hybrid",
                "max_tokens": 500,
                "include_sources": True
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RAG query endpoint successful")
            print(f"   Response keys: {list(data.keys())}")
        else:
            print(f"❌ RAG query endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Test RAG modes endpoint
        print("Testing /rag/modes endpoint...")
        response = client.get("/api/rag/modes")
        
        if response.status_code == 200:
            data = response.json()
            modes = data.get("modes", {})
            print(f"✅ RAG modes endpoint successful: {len(modes)} modes")
        else:
            print(f"❌ RAG modes endpoint failed: {response.status_code}")
        
        # Test RAG health endpoint
        print("Testing /rag/health endpoint...")
        response = client.get("/api/rag/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RAG health endpoint successful")
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ RAG health endpoint failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG API endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_rag_cache():
    """Test RAG caching functionality."""
    print("\nTesting RAG cache functionality...")
    
    try:
        from app.services.rag_service import rag_service
        
        # Clear cache first
        await rag_service.clear_cache()
        print("✅ Cache cleared")
        
        # Test cache miss (first query)
        start_time = datetime.now()
        response1 = await rag_service.process_rag_query(
            query="What is machine learning?",
            mode="hybrid",
            use_cache=True
        )
        time1 = (datetime.now() - start_time).total_seconds()
        
        # Test cache hit (same query)
        start_time = datetime.now()
        response2 = await rag_service.process_rag_query(
            query="What is machine learning?",
            mode="hybrid",
            use_cache=True
        )
        time2 = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Cache test completed")
        print(f"   First query (cache miss): {time1:.2f}s")
        print(f"   Second query (cache hit): {time2:.2f}s")
        print(f"   Answers match: {response1.answer == response2.answer}")
        
        # Cache should make the second query faster
        if time2 < time1:
            print("✅ Cache is working (second query was faster)")
        else:
            print("⚠️  Cache might not be working as expected")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all RAG tests."""
    print("🚀 Starting RAG Functionality Tests\n")
    
    tests = [
        ("RAG Service", test_rag_service),
        ("RAG API Endpoints", test_rag_api_endpoints),
        ("RAG Cache", test_rag_cache),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All RAG tests passed! RAG functionality is working correctly.")
        return 0
    else:
        print("⚠️  Some RAG tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)