#!/usr/bin/env python3
"""
Test MinerU 2.0 integration and functionality.
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.config import settings
from app.services.document_processor import document_processor


def test_mineru_import():
    """Test MinerU import and basic functionality."""
    print("Testing MinerU import...")
    
    try:
        import mineru
        print(f"✓ MinerU imported successfully")
        
        # Try to access MinerU components
        from mineru.core import PDFProcessor
        print(f"✓ MinerU PDFProcessor imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ MinerU import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ MinerU component access failed: {e}")
        return False


def test_mineru_device_detection():
    """Test MinerU device detection (CPU/CUDA)."""
    print("\nTesting MinerU device detection...")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"CUDA available: {cuda_available}")
        
        if cuda_available:
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"Current CUDA device: {torch.cuda.current_device()}")
        
        # Test configured device
        configured_device = settings.MINERU_DEVICE
        print(f"Configured MinerU device: {configured_device}")
        
        if configured_device == "cuda" and not cuda_available:
            print("⚠ Warning: CUDA configured but not available, falling back to CPU")
            return "cpu"
        
        return configured_device
        
    except ImportError:
        print("PyTorch not available, using CPU")
        return "cpu"
    except Exception as e:
        print(f"Device detection error: {e}")
        return "cpu"


def create_test_pdf():
    """Create a simple test PDF for processing."""
    print("\nCreating test PDF...")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Create PDF content
        c = canvas.Canvas(temp_path, pagesize=letter)
        c.drawString(100, 750, "Test Document for MinerU Processing")
        c.drawString(100, 700, "This is a test PDF document created for testing MinerU 2.0 integration.")
        c.drawString(100, 650, "It contains simple text content that should be extracted successfully.")
        c.drawString(100, 600, "Key features to test:")
        c.drawString(120, 580, "• Text extraction")
        c.drawString(120, 560, "• Document structure parsing")
        c.drawString(120, 540, "• Metadata extraction")
        c.save()
        
        print(f"✓ Test PDF created: {temp_path}")
        return temp_path
        
    except ImportError:
        print("✗ ReportLab not available, cannot create test PDF")
        return None
    except Exception as e:
        print(f"✗ Failed to create test PDF: {e}")
        return None


def test_mineru_pdf_processing(pdf_path):
    """Test MinerU PDF processing functionality."""
    print(f"\nTesting MinerU PDF processing with: {pdf_path}")
    
    try:
        import mineru
        from mineru.core import PDFProcessor
        
        # Initialize PDF processor with configuration
        processor = PDFProcessor(
            device=settings.MINERU_DEVICE,
            backend=settings.MINERU_BACKEND,
            lang=settings.MINERU_LANG
        )
        
        # Process the PDF
        result = processor.process(pdf_path)
        
        if result and result.get('text'):
            print(f"✓ PDF processing successful")
            print(f"  Extracted text length: {len(result['text'])} characters")
            print(f"  Text preview: {result['text'][:200]}...")
            
            if result.get('images'):
                print(f"  Images found: {len(result['images'])}")
            
            if result.get('tables'):
                print(f"  Tables found: {len(result['tables'])}")
            
            return True
        else:
            print("✗ PDF processing failed - no text extracted")
            return False
            
    except Exception as e:
        print(f"✗ MinerU PDF processing failed: {e}")
        return False


async def test_document_processor_integration():
    """Test document processor integration with MinerU."""
    print("\nTesting document processor integration...")
    
    try:
        # Create a test document
        test_pdf = create_test_pdf()
        if not test_pdf:
            print("✗ Cannot test without test PDF")
            return False
        
        # Test document processing
        result = await document_processor.process_document(
            file_path=test_pdf,
            document_id="test_mineru_integration"
        )
        
        if result and result.get('success'):
            print("✓ Document processor integration successful")
            print(f"  Document ID: {result.get('document_id')}")
            print(f"  File type: {result.get('file_type')}")
            print(f"  Extracted text length: {len(result.get('extracted_text', ''))}")
            
            if result.get('extracted_text'):
                print(f"  Text preview: {result['extracted_text'][:200]}...")
            
            return True
        else:
            print(f"✗ Document processor integration failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Document processor integration test failed: {e}")
        return False
    finally:
        # Clean up test file
        if 'test_pdf' in locals() and test_pdf and os.path.exists(test_pdf):
            os.unlink(test_pdf)


def test_mineru_configuration():
    """Test MinerU configuration settings."""
    print("\nTesting MinerU configuration...")
    
    config_tests = [
        ("MINERU_DEVICE", settings.MINERU_DEVICE, ["cpu", "cuda"]),
        ("MINERU_BACKEND", settings.MINERU_BACKEND, ["pipeline", "api"]),
        ("MINERU_LANG", settings.MINERU_LANG, ["en", "zh", "auto"])
    ]
    
    all_passed = True
    
    for setting_name, setting_value, valid_values in config_tests:
        if setting_value in valid_values:
            print(f"✓ {setting_name}: {setting_value}")
        else:
            print(f"⚠ {setting_name}: {setting_value} (not in recommended values: {valid_values})")
            all_passed = False
    
    return all_passed


async def main():
    """Run all MinerU integration tests."""
    print("=" * 60)
    print("MinerU 2.0 Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("MinerU Import", test_mineru_import),
        ("Device Detection", test_mineru_device_detection),
        ("Configuration", test_mineru_configuration),
        ("Document Processor Integration", test_document_processor_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results[test_name] = result
            
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All MinerU integration tests passed!")
        return True
    else:
        print("❌ Some MinerU integration tests failed")
        return False


if __name__ == "__main__":
    asyncio.run(main())