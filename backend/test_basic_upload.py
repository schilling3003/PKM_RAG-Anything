#!/usr/bin/env python3
"""
Basic document upload test - focuses on upload functionality without heavy processing.
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_upload():
    """Test basic document upload functionality."""
    base_url = "http://localhost:8000"
    api_base = f"{base_url}/api/v1"
    
    # Check if backend is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Backend is not running or not healthy")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to backend: {e}")
        return False
    
    logger.info("✅ Backend is running")
    
    # Create a simple test file
    temp_dir = tempfile.mkdtemp(prefix="pkm_basic_test_")
    test_file = os.path.join(temp_dir, "simple_test.txt")
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("This is a simple test document for basic upload functionality.")
    
    logger.info(f"📁 Created test file: {test_file}")
    
    try:
        # Test upload
        logger.info("📤 Testing document upload...")
        
        with open(test_file, 'rb') as f:
            files = {'file': ('simple_test.txt', f, 'text/plain')}
            response = requests.post(f"{api_base}/documents/upload", files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            document_id = data.get("document_id")
            task_id = data.get("task_id")
            
            logger.info(f"✅ Upload successful!")
            logger.info(f"📄 Document ID: {document_id}")
            logger.info(f"⚙️ Task ID: {task_id}")
            
            # Test document retrieval
            logger.info("📋 Testing document retrieval...")
            
            response = requests.get(f"{api_base}/documents/{document_id}", timeout=10)
            
            if response.status_code == 200:
                doc_data = response.json()
                logger.info(f"✅ Document retrieved successfully")
                logger.info(f"📝 Filename: {doc_data.get('filename')}")
                logger.info(f"📊 Status: {doc_data.get('processing_status')}")
                logger.info(f"💾 File size: {doc_data.get('file_size')} bytes")
                
                # Test status endpoint
                logger.info("📊 Testing status endpoint...")
                
                response = requests.get(f"{api_base}/documents/{document_id}/status", timeout=10)
                
                if response.status_code == 200:
                    status_data = response.json()
                    logger.info(f"✅ Status retrieved successfully")
                    logger.info(f"📊 Processing status: {status_data.get('status')}")
                    logger.info(f"📈 Progress: {status_data.get('progress', 0)}%")
                    
                    return True
                else:
                    logger.error(f"❌ Status retrieval failed: HTTP {response.status_code}")
                    return False
            else:
                logger.error(f"❌ Document retrieval failed: HTTP {response.status_code}")
                return False
        else:
            logger.error(f"❌ Upload failed: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        logger.info(f"🧹 Cleaned up test directory")

def test_service_health():
    """Test all service health endpoints."""
    base_url = "http://localhost:8000"
    api_base = f"{base_url}/api/v1"
    
    health_checks = {
        "redis": f"{api_base}/health/redis",
        "celery": f"{api_base}/health/celery", 
        "lightrag": f"{api_base}/health/lightrag",
        "raganything": f"{api_base}/health/raganything",
        "openai": f"{api_base}/health/openai",
        "storage": f"{api_base}/health/storage"
    }
    
    logger.info("🔍 Testing service health...")
    
    all_healthy = True
    
    for service, url in health_checks.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                logger.info(f"✅ {service.upper()}: {status}")
            else:
                logger.error(f"❌ {service.upper()}: HTTP {response.status_code}")
                all_healthy = False
                
        except Exception as e:
            logger.error(f"❌ {service.upper()}: {e}")
            all_healthy = False
    
    return all_healthy

def main():
    """Main test execution."""
    logger.info("🧪 AI PKM Tool - Basic Upload Test")
    logger.info("=" * 50)
    
    # Test service health
    logger.info("\n📋 TESTING SERVICE HEALTH")
    logger.info("-" * 30)
    health_ok = test_service_health()
    
    if not health_ok:
        logger.warning("⚠️ Some services are not healthy, but continuing with upload test...")
    
    # Test basic upload
    logger.info("\n📤 TESTING BASIC UPLOAD")
    logger.info("-" * 30)
    upload_ok = test_basic_upload()
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("-" * 30)
    logger.info(f"Service Health: {'✅ PASS' if health_ok else '⚠️ PARTIAL'}")
    logger.info(f"Basic Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    
    overall_success = upload_ok  # Upload is the critical test
    logger.info(f"\n🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)