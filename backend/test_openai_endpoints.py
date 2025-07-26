#!/usr/bin/env python3
"""
Test script for OpenAI health check endpoints.
This script tests the OpenAI health check API endpoints.
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def test_openai_endpoints():
    """Test OpenAI health check endpoints."""
    print("🧪 Testing OpenAI Health Check Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Basic health check
        print("\n1. Testing basic health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Service: {data.get('service', 'N/A')}")
                print(f"   Status: {data.get('status', 'N/A')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Connection error: {e}")
            print("   Make sure the FastAPI server is running:")
            print("   cd backend && uvicorn app.main:app --reload")
            return
        
        # Test 2: OpenAI health check
        print("\n2. Testing OpenAI health check endpoint...")
        try:
            response = await client.get(f"{base_url}/monitoring/health/openai")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Service: {data.get('service', 'N/A')}")
                print(f"   Configured: {data.get('configured', False)}")
                print(f"   Available: {data.get('available', False)}")
                print(f"   Models: {data.get('models', {})}")
                print(f"   Fallback enabled: {data.get('fallback_enabled', False)}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Request error: {e}")
        
        # Test 3: OpenAI connectivity test
        print("\n3. Testing OpenAI connectivity test endpoint...")
        try:
            response = await client.get(f"{base_url}/monitoring/health/openai/test")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Connectivity test: {data.get('connectivity_test', False)}")
                print(f"   API key configured: {data.get('api_key_configured', False)}")
                print(f"   Model access: {data.get('model_access', {})}")
                print(f"   Embedding access: {data.get('embedding_access', False)}")
                if data.get('response_time'):
                    print(f"   Response time: {data['response_time']:.3f} seconds")
            elif response.status_code == 503:
                data = response.json()
                print(f"   Service unavailable (expected): {data.get('detail', 'N/A')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Request error: {e}")
        
        # Test 4: System status
        print("\n4. Testing system status endpoint...")
        try:
            response = await client.get(f"{base_url}/monitoring/system/status")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Overall status: {data.get('status', 'N/A')}")
                services = data.get('services', {})
                print(f"   Services: {services}")
                openai_status = data.get('openai_status', {})
                print(f"   OpenAI status: {openai_status}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Request error: {e}")
    
    print("\n✅ OpenAI endpoint testing completed!")
    print("\nTo test with real API key:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Restart the FastAPI server")
    print("3. Run this test again")


if __name__ == "__main__":
    asyncio.run(test_openai_endpoints())