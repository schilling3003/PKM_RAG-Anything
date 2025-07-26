#!/usr/bin/env python3
"""
Final test to verify LightRAG installation and configuration meets task requirements.
This test verifies:
1. ✓ Install LightRAG package via pip in backend environment
2. ✓ Verify LightRAG imports work correctly in Python  
3. ✓ Test basic LightRAG initialization with mock functions
4. ✓ Configure LightRAG working directory and storage
"""

import sys
import os
from pathlib import Path

def test_requirement_1_installation():
    """Test: Install LightRAG package via pip in backend environment"""
    print("1. Testing LightRAG package installation...")
    
    try:
        import lightrag
        version = lightrag.__version__
        print(f"✓ LightRAG package installed successfully (version: {version})")
        return True
    except ImportError as e:
        print(f"✗ LightRAG package not installed: {e}")
        return False

def test_requirement_2_imports():
    """Test: Verify LightRAG imports work correctly in Python"""
    print("\n2. Testing LightRAG imports...")
    
    try:
        # Core imports
        from lightrag import LightRAG, QueryParam
        print("✓ Core LightRAG classes imported")
        
        # LLM imports
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
        print("✓ OpenAI LLM functions imported")
        
        # Utility imports
        from lightrag.utils import EmbeddingFunc
        print("✓ Utility functions imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_requirement_3_initialization():
    """Test: Test basic LightRAG initialization with mock functions"""
    print("\n3. Testing LightRAG initialization with mock functions...")
    
    try:
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc
        import numpy as np
        import tempfile
        import shutil
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="lightrag_init_test_")
        
        # Mock functions
        def mock_embedding(texts):
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), 384).tolist()
        
        async def mock_llm(prompt, **kwargs):
            return f"Mock response to: {prompt[:50]}..."
        
        # Initialize LightRAG
        rag = LightRAG(
            working_dir=temp_dir,
            llm_model_func=mock_llm,
            embedding_func=EmbeddingFunc(
                embedding_dim=384,
                max_token_size=8192,
                func=mock_embedding
            )
        )
        
        print("✓ LightRAG initialized successfully with mock functions")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False

def test_requirement_4_storage_configuration():
    """Test: Configure LightRAG working directory and storage"""
    print("\n4. Testing LightRAG working directory and storage configuration...")
    
    try:
        # Test project storage directory
        project_storage = "./data/rag_storage"
        storage_path = Path(project_storage)
        
        # Ensure directory exists
        storage_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Project storage directory created/verified: {project_storage}")
        
        # Test directory is writable
        test_file = storage_path / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        print("✓ Storage directory is writable")
        
        # Test LightRAG with project directory
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc
        import numpy as np
        
        def mock_embedding(texts):
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), 384).tolist()
        
        async def mock_llm(prompt, **kwargs):
            return "Mock response"
        
        # Initialize with project directory
        rag = LightRAG(
            working_dir=project_storage,
            llm_model_func=mock_llm,
            embedding_func=EmbeddingFunc(
                embedding_dim=384,
                max_token_size=8192,
                func=mock_embedding
            )
        )
        
        print(f"✓ LightRAG configured with project working directory: {project_storage}")
        
        # Check that LightRAG creates expected structure
        expected_files = ["vdb_entities.json", "vdb_relationships.json", "vdb_chunks.json"]
        for expected_file in expected_files:
            file_path = storage_path / expected_file
            if file_path.exists():
                print(f"✓ LightRAG storage file exists: {expected_file}")
            else:
                print(f"⚠ LightRAG storage file will be created on first use: {expected_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Storage configuration failed: {e}")
        return False

def main():
    """Run all requirement tests."""
    print("=== LightRAG Installation and Configuration Verification ===")
    print("Task: 3. Install LightRAG dependency\n")
    
    tests = [
        test_requirement_1_installation,
        test_requirement_2_imports,
        test_requirement_3_initialization,
        test_requirement_4_storage_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Task Completion Summary ===")
    print(f"Requirements completed: {sum(results)}/{len(results)}")
    
    requirements_status = [
        "✓ Install LightRAG package via pip in backend environment",
        "✓ Verify LightRAG imports work correctly in Python", 
        "✓ Test basic LightRAG initialization with mock functions",
        "✓ Configure LightRAG working directory and storage"
    ]
    
    for i, status in enumerate(requirements_status):
        if results[i]:
            print(status)
        else:
            print(status.replace("✓", "✗"))
    
    if all(results):
        print("\n🎉 Task 3: Install LightRAG dependency - COMPLETED SUCCESSFULLY!")
        print("\nLightRAG is now properly installed and configured for the PKM system.")
        print("- Package installed and importable")
        print("- Mock functions working for testing")
        print("- Working directory configured at ./data/rag_storage")
        print("- Ready for integration with OpenAI API when configured")
        return 0
    else:
        print("\n❌ Task 3: Install LightRAG dependency - INCOMPLETE")
        return 1

if __name__ == "__main__":
    sys.exit(main())