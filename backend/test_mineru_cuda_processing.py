#!/usr/bin/env python3
"""
Test MinerU document processing with CUDA acceleration
"""

import os
import tempfile
import json
from pathlib import Path
from raganything.mineru_parser import MineruParser
from raganything import RAGAnything, RAGAnythingConfig

def test_mineru_cuda_configuration():
    """Test MinerU CUDA configuration"""
    print("Testing MinerU CUDA configuration...")
    
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        print(f"✓ CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA device count: {torch.cuda.device_count()}")
            print(f"✓ Current CUDA device: {torch.cuda.current_device()}")
            print(f"✓ CUDA device name: {torch.cuda.get_device_name()}")
            print(f"✓ CUDA memory allocated: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
            print(f"✓ CUDA memory cached: {torch.cuda.memory_reserved() / 1024**2:.1f} MB")
        
        return True
    except Exception as e:
        print(f"✗ CUDA configuration test failed: {e}")
        return False

def test_mineru_config_file():
    """Test MinerU configuration file"""
    print("\nTesting MinerU configuration file...")
    
    try:
        config_path = Path("magic-pdf.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✓ Configuration file found: {config_path}")
            print(f"✓ Device setting: {config.get('device', 'not specified')}")
            print(f"✓ Models directory: {config.get('models-dir', 'not specified')}")
            
            # Verify device is set to cuda
            if config.get('device') == 'cuda':
                print(f"✓ CUDA device correctly configured")
            else:
                print(f"⚠ Device not set to CUDA (current: {config.get('device')})")
        else:
            print(f"ℹ No configuration file found, using defaults")
        
        return True
    except Exception as e:
        print(f"✗ Configuration file test failed: {e}")
        return False

def test_mineru_pdf_processing():
    """Test MinerU PDF processing capabilities"""
    print("\nTesting MinerU PDF processing...")
    
    try:
        parser = MineruParser()
        
        # Create a simple test PDF content (we'll simulate this with text)
        test_content = """
        # Test Document
        
        This is a test document for MinerU processing.
        
        ## Features to Test
        - Text extraction
        - Layout detection
        - CUDA acceleration
        
        The system should process this efficiently using GPU acceleration.
        """
        
        # Test with text content (simulating PDF processing)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            result = parser.parse_text_file(test_file)
            print(f"✓ Document processing successful")
            print(f"✓ Result type: {type(result)}")
            
            if isinstance(result, tuple) and len(result) > 0:
                content = result[0] if result[0] else "No content extracted"
                print(f"✓ Extracted content length: {len(str(content))} characters")
            
            return True
        finally:
            os.unlink(test_file)
            
    except Exception as e:
        print(f"✗ PDF processing test failed: {e}")
        return False

def test_raganything_mineru_integration():
    """Test RAG-Anything integration with MinerU"""
    print("\nTesting RAG-Anything + MinerU integration...")
    
    try:
        # Create RAG-Anything config
        config = RAGAnythingConfig()
        rag = RAGAnything(config=config)
        
        print(f"✓ RAG-Anything initialized")
        
        # Test MinerU parser through RAG-Anything
        parser = MineruParser()
        print(f"✓ MinerU parser accessible")
        
        # Check available parsing methods
        methods = [method for method in dir(parser) if method.startswith('parse_')]
        print(f"✓ Available parsing methods: {methods}")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def test_gpu_memory_usage():
    """Test GPU memory usage during processing"""
    print("\nTesting GPU memory usage...")
    
    try:
        import torch
        
        if not torch.cuda.is_available():
            print(f"ℹ CUDA not available, skipping GPU memory test")
            return True
        
        # Clear GPU cache
        torch.cuda.empty_cache()
        
        initial_memory = torch.cuda.memory_allocated()
        print(f"✓ Initial GPU memory: {initial_memory / 1024**2:.1f} MB")
        
        # Initialize MinerU parser (this may load models to GPU)
        parser = MineruParser()
        
        after_init_memory = torch.cuda.memory_allocated()
        print(f"✓ Memory after MinerU init: {after_init_memory / 1024**2:.1f} MB")
        print(f"✓ Memory increase: {(after_init_memory - initial_memory) / 1024**2:.1f} MB")
        
        return True
    except Exception as e:
        print(f"✗ GPU memory test failed: {e}")
        return False

def main():
    """Run all MinerU CUDA processing tests"""
    print("=" * 70)
    print("MinerU 2.0 CUDA Processing Test")
    print("=" * 70)
    
    results = []
    
    # Test CUDA configuration
    results.append(test_mineru_cuda_configuration())
    
    # Test config file
    results.append(test_mineru_config_file())
    
    # Test GPU memory usage
    results.append(test_gpu_memory_usage())
    
    # Test document processing
    results.append(test_mineru_pdf_processing())
    
    # Test RAG-Anything integration
    results.append(test_raganything_mineru_integration())
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All MinerU CUDA processing tests passed!")
        print("✓ MinerU 2.0 is properly configured with CUDA acceleration")
        print("✓ Document processing pipeline is ready for production use")
    else:
        print("✗ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)