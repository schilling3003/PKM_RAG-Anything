#!/usr/bin/env python3
"""
Quick processing test - shorter timeout to see if processing starts.
"""

import os
import sys
import time
import tempfile
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_processing_test():
    """Quick test to see if processing starts."""
    base_url = "http://localhost:8000"
    api_base = f"{base_url}/api/v1"
    
    # Create simple test file
    temp_dir = tempfile.mkdtemp(prefix="pkm_quick_test_")
    test_file = os.path.join(temp_dir, "quick_test.txt")
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("This is a quick test for AI processing. Machine learning and artificial intelligence.")
    
    logger.info(f"📄 Created test file: {test_file}")
    
    try:
        # Upload
        logger.info("📤 Uploading document...")
        with open(test_file, 'rb') as f:
            files = {'file': ('quick_test.txt', f, 'text/plain')}
            response = requests.post(f"{api_base}/documents/upload", files=files, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        document_id = data.get("document_id")
        task_id = data.get("task_id")
        
        logger.info(f"✅ Upload successful!")
        logger.info(f"📄 Document ID: {document_id}")
        logger.info(f"⚙️ Task ID: {task_id}")
        
        # Monitor for 60 seconds to see if processing starts
        logger.info("⏳ Monitoring for 60 seconds...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < 60:
            response = requests.get(f"{api_base}/documents/{document_id}/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data.get("status")
                progress = status_data.get("progress", 0)
                current_step = status_data.get("current_step", "")
                
                if current_status != last_status:
                    elapsed = time.time() - start_time
                    logger.info(f"📊 [{elapsed:.1f}s] Status: {current_status} ({progress}%) - {current_step}")
                    last_status = current_status
                
                # If processing started, that's good enough for now
                if current_status == "processing":
                    logger.info("✅ Processing has started! This confirms the pipeline is working.")
                    return True
                
                # If completed quickly, even better
                if current_status == "completed":
                    logger.info("✅ Processing completed quickly!")
                    return True
                
                # If failed, we need to know
                if current_status == "failed":
                    logger.error(f"❌ Processing failed: {status_data.get('error', 'Unknown error')}")
                    return False
            
            time.sleep(3)
        
        # Check final status
        response = requests.get(f"{api_base}/documents/{document_id}/status", timeout=10)
        if response.status_code == 200:
            final_status = response.json().get("status")
            logger.info(f"📊 Final status after 60s: {final_status}")
            
            if final_status in ["processing", "completed"]:
                logger.info("✅ Processing is working (either in progress or completed)")
                return True
            else:
                logger.warning(f"⚠️ Status is still '{final_status}' - processing may be slow or stuck")
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        logger.info("🧹 Cleaned up test files")

def main():
    logger.info("🧪 Quick Processing Test")
    logger.info("=" * 40)
    
    success = quick_processing_test()
    
    logger.info("\n📊 RESULT")
    logger.info("-" * 20)
    logger.info(f"🎯 Test result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    if success:
        logger.info("✅ The document processing pipeline is working!")
        logger.info("📝 You can now run the full test with longer timeout if needed.")
    else:
        logger.error("❌ The document processing pipeline has issues.")
        logger.error("🔍 Check Celery worker logs for more details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)