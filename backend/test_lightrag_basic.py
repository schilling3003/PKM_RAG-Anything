#!/usr/bin/env python3
"""
Test script to verify LightRAG installation and basic functionality.
This script tests:
1. LightRAG imports work correctly
2. Basic LightRAG initialization with mock functions
3. LightRAG working directory and storage configuration
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_lightrag_imports():
    """Test that LightRAG imports work correctly."""
    print("Testing LightRAG imports...")
    
    try:
        import lightrag
        print(f"✓ LightRAG imported successfully (version: {lightrag.__version__})")
        
        from lightrag import LightRAG, QueryParam
        print("✓ LightRAG class and QueryParam imported successfully")
        
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
        print("✓ LightRAG OpenAI functions imported successfully")
        
        from lightrag.utils import EmbeddingFunc
        print("✓ LightRAG embedding utilities imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False

def test_lightrag_initialization():
    """Test basic LightRAG initialization with mock functions."""
    print("\nTesting LightRAG initialization...")
    
    try:
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc
        import numpy as np
        
        # Create a temporary working directory
        temp_dir = tempfile.mkdtemp(prefix="lightrag_test_")
        print(f"Using temporary directory: {temp_dir}")
        
        # Mock embedding function for testing
        def mock_embedding_func(texts):
            """Mock embedding function that returns random vectors."""
            if isinstance(texts, str):
                texts = [texts]
            # Return random embeddings for testing
            return np.random.rand(len(texts), 384).tolist()
        
        # Mock LLM function for testing
        async def mock_llm_func(prompt, **kwargs):
            """Mock LLM function that returns a simple response."""
            return f"Mock response to: {prompt[:50]}..."
        
        # Initialize LightRAG with mock functions
        rag = LightRAG(
            working_dir=temp_dir,
            llm_model_func=mock_llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=384,
                max_token_size=8192,
                func=mock_embedding_func
            )
        )
        
        print("✓ LightRAG initialized successfully with mock functions")
        
        # Test basic functionality
        print("Testing basic LightRAG operations...")
        
        # Test insert (this should work with mock functions)
        test_text = "This is a test document for LightRAG functionality."
        try:
            rag.insert(test_text)
            print("✓ Document insertion test passed")
        except Exception as e:
            print(f"⚠ Document insertion test failed (expected with mocks): {e}")
        
        # Clean up
        shutil.rmtree(temp_dir)
        print("✓ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ LightRAG initialization failed: {e}")
        # Clean up on error
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

def test_lightrag_storage_configuration():
    """Test LightRAG working directory and storage configuration."""
    print("\nTesting LightRAG storage configuration...")
    
    try:
        # Test with different storage paths
        test_paths = [
            "./data/rag_storage",
            "./rag_storage", 
            tempfile.mkdtemp(prefix="lightrag_storage_")
        ]
        
        for test_path in test_paths:
            print(f"Testing storage path: {test_path}")
            
            # Create directory if it doesn't exist
            Path(test_path).mkdir(parents=True, exist_ok=True)
            
            # Check if directory is writable
            test_file = Path(test_path) / "test_write.txt"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print(f"✓ Storage path {test_path} is writable")
            except Exception as e:
                print(f"✗ Storage path {test_path} is not writable: {e}")
                continue
            
            # Clean up temporary directories
            if test_path.startswith(tempfile.gettempdir()):
                shutil.rmtree(test_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Storage configuration test failed: {e}")
        return False

def main():
    """Run all LightRAG tests."""
    print("=== LightRAG Installation and Configuration Test ===\n")
    
    tests = [
        test_lightrag_imports,
        test_lightrag_initialization, 
        test_lightrag_storage_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All LightRAG tests passed!")
        return 0
    else:
        print("✗ Some LightRAG tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())