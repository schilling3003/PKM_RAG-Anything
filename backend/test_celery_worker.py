#!/usr/bin/env python3
"""
Test script to verify Celery worker can start and process tasks.
"""

import sys
import os
import time
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app

# Simple test task
@celery_app.task
def test_task(message):
    """Simple test task."""
    return f"Task completed: {message}"

def test_task_execution():
    """Test that we can send and execute a task."""
    try:
        # Send a test task
        result = test_task.delay("Hello from test!")
        print(f"✓ Task sent with ID: {result.id}")
        
        # Wait for result (with timeout)
        try:
            task_result = result.get(timeout=10)
            print(f"✓ Task completed successfully: {task_result}")
            return True
        except Exception as e:
            print(f"✗ Task execution failed or timed out: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to send task: {e}")
        return False

def main():
    """Run task execution test."""
    print("Testing Celery task execution...\n")
    
    print("Note: This test requires a Celery worker to be running.")
    print("Start a worker in another terminal with:")
    print("  celery -A app.core.celery_app worker --loglevel=info\n")
    
    # Check if we can connect to broker
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=3)
        print("✓ Connected to Celery broker")
        conn.close()
    except Exception as e:
        print(f"✗ Cannot connect to Celery broker: {e}")
        return 1
    
    # Test task execution
    success = test_task_execution()
    
    if success:
        print("\n✓ Celery task execution test passed!")
        return 0
    else:
        print("\n✗ Celery task execution test failed!")
        print("Make sure a Celery worker is running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())