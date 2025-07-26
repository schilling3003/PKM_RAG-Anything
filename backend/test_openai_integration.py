#!/usr/bin/env python3
"""
Test script for OpenAI API integration.
This script tests the OpenAI service configuration, connectivity, and fallback behavior.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.openai_service import OpenAIService, initialize_openai_service
from app.core.config import settings


async def test_openai_service():
    """Test OpenAI service functionality."""
    print("🧪 Testing OpenAI API Integration")
    print("=" * 50)
    
    # Initialize service
    service = OpenAIService()
    
    # Test 1: Configuration without API key
    print("\n1. Testing configuration without API key...")
    configured = service.configure()
    print(f"   Configuration result: {configured}")
    
    health = service.health_check()
    print(f"   Service configured: {health['configured']}")
    print(f"   Service available: {health['available']}")
    
    # Test 2: Configuration with mock API key
    print("\n2. Testing configuration with mock API key...")
    configured = service.configure(api_key="sk-test-mock-key-for-testing")
    print(f"   Configuration result: {configured}")
    
    health = service.health_check()
    print(f"   Service configured: {health['configured']}")
    print(f"   Base URL: {health['base_url']}")
    print(f"   Models: {health['models']}")
    
    # Test 3: Connectivity test (will fail with mock key)
    print("\n3. Testing connectivity (expected to fail with mock key)...")
    test_result = await service.test_connectivity()
    print(f"   Connectivity test: {test_result['connectivity_test']}")
    print(f"   API key configured: {test_result['api_key_configured']}")
    print(f"   Client initialized: {test_result['client_initialized']}")
    if test_result['error']:
        print(f"   Error (expected): {test_result['error'][:100]}...")
    
    # Test 4: Fallback behavior
    print("\n4. Testing fallback behavior...")
    
    # Test chat completion fallback
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    response = await service.chat_completion(messages)
    print(f"   Chat completion fallback: {response[:100]}...")
    
    # Test embeddings fallback
    texts = ["Hello world", "Test embedding"]
    embeddings = await service.create_embeddings(texts)
    if embeddings:
        print(f"   Embeddings fallback: Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
    
    # Test 5: Real API key test (if available)
    print("\n5. Testing with real API key (if available)...")
    real_api_key = os.getenv("OPENAI_API_KEY")
    
    if real_api_key and real_api_key.startswith("sk-"):
        print("   Real API key found, testing connectivity...")
        service.configure(api_key=real_api_key)
        
        test_result = await service.test_connectivity()
        print(f"   Connectivity test: {test_result['connectivity_test']}")
        print(f"   Response time: {test_result.get('response_time', 'N/A')} seconds")
        print(f"   Model access: {test_result['model_access']}")
        print(f"   Embedding access: {test_result['embedding_access']}")
        
        if test_result['connectivity_test']:
            # Test real completion
            response = await service.chat_completion(
                [{"role": "user", "content": "Say 'OpenAI integration working!'"}],
                max_tokens=10
            )
            print(f"   Real completion: {response}")
            
            # Test real embeddings
            embeddings = await service.create_embeddings(["test"])
            if embeddings:
                print(f"   Real embeddings: Generated embedding of dimension {len(embeddings[0])}")
    else:
        print("   No real API key found (set OPENAI_API_KEY environment variable to test)")
        print("   To test with real API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("   python test_openai_integration.py")
    
    # Test 6: Global service initialization
    print("\n6. Testing global service initialization...")
    initialized = await initialize_openai_service()
    print(f"   Global service initialized: {initialized}")
    
    # Final health check
    print("\n7. Final health check...")
    final_health = service.health_check()
    print(f"   Service status: {final_health}")
    
    print("\n✅ OpenAI integration test completed!")
    print("\nNext steps:")
    print("1. Set OPENAI_API_KEY environment variable for full functionality")
    print("2. Test health check endpoints: GET /api/v1/health/openai")
    print("3. Test connectivity endpoint: GET /api/v1/health/openai/test")


if __name__ == "__main__":
    asyncio.run(test_openai_service())