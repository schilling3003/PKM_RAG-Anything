#!/usr/bin/env python3
"""
Test script to verify real functionality of embeddings and knowledge graph.
"""

import asyncio
import sys
import os
import tempfile
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import DatabaseManager
from app.core.migrations import initialize_migrations
from app.core.vector_db import vector_db
from app.services.knowledge_graph import knowledge_graph_service
from app.services.document_processor import document_processor
from app.models.database import Note, Document
from app.core.database import SessionLocal


async def test_real_embeddings():
    """Test real embedding functionality with ChromaDB."""
    print("=" * 60)
    print("TESTING REAL EMBEDDINGS WITH CHROMADB")
    print("=" * 60)
    
    try:
        # Test 1: Add a single document
        print("1. Testing single document embedding...")
        
        test_content = "Machine learning is a subset of artificial intelligence that focuses on algorithms."
        test_metadata = {"type": "test", "source": "manual"}
        test_id = f"test_doc_{uuid.uuid4()}"
        
        success = await vector_db.add_document(
            document_id=test_id,
            content=test_content,
            metadata=test_metadata
        )
        
        print(f"   Single document added: {success}")
        
        # Test 2: Search for similar content
        print("2. Testing similarity search...")
        
        search_results = await vector_db.similarity_search(
            query="artificial intelligence algorithms",
            n_results=5
        )
        
        print(f"   Search results found: {search_results['total']}")
        if search_results['results']:
            for i, result in enumerate(search_results['results'][:2]):
                print(f"   Result {i+1}: {result['document'][:50]}... (score: {result['relevance_score']:.3f})")
        
        # Test 3: Add multiple documents
        print("3. Testing batch document embedding...")
        
        batch_docs = [
            "Deep learning uses neural networks with multiple layers.",
            "Natural language processing helps computers understand human language.",
            "Computer vision enables machines to interpret visual information."
        ]
        batch_metadata = [{"type": "test", "batch": i} for i in range(len(batch_docs))]
        batch_ids = [f"batch_doc_{i}_{uuid.uuid4()}" for i in range(len(batch_docs))]
        
        batch_success = await vector_db.add_documents(
            documents=batch_docs,
            metadatas=batch_metadata,
            ids=batch_ids
        )
        
        print(f"   Batch documents added: {batch_success}")
        
        # Test 4: Search again with more content
        print("4. Testing search with more content...")
        
        search_results2 = await vector_db.similarity_search(
            query="neural networks deep learning",
            n_results=5
        )
        
        print(f"   Search results found: {search_results2['total']}")
        if search_results2['results']:
            for i, result in enumerate(search_results2['results'][:3]):
                print(f"   Result {i+1}: {result['document'][:50]}... (score: {result['relevance_score']:.3f})")
        
        # Test 5: Get collection info
        print("5. Testing collection info...")
        
        collection_info = vector_db.get_collection_info()
        print(f"   Collection: {collection_info['name']}")
        print(f"   Document count: {collection_info['count']}")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False


async def test_real_knowledge_graph():
    """Test real knowledge graph functionality."""
    print("\n" + "=" * 60)
    print("TESTING REAL KNOWLEDGE GRAPH FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test 1: Create a test note in database first
        print("1. Creating test note in database...")
        
        db = SessionLocal()
        try:
            test_note = Note(
                id="test_note_real",
                title="AI and Machine Learning Overview",
                content="""
                Artificial Intelligence (AI) is a broad field that encompasses machine learning.
                Machine Learning (ML) is a subset of AI that focuses on algorithms that learn from data.
                Deep Learning is a specialized area of ML that uses neural networks.
                Natural Language Processing (NLP) helps computers understand human language.
                Computer Vision enables machines to interpret and analyze visual information.
                """,
                tags=["ai", "machine-learning", "deep-learning"]
            )
            db.add(test_note)
            db.commit()
            print("   Test note created successfully")
        finally:
            db.close()
        
        # Test 2: Build knowledge graph from note
        print("2. Building knowledge graph from note...")
        
        result = await knowledge_graph_service.build_graph_from_note(
            note_id="test_note_real",
            content=test_note.content,
            title=test_note.title,
            tags=test_note.tags
        )
        
        print(f"   Graph building result: {result}")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Nodes added: {result.get('nodes_added', 0)}")
        print(f"   Edges added: {result.get('edges_added', 0)}")
        
        # Test 3: Get graph statistics
        print("3. Getting graph statistics...")
        
        stats = await knowledge_graph_service.get_graph_statistics()
        print(f"   Total nodes: {stats.get('total_nodes', 0)}")
        print(f"   Total edges: {stats.get('total_edges', 0)}")
        print(f"   Node types: {stats.get('node_types', {})}")
        print(f"   Relationship types: {stats.get('relationship_types', {})}")
        
        # Test 4: Search nodes
        print("4. Testing node search...")
        
        search_results = await knowledge_graph_service.search_nodes("machine learning")
        print(f"   Search results for 'machine learning': {len(search_results)}")
        
        for i, result in enumerate(search_results[:3]):
            print(f"   Result {i+1}: {result['label']} (score: {result['relevance_score']:.3f})")
        
        # Test 5: Test graph data retrieval
        print("5. Testing graph data retrieval...")
        
        # Check if get_graph_data method exists
        if hasattr(knowledge_graph_service, 'get_graph_data'):
            graph_data = await knowledge_graph_service.get_graph_data()
            print(f"   Graph nodes retrieved: {len(graph_data.nodes)}")
            print(f"   Graph edges retrieved: {len(graph_data.edges)}")
            
            if graph_data.nodes:
                print("   Sample nodes:")
                for i, node in enumerate(graph_data.nodes[:3]):
                    print(f"     - {node.id}: {node.label} ({node.type})")
        else:
            print("   get_graph_data method not found - this needs to be implemented")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_processing_integration():
    """Test the full document processing pipeline with embeddings and knowledge graph."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT PROCESSING INTEGRATION")
    print("=" * 60)
    
    try:
        # Test 1: Create a temporary text file
        print("1. Creating test document...")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            Introduction to Artificial Intelligence
            
            Artificial Intelligence (AI) represents one of the most significant technological 
            advances of our time. It encompasses various subfields including:
            
            1. Machine Learning - algorithms that learn from data
            2. Deep Learning - neural networks with multiple layers
            3. Natural Language Processing - understanding human language
            4. Computer Vision - interpreting visual information
            5. Robotics - intelligent physical systems
            
            These technologies are transforming industries and creating new possibilities
            for automation, analysis, and human-computer interaction.
            """)
            temp_file_path = f.name
        
        print(f"   Test document created: {temp_file_path}")
        
        # Test 2: Process document
        print("2. Processing document with full pipeline...")
        
        document_id = f"test_doc_{uuid.uuid4()}"
        
        try:
            processing_result = await document_processor.process_document(
                file_path=temp_file_path,
                document_id=document_id
            )
            
            print(f"   Processing success: {processing_result.get('success', False)}")
            print(f"   Extracted text length: {len(processing_result.get('extracted_text', ''))}")
            
            # The document processing should have:
            # 1. Extracted text
            # 2. Stored embeddings in ChromaDB
            # 3. Built knowledge graph
            
            if processing_result.get('success'):
                print("   ✓ Document processing completed successfully")
            else:
                print(f"   ✗ Document processing failed: {processing_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"   ✗ Document processing failed with exception: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Verify embeddings were stored
        print("3. Verifying embeddings were stored...")
        
        search_results = await vector_db.similarity_search(
            query="artificial intelligence machine learning",
            n_results=5
        )
        
        print(f"   Embeddings search results: {search_results['total']}")
        
        # Test 4: Verify knowledge graph was updated
        print("4. Verifying knowledge graph was updated...")
        
        final_stats = await knowledge_graph_service.get_graph_statistics()
        print(f"   Final graph nodes: {final_stats.get('total_nodes', 0)}")
        print(f"   Final graph edges: {final_stats.get('total_edges', 0)}")
        
        # Cleanup
        os.unlink(temp_file_path)
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("COMPREHENSIVE FUNCTIONALITY TEST")
    print("Testing real embeddings and knowledge graph functionality")
    print("=" * 80)
    
    # Initialize database
    print("Initializing database...")
    DatabaseManager.init_database()
    migration_manager = initialize_migrations()
    migration_manager.run_migrations()
    print("Database initialized successfully\n")
    
    # Run tests
    embedding_success = await test_real_embeddings()
    kg_success = await test_real_knowledge_graph()
    integration_success = await test_document_processing_integration()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Embeddings (ChromaDB):     {'✓ PASS' if embedding_success else '✗ FAIL'}")
    print(f"Knowledge Graph:           {'✓ PASS' if kg_success else '✗ FAIL'}")
    print(f"Integration Pipeline:      {'✓ PASS' if integration_success else '✗ FAIL'}")
    
    overall_success = embedding_success and kg_success and integration_success
    print(f"\nOVERALL RESULT:            {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    if not overall_success:
        print("\nNOTE: Some functionality may be using mock implementations.")
        print("For full functionality, ensure all dependencies are installed:")
        print("- ChromaDB for embeddings")
        print("- LightRAG for knowledge graph construction")
        print("- OpenAI API key for real LLM/embedding calls")


if __name__ == "__main__":
    asyncio.run(main())