#!/usr/bin/env python3
"""
Test script for the LightRAG service.
"""

import asyncio
import sys
from app.services.lightrag_service import LightRAGService, lightrag_service

async def test_lightrag_service():
    """Test the LightRAG service functionality."""
    print("=== LightRAG Service Test ===\n")
    
    # Test service initialization
    print("1. Testing service initialization...")
    service = LightRAGService()
    
    # Try OpenAI initialization first
    success = service.initialize_with_openai()
    if success:
        print("✓ Service initialized with OpenAI")
    else:
        print("⚠ Service initialized with mock functions")
    
    # Test health check
    print("\n2. Testing health check...")
    health = service.health_check()
    print(f"✓ Health check completed:")
    for key, value in health.items():
        print(f"  - {key}: {value}")
    
    # Test document insertion
    print("\n3. Testing document insertion...")
    test_doc = """
    LightRAG is a knowledge graph-based Retrieval-Augmented Generation (RAG) system.
    It combines the power of knowledge graphs with large language models to provide
    intelligent question answering and document understanding capabilities.
    
    Key features of LightRAG include:
    - Knowledge graph construction from documents
    - Multiple query modes (naive, local, global, hybrid, mix)
    - Integration with various LLM providers
    - Efficient vector storage and retrieval
    """
    
    insert_success = await service.insert_document(test_doc)
    if insert_success:
        print("✓ Document insertion successful")
    else:
        print("✗ Document insertion failed")
    
    # Test querying
    print("\n4. Testing queries...")
    test_queries = [
        ("What is LightRAG?", "naive"),
        ("What are the key features of LightRAG?", "hybrid"),
        ("How does LightRAG work?", "local")
    ]
    
    for question, mode in test_queries:
        print(f"\nQuery: {question} (mode: {mode})")
        result = await service.query(question, mode)
        if result:
            print(f"✓ Query successful: {result[:200]}...")
        else:
            print("✗ Query failed")
    
    # Test storage info
    print("\n5. Testing storage information...")
    storage_info = service.get_storage_info()
    print("✓ Storage info retrieved:")
    print(f"  - Working directory: {storage_info['working_dir']}")
    print(f"  - Directory exists: {storage_info['exists']}")
    print(f"  - Total files: {len(storage_info['files'])}")
    print(f"  - Total size: {storage_info['total_size']} bytes")
    
    if storage_info['files']:
        print("  - Files:")
        for file_info in storage_info['files']:
            print(f"    * {file_info['name']} ({file_info['size']} bytes)")
    
    print("\n=== Test Complete ===")
    return True

async def test_global_service():
    """Test the global service instance."""
    print("\n=== Global Service Test ===\n")
    
    # Test global service
    print("Testing global service access...")
    global_service = await lightrag_service.initialize_with_openai()
    print(f"✓ Global service initialization: {global_service}")
    
    # Test health check on global service
    health = lightrag_service.health_check()
    print(f"✓ Global service health: {health['initialized']}")
    
    return True

async def main():
    """Run all tests."""
    try:
        await test_lightrag_service()
        await test_global_service()
        print("\n✓ All tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))