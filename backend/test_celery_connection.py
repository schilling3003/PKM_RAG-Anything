#!/usr/bin/env python3
"""
Test script to verify Celery configuration and Redis connection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
import redis

def test_redis_connection():
    """Test Redis connection."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis connection successful")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

def test_celery_config():
    """Test Celery configuration."""
    try:
        print(f"✓ Celery app created: {celery_app.main}")
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result backend: {celery_app.conf.result_backend}")
        print(f"✓ Task routes configured: {len(celery_app.conf.task_routes)} routes")
        return True
    except Exception as e:
        print(f"✗ Celery configuration error: {e}")
        return False

def test_celery_broker_connection():
    """Test Celery broker connection."""
    try:
        # Try to get broker connection info
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=3)
        print("✓ Celery broker connection successful")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Celery broker connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Celery configuration and connections...\n")
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Celery Configuration", test_celery_config),
        ("Celery Broker Connection", test_celery_broker_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    if all(results):
        print("✓ All tests passed! Celery is properly configured.")
        return 0
    else:
        print("✗ Some tests failed. Check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())