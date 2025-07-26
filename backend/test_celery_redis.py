#!/usr/bin/env python3
"""
Comprehensive test script to verify Celery and Redis integration.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
import redis

def test_redis_connection():
    """Test Redis connection."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis connection successful")
        
        # Test basic Redis operations
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        if value == b'test_value':
            print("✓ Redis read/write operations working")
        r.delete('test_key')
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

def test_celery_broker_connection():
    """Test Celery broker connection."""
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=3)
        print("✓ Celery broker connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Celery broker connection failed: {e}")
        return False

def test_celery_worker_status():
    """Test if Celery workers are active."""
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✓ Found {len(active_workers)} active Celery worker(s)")
            for worker_name in active_workers.keys():
                print(f"  - Worker: {worker_name}")
            return True
        else:
            print("✗ No active Celery workers found")
            return False
    except Exception as e:
        print(f"✗ Failed to check worker status: {e}")
        return False

def test_task_routing():
    """Test task routing configuration."""
    try:
        routes = celery_app.conf.task_routes
        print(f"✓ Task routing configured with {len(routes)} routes:")
        for pattern, config in routes.items():
            print(f"  - {pattern} -> {config}")
        return True
    except Exception as e:
        print(f"✗ Task routing test failed: {e}")
        return False

def test_registered_tasks():
    """Test registered tasks."""
    try:
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✓ Found {len(registered_tasks)} registered tasks:")
        for task in sorted(registered_tasks):
            if not task.startswith('celery.'):
                print(f"  - {task}")
        return True
    except Exception as e:
        print(f"✗ Failed to list registered tasks: {e}")
        return False

def test_queue_inspection():
    """Test queue inspection."""
    try:
        inspect = celery_app.control.inspect()
        
        # Check reserved tasks
        reserved = inspect.reserved()
        if reserved:
            print("✓ Queue inspection working - reserved tasks found")
        else:
            print("✓ Queue inspection working - no reserved tasks")
        
        # Check scheduled tasks
        scheduled = inspect.scheduled()
        if scheduled:
            print("✓ Scheduled tasks inspection working")
        else:
            print("✓ No scheduled tasks found")
            
        return True
    except Exception as e:
        print(f"✗ Queue inspection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Celery and Redis integration...\n")
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Celery Broker Connection", test_celery_broker_connection),
        ("Celery Worker Status", test_celery_worker_status),
        ("Task Routing Configuration", test_task_routing),
        ("Registered Tasks", test_registered_tasks),
        ("Queue Inspection", test_queue_inspection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✓ All tests passed! Celery and Redis are properly configured and working.")
        return 0
    else:
        print("✗ Some tests failed. Check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())