#!/usr/bin/env python3
"""
Test script to verify document processing task execution.
"""

import sys
import os
import tempfile
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.document_processing import process_document_task
from app.core.celery_app import celery_app

def create_test_file():
    """Create a simple test text file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for Celery task processing.\n")
        f.write("It contains some sample text to verify that the document processing pipeline works correctly.\n")
        f.write("The Celery worker should be able to process this file successfully.")
        return f.name

def test_document_processing_task():
    """Test that we can send a document processing task."""
    try:
        # Create a test file
        test_file = create_test_file()
        print(f"✓ Created test file: {test_file}")
        
        # Generate a test document ID
        test_doc_id = "test-doc-123"
        
        # Send the task to Celery
        print("Sending document processing task to Celery worker...")
        result = process_document_task.delay(test_doc_id, test_file)
        print(f"✓ Task sent with ID: {result.id}")
        
        # Wait for result with timeout
        print("Waiting for task completion (timeout: 30 seconds)...")
        try:
            task_result = result.get(timeout=30)
            print(f"✓ Task completed successfully!")
            print(f"Result: {task_result}")
            
            # Clean up test file
            os.unlink(test_file)
            print("✓ Test file cleaned up")
            
            return True
        except Exception as e:
            print(f"✗ Task execution failed or timed out: {e}")
            # Clean up test file even if task failed
            try:
                os.unlink(test_file)
            except:
                pass
            return False
            
    except Exception as e:
        print(f"✗ Failed to send task: {e}")
        return False

def test_celery_task_inspection():
    """Test Celery task inspection capabilities."""
    try:
        inspect = celery_app.control.inspect()
        
        # Check active tasks
        active = inspect.active()
        print(f"✓ Active tasks: {len(active) if active else 0}")
        
        # Check registered tasks
        registered = inspect.registered()
        if registered:
            for worker, tasks in registered.items():
                print(f"✓ Worker {worker} has {len(tasks)} registered tasks")
                # Look for our document processing task
                doc_tasks = [t for t in tasks if 'document_processing' in t]
                if doc_tasks:
                    print(f"  - Document processing tasks: {doc_tasks}")
        
        return True
    except Exception as e:
        print(f"✗ Task inspection failed: {e}")
        return False

def main():
    """Run task tests."""
    print("Testing Celery document processing task...\n")
    
    # First check task inspection
    print("1. Checking task registration...")
    if not test_celery_task_inspection():
        print("Task inspection failed, but continuing with task test...\n")
    else:
        print("Task inspection successful!\n")
    
    # Test actual task execution
    print("2. Testing task execution...")
    success = test_document_processing_task()
    
    if success:
        print("\n✓ Document processing task test passed!")
        print("Celery worker is properly configured and can process tasks.")
        return 0
    else:
        print("\n✗ Document processing task test failed!")
        print("Check Celery worker logs for more details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())