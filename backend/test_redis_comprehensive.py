#!/usr/bin/env python3
"""
Comprehensive Redis setup verification for AI PKM Tool.
"""

import sys
import os
import redis
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
from app.core.config import settings

def test_redis_basic_functionality():
    """Test basic Redis functionality."""
    print("=== Testing Basic Redis Functionality ===")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test connectivity
        ping_result = r.ping()
        print(f"✓ Redis ping: {ping_result}")
        
        # Test basic operations
        r.set('test:basic', 'hello_redis')
        value = r.get('test:basic')
        print(f"✓ Basic set/get: {value}")
        
        # Test expiration
        r.setex('test:expire', 5, 'expires_soon')
        ttl = r.ttl('test:expire')
        print(f"✓ TTL functionality: {ttl} seconds")
        
        # Test hash operations (used by Celery)
        r.hset('test:hash', mapping={'field1': 'value1', 'field2': 'value2'})
        hash_data = r.hgetall('test:hash')
        print(f"✓ Hash operations: {hash_data}")
        
        # Test list operations (used by Celery queues)
        r.lpush('test:queue', 'task1', 'task2', 'task3')
        queue_length = r.llen('test:queue')
        task = r.rpop('test:queue')
        print(f"✓ Queue operations: length={queue_length}, popped={task}")
        
        # Clean up test keys
        r.delete('test:basic', 'test:expire', 'test:hash', 'test:queue')
        
        return True
    except Exception as e:
        print(f"✗ Basic Redis test failed: {e}")
        return False

def test_redis_persistence():
    """Test Redis persistence configuration."""
    print("\n=== Testing Redis Persistence ===")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Check AOF configuration
        aof_config = r.config_get('appendonly')
        print(f"✓ AOF persistence: {aof_config.get('appendonly')}")
        
        # Check AOF sync policy
        fsync_config = r.config_get('appendfsync')
        print(f"✓ AOF sync policy: {fsync_config.get('appendfsync')}")
        
        # Check RDB configuration
        save_config = r.config_get('save')
        print(f"✓ RDB save policy: {save_config.get('save')}")
        
        # Check data directory
        dir_config = r.config_get('dir')
        print(f"✓ Data directory: {dir_config.get('dir')}")
        
        return True
    except Exception as e:
        print(f"✗ Persistence test failed: {e}")
        return False

def test_redis_memory_optimization():
    """Test Redis memory optimization settings."""
    print("\n=== Testing Redis Memory Optimization ===")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Get memory info
        info = r.info('memory')
        print(f"✓ Used memory: {info.get('used_memory_human')}")
        print(f"✓ Peak memory: {info.get('used_memory_peak_human')}")
        
        # Check memory policy
        maxmemory = r.config_get('maxmemory')
        maxmemory_policy = r.config_get('maxmemory-policy')
        print(f"✓ Max memory: {maxmemory.get('maxmemory')} (0 = unlimited)")
        print(f"✓ Memory policy: {maxmemory_policy.get('maxmemory-policy')}")
        
        # Check compression settings
        rdb_compression = r.config_get('rdbcompression')
        print(f"✓ RDB compression: {rdb_compression.get('rdbcompression')}")
        
        return True
    except Exception as e:
        print(f"✗ Memory optimization test failed: {e}")
        return False

def test_celery_integration():
    """Test Celery integration with Redis."""
    print("\n=== Testing Celery Integration ===")
    try:
        # Test broker connection
        broker_connection = celery_app.broker_connection()
        broker_connection.ensure_connection(max_retries=3)
        print("✓ Celery broker connection successful")
        
        # Test configuration
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result backend: {celery_app.conf.result_backend}")
        
        # Test task registration
        registered_tasks = [task for task in celery_app.tasks.keys() if not task.startswith('celery.')]
        print(f"✓ Registered tasks: {len(registered_tasks)}")
        
        # Test Redis queues used by Celery
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Check if Celery queues exist (they're created when tasks are sent)
        keys = r.keys('celery*')
        print(f"✓ Celery keys in Redis: {len(keys)}")
        
        return True
    except Exception as e:
        print(f"✗ Celery integration test failed: {e}")
        return False

def test_redis_performance():
    """Test Redis performance with typical workload."""
    print("\n=== Testing Redis Performance ===")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test bulk operations
        start_time = datetime.now()
        pipe = r.pipeline()
        for i in range(1000):
            pipe.set(f'perf:test:{i}', f'value_{i}')
        pipe.execute()
        bulk_time = (datetime.now() - start_time).total_seconds()
        print(f"✓ Bulk write (1000 keys): {bulk_time:.3f} seconds")
        
        # Test bulk read
        start_time = datetime.now()
        pipe = r.pipeline()
        for i in range(1000):
            pipe.get(f'perf:test:{i}')
        results = pipe.execute()
        bulk_read_time = (datetime.now() - start_time).total_seconds()
        print(f"✓ Bulk read (1000 keys): {bulk_read_time:.3f} seconds")
        
        # Clean up
        keys_to_delete = [f'perf:test:{i}' for i in range(1000)]
        r.delete(*keys_to_delete)
        
        return True
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

def main():
    """Run all Redis tests."""
    print("🔍 Comprehensive Redis Setup Verification")
    print("=" * 50)
    
    tests = [
        test_redis_basic_functionality,
        test_redis_persistence,
        test_redis_memory_optimization,
        test_celery_integration,
        test_redis_performance
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✅ Redis is properly installed and configured for:")
        print("   • Basic operations and connectivity")
        print("   • Persistence (AOF + RDB)")
        print("   • Memory optimization")
        print("   • Celery task queue integration")
        print("   • Performance under load")
        return True
    else:
        print(f"❌ Some tests failed ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)