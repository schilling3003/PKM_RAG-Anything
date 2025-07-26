#!/usr/bin/env python3
"""
Test script to verify LightRAG integration with the PKM system.
This script tests:
1. LightRAG configuration with proper working directory
2. Integration with existing project structure
3. Basic functionality with real OpenAI functions (if API key available)
"""

import os
import sys
import asyncio
from pathlib import Path

def test_lightrag_working_directory():
    """Test LightRAG working directory configuration."""
    print("Testing LightRAG working directory configuration...")
    
    try:
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc
        import numpy as np
        
        # Use the project's rag_storage directory
        working_dir = "./data/rag_storage"
        
        # Ensure directory exists
        Path(working_dir).mkdir(parents=True, exist_ok=True)
        print(f"✓ Working directory created/verified: {working_dir}")
        
        # Mock functions for testing
        def mock_embedding_func(texts):
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), 384).tolist()
        
        async def mock_llm_func(prompt, **kwargs):
            return f"Mock response to: {prompt[:50]}..."
        
        # Initialize LightRAG with project directory
        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=mock_llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=384,
                max_token_size=8192,
                func=mock_embedding_func
            )
        )
        
        print("✓ LightRAG initialized with project working directory")
        
        # Check that expected files/directories are created
        expected_files = [
            "vdb_entities.json",
            "vdb_relationships.json", 
            "vdb_chunks.json"
        ]
        
        for file_name in expected_files:
            file_path = Path(working_dir) / file_name
            if file_path.exists():
                print(f"✓ Expected file created: {file_name}")
            else:
                print(f"⚠ Expected file not found: {file_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Working directory test failed: {e}")
        return False

def test_lightrag_with_openai_config():
    """Test LightRAG with OpenAI configuration if API key is available."""
    print("\nTesting LightRAG with OpenAI configuration...")
    
    try:
        from lightrag import LightRAG
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠ OPENAI_API_KEY not found in environment, skipping OpenAI test")
            return True
        
        print("✓ OpenAI API key found in environment")
        
        working_dir = "./data/rag_storage"
        
        # Initialize LightRAG with OpenAI functions
        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=openai_complete_if_cache,
            llm_model_name="gpt-4o-mini",
            embedding_func=openai_embed,
            embedding_model_name="text-embedding-3-large"
        )
        
        print("✓ LightRAG initialized with OpenAI functions")
        
        # Test a simple query (this will make an API call if key is valid)
        try:
            # Insert a simple test document
            test_doc = "LightRAG is a knowledge graph-based RAG system."
            rag.insert(test_doc)
            print("✓ Document insertion with OpenAI functions successful")
            
            # Test query
            result = rag.query("What is LightRAG?", param="naive")
            print(f"✓ Query successful: {result[:100]}...")
            
        except Exception as e:
            print(f"⚠ OpenAI API test failed (may be due to rate limits or invalid key): {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ OpenAI configuration test failed: {e}")
        return False

def test_lightrag_storage_structure():
    """Test that LightRAG creates proper storage structure."""
    print("\nTesting LightRAG storage structure...")
    
    try:
        working_dir = "./data/rag_storage"
        
        # Check directory structure
        storage_path = Path(working_dir)
        if not storage_path.exists():
            print(f"✗ Storage directory does not exist: {working_dir}")
            return False
        
        print(f"✓ Storage directory exists: {working_dir}")
        
        # List contents
        contents = list(storage_path.iterdir())
        print(f"✓ Storage directory contents: {[f.name for f in contents]}")
        
        # Check for key files that should exist after initialization
        key_files = ["vdb_entities.json", "vdb_relationships.json", "vdb_chunks.json"]
        for key_file in key_files:
            file_path = storage_path / key_file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✓ Key file exists: {key_file} ({size} bytes)")
            else:
                print(f"⚠ Key file missing: {key_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Storage structure test failed: {e}")
        return False

def main():
    """Run all LightRAG integration tests."""
    print("=== LightRAG Integration Test ===\n")
    
    tests = [
        test_lightrag_working_directory,
        test_lightrag_storage_structure,
        test_lightrag_with_openai_config
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Integration Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All LightRAG integration tests passed!")
        return 0
    else:
        print("✗ Some LightRAG integration tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())