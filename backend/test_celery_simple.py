#!/usr/bin/env python3
"""
Simple Celery test with a basic task.
"""

import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.celery_app import celery_app

# Define a simple test task
@celery_app.task
def simple_test_task(message: str):
    """Simple test task."""
    print(f"Processing message: {message}")
    time.sleep(2)  # Simulate some work
    return f"Processed: {message}"

def test_simple_celery():
    """Test Celery with a simple task."""
    print("🧪 Simple Celery Test")
    print("=" * 30)
    
    try:
        print("🚀 Queuing simple task...")
        result = simple_test_task.delay("Hello from Celery!")
        
        print(f"✅ Task queued successfully!")
        print(f"⚙️ Task ID: {result.id}")
        print(f"📊 Initial state: {result.state}")
        
        # Monitor the task
        print("⏳ Monitoring task for 15 seconds...")
        
        start_time = time.time()
        last_state = None
        
        while time.time() - start_time < 15:
            current_state = result.state
            
            if current_state != last_state:
                elapsed = time.time() - start_time
                print(f"📊 [{elapsed:.1f}s] Task state: {current_state}")
                last_state = current_state
                
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
            
            time.sleep(1)
        
        print(f"⏰ Timeout after 15 seconds. Final state: {result.state}")
        return result.state == 'SUCCESS'
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_celery()
    print(f"\n🎯 Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    sys.exit(0 if success else 1)