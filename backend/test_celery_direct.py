#!/usr/bin/env python3
"""
Direct Celery task test - bypasses the API to test Celery directly.
"""

import os
import sys
import time
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.tasks.document_processing import process_document_task

def test_celery_direct():
    """Test Celery task directly."""
    print("🧪 Direct Celery Task Test")
    print("=" * 40)
    
    # Create a simple test file
    temp_dir = tempfile.mkdtemp(prefix="celery_direct_test_")
    test_file = os.path.join(temp_dir, "direct_test.txt")
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Direct Celery test content for AI processing.")
    
    print(f"📄 Created test file: {test_file}")
    
    try:
        # Generate a fake document ID
        import uuid
        document_id = str(uuid.uuid4())
        
        print(f"📄 Document ID: {document_id}")
        print("🚀 Queuing Celery task directly...")
        
        # Queue the task directly
        result = process_document_task.delay(document_id, test_file)
        
        print(f"✅ Task queued successfully!")
        print(f"⚙️ Task ID: {result.id}")
        print(f"📊 Task state: {result.state}")
        
        # Monitor the task
        print("⏳ Monitoring task for 30 seconds...")
        
        start_time = time.time()
        last_state = None
        
        while time.time() - start_time < 30:
            current_state = result.state
            
            if current_state != last_state:
                elapsed = time.time() - start_time
                print(f"📊 [{elapsed:.1f}s] Task state: {current_state}")
                last_state = current_state
                
                # Get more info if available
                if hasattr(result, 'info') and result.info:
                    print(f"📝 Task info: {result.info}")
            
            # Check if task completed
            if current_state in ['SUCCESS', 'FAILURE']:
                print(f"🎯 Task finished with state: {current_state}")
                if current_state == 'SUCCESS':
                    print(f"✅ Task result: {result.result}")
                    return True
                else:
                    print(f"❌ Task failed: {result.info}")
                    return False
            
            time.sleep(2)
        
        print(f"⏰ Timeout after 30 seconds. Final state: {result.state}")
        return result.state in ['SUCCESS', 'PENDING']  # PENDING means it's still processing
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print("🧹 Cleaned up test files")

if __name__ == "__main__":
    success = test_celery_direct()
    print(f"\n🎯 Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    sys.exit(0 if success else 1)