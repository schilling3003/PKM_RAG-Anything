#!/usr/bin/env python3
"""
Test script to verify LightRAG integration is working properly.
"""

import os
import sys
import asyncio
import tempfile
import shutil
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_lightrag_import():
    """Test LightRAG import and basic functionality."""
    print("Testing LightRAG import...")
    
    try:
        from lightrag import LightRAG, QueryParam
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
        from lightrag.utils import EmbeddingFunc
        from lightrag.kg.shared_storage import initialize_pipeline_status
        print("✅ LightRAG imports successful")
        return True
    except ImportError as e:
        print(f"❌ LightRAG import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ LightRAG import error: {e}")
        return False

async def test_lightrag_initialization():
    """Test LightRAG initialization with mock functions."""
    print("\nTesting LightRAG initialization...")
    
    try:
        from lightrag import LightRAG, QueryParam
        from lightrag.utils import EmbeddingFunc
        from lightrag.kg.shared_storage import initialize_pipeline_status
        
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        print(f"Using temporary directory: {temp_dir}")
        
        # Mock LLM function
        async def mock_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            return f"Mock response to: {prompt[:50]}..."
        
        # Mock embedding function
        async def mock_embedding_func(texts):
            # Return mock embeddings (1536 dimensions for OpenAI compatibility)
            import numpy as np
            return np.random.random((len(texts), 1536)).tolist()
        
        # Initialize LightRAG
        rag = LightRAG(
            working_dir=temp_dir,
            llm_model_func=mock_llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=mock_embedding_func
            )
        )
        
        # Initialize storages
        await rag.initialize_storages()
        await initialize_pipeline_status()
        
        print("✅ LightRAG initialization successful")
        
        # Test basic insertion
        print("Testing document insertion...")
        test_content = "This is a test document about artificial intelligence and machine learning."
        
        if hasattr(rag, 'ainsert'):
            await rag.ainsert(test_content)
        else:
            rag.insert(test_content)
        
        print("✅ Document insertion successful")
        
        # Test query
        print("Testing query...")
        query_param = QueryParam(mode="hybrid")
        
        if hasattr(rag, 'aquery'):
            response = await rag.aquery("What is artificial intelligence?", param=query_param)
        else:
            response = rag.query("What is artificial intelligence?", param=query_param)
        
        print(f"✅ Query successful. Response: {response[:100]}...")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ LightRAG initialization failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        return False

async def test_knowledge_graph_service():
    """Test the knowledge graph service integration."""
    print("\nTesting knowledge graph service...")
    
    try:
        from app.services.knowledge_graph import knowledge_graph_service
        
        # Test document processing
        test_content = "Apple Inc. is a technology company founded by Steve Jobs. The company develops iPhones and MacBooks."
        
        result = await knowledge_graph_service.build_graph_from_document(
            document_id="test_doc_1",
            content=test_content,
            metadata={"filename": "test.txt", "type": "document"}
        )
        
        print(f"✅ Knowledge graph service test result: {result}")
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ Knowledge graph service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_semantic_search_service():
    """Test the semantic search service."""
    print("\nTesting semantic search service...")
    
    try:
        from app.services.semantic_search import semantic_search_service
        
        # Test search stats
        stats = await semantic_search_service.get_search_stats()
        print(f"✅ Search stats: {stats}")
        
        # Test search suggestions
        suggestions = await semantic_search_service.get_search_suggestions("artificial")
        print(f"✅ Search suggestions: {suggestions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Semantic search service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting LightRAG Integration Tests\n")
    
    tests = [
        ("LightRAG Import", test_lightrag_import),
        ("LightRAG Initialization", test_lightrag_initialization),
        ("Knowledge Graph Service", test_knowledge_graph_service),
        ("Semantic Search Service", test_semantic_search_service),
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
        print("🎉 All tests passed! LightRAG integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)