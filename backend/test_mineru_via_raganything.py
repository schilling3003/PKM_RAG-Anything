#!/usr/bin/env python3
"""
Test MinerU integration through RAG-Anything
"""

import os
import tempfile
from pathlib import Path
from raganything import RAGAnything, RAGAnythingConfig
from raganything.mineru_parser import MineruParser

def test_mineru_parser_direct():
    """Test MinerU parser directly"""
    print("Testing MinerU parser directly...")
    
    try:
        parser = MineruParser()
        print(f"✓ MinerU parser created successfully")
        print(f"  Parser type: {type(parser)}")
        print(f"  Available methods: {[m for m in dir(parser) if not m.startswith('_')]}")
        return True
    except Exception as e:
        print(f"✗ Failed to create MinerU parser: {e}")
        return False

def test_raganything_with_mineru():
    """Test RAG-Anything configuration with MinerU"""
    print("\nTesting RAG-Anything with MinerU...")
    
    try:
        # Create a basic config
        config = RAGAnythingConfig()
        print(f"✓ RAG-Anything config created")
        
        # Initialize RAG-Anything
        rag = RAGAnything(config=config)
        print(f"✓ RAG-Anything initialized")
        
        # Check available processors
        if hasattr(rag, 'processors'):
            print(f"  Available processors: {list(rag.processors.keys()) if rag.processors else 'None'}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to initialize RAG-Anything: {e}")
        return False

def test_mineru_version_info():
    """Test MinerU version and configuration"""
    print("\nTesting MinerU version and configuration...")
    
    try:
        from mineru.version import __version__
        print(f"✓ MinerU version: {__version__}")
        
        # Test basic MinerU import
        import mineru
        print(f"✓ MinerU package available at: {mineru.__path__}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to get MinerU info: {e}")
        return False

def main():
    """Run all MinerU tests"""
    print("=" * 60)
    print("MinerU Integration Test via RAG-Anything")
    print("=" * 60)
    
    results = []
    
    # Test MinerU version info
    results.append(test_mineru_version_info())
    
    # Test MinerU parser directly
    results.append(test_mineru_parser_direct())
    
    # Test RAG-Anything with MinerU
    results.append(test_raganything_with_mineru())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All MinerU integration tests passed!")
        print("✓ MinerU 2.0 is properly installed and accessible through RAG-Anything")
    else:
        print("✗ Some tests failed. MinerU integration needs attention.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)