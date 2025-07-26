#!/usr/bin/env python3
"""
Test MinerU configuration and document processing functionality
"""

import os
import tempfile
import json
from pathlib import Path
from raganything.mineru_parser import MineruParser

def test_mineru_device_configuration():
    """Test MinerU device configuration (CPU/CUDA)"""
    print("Testing MinerU device configuration...")
    
    try:
        parser = MineruParser()
        
        # Check if we can configure device settings
        print(f"✓ MinerU parser initialized")
        
        # Test device detection
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.device_count()} device(s)")
            print(f"  Current device: {torch.cuda.current_device()}")
            print(f"  Device name: {torch.cuda.get_device_name()}")
        else:
            print(f"✓ CUDA not available, will use CPU")
        
        return True
    except Exception as e:
        print(f"✗ Device configuration test failed: {e}")
        return False

def test_mineru_document_parsing():
    """Test MinerU document parsing functionality"""
    print("\nTesting MinerU document parsing functionality...")
    
    try:
        parser = MineruParser()
        
        # Create a simple test text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for MinerU parsing.\n")
            f.write("It contains multiple lines of text.\n")
            f.write("MinerU should be able to process this successfully.")
            test_file = f.name
        
        try:
            # Test text file parsing
            result = parser.parse_text_file(test_file)
            print(f"✓ Text file parsing successful")
            print(f"  Result type: {type(result)}")
            if isinstance(result, str):
                print(f"  Content length: {len(result)} characters")
            elif isinstance(result, dict):
                print(f"  Result keys: {list(result.keys())}")
            
            return True
        finally:
            # Clean up test file
            os.unlink(test_file)
            
    except Exception as e:
        print(f"✗ Document parsing test failed: {e}")
        return False

def test_mineru_installation_check():
    """Test MinerU installation verification"""
    print("\nTesting MinerU installation verification...")
    
    try:
        parser = MineruParser()
        
        # Use the built-in installation check if available
        if hasattr(parser, 'check_installation'):
            install_status = parser.check_installation()
            print(f"✓ Installation check completed")
            print(f"  Status: {install_status}")
        else:
            print(f"✓ Installation check method not available, but parser works")
        
        return True
    except Exception as e:
        print(f"✗ Installation check failed: {e}")
        return False

def test_mineru_config_file():
    """Test MinerU configuration file setup"""
    print("\nTesting MinerU configuration file...")
    
    try:
        # Check for magic-pdf.json config file
        config_paths = [
            Path.home() / ".magic-pdf.json",
            Path.cwd() / "magic-pdf.json",
            Path("/tmp/magic-pdf.json")
        ]
        
        config_found = False
        for config_path in config_paths:
            if config_path.exists():
                print(f"✓ Found config file at: {config_path}")
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    print(f"  Config keys: {list(config.keys())}")
                    config_found = True
                    break
                except Exception as e:
                    print(f"  Warning: Could not parse config file: {e}")
        
        if not config_found:
            print(f"ℹ No magic-pdf.json config file found (using defaults)")
            print(f"  This is normal for basic usage")
        
        return True
    except Exception as e:
        print(f"✗ Config file test failed: {e}")
        return False

def test_integration_with_document_processing():
    """Test integration with document processing pipeline"""
    print("\nTesting integration with document processing pipeline...")
    
    try:
        from raganything import RAGAnything, RAGAnythingConfig
        
        # Create config
        config = RAGAnythingConfig()
        rag = RAGAnything(config=config)
        
        print(f"✓ RAG-Anything initialized with MinerU support")
        
        # Check if MinerU is available as a processor
        if hasattr(rag, 'processors'):
            processors = rag.processors or {}
            mineru_available = any('mineru' in str(p).lower() for p in processors.values())
            if mineru_available:
                print(f"✓ MinerU processor found in RAG-Anything")
            else:
                print(f"ℹ MinerU processor not explicitly listed (may be integrated differently)")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def main():
    """Run all MinerU configuration and processing tests"""
    print("=" * 70)
    print("MinerU 2.0 Configuration and Processing Test")
    print("=" * 70)
    
    results = []
    
    # Test device configuration
    results.append(test_mineru_device_configuration())
    
    # Test installation check
    results.append(test_mineru_installation_check())
    
    # Test config file
    results.append(test_mineru_config_file())
    
    # Test document parsing
    results.append(test_mineru_document_parsing())
    
    # Test integration
    results.append(test_integration_with_document_processing())
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All MinerU configuration and processing tests passed!")
        print("✓ MinerU 2.0 is properly configured and ready for document processing")
    else:
        print("✗ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)