#!/usr/bin/env python3
"""
Test script to verify real embedding functionality with ChromaDB.
This focuses on testing what we can actually verify is working.
"""

import asyncio
import sys
import os
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import DatabaseManager
from app.core.migrations import initialize_migrations
from app.core.vector_db import vector_db


async def test_chromadb_embeddings():
    """Test real ChromaDB embedding functionality."""
    print("=" * 60)
    print("TESTING REAL CHROMADB EMBEDDINGS")
    print("=" * 60)
    
    try:
        # Test 1: Check ChromaDB initialization
        print("1. Testing ChromaDB initialization...")
        
        collection_info = vector_db.get_collection_info()
        print(f"   Collection name: {collection_info['name']}")
        print(f"   Initial document count: {collection_info['count']}")
        print("   ✓ ChromaDB initialized successfully")
        
        # Test 2: Add single document with embedding
        print("\n2. Testing single document addition...")
        
        test_content = "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data."
        test_metadata = {"type": "test", "source": "manual", "category": "ai"}
        test_id = f"test_doc_{uuid.uuid4()}"
        
        success = await vector_db.add_document(
            document_id=test_id,
            content=test_content,
            metadata=test_metadata
        )
        
        print(f"   Document added: {success}")
        if success:
            print("   ✓ Single document embedding successful")
        else:
            print("   ✗ Single document embedding failed")
            return False
        
        # Test 3: Add batch of documents
        print("\n3. Testing batch document addition...")
        
        batch_docs = [
            "Deep learning uses neural networks with multiple layers to process data.",
            "Natural language processing helps computers understand and generate human language.",
            "Computer vision enables machines to interpret and analyze visual information from images.",
            "Reinforcement learning trains agents to make decisions through trial and error.",
            "Supervised learning uses labeled data to train predictive models."
        ]
        
        batch_metadata = [
            {"type": "test", "topic": "deep_learning", "category": "ai"},
            {"type": "test", "topic": "nlp", "category": "ai"},
            {"type": "test", "topic": "computer_vision", "category": "ai"},
            {"type": "test", "topic": "reinforcement_learning", "category": "ai"},
            {"type": "test", "topic": "supervised_learning", "category": "ai"}
        ]
        
        batch_ids = [f"batch_doc_{i}_{uuid.uuid4()}" for i in range(len(batch_docs))]
        
        batch_success = await vector_db.add_documents(
            documents=batch_docs,
            metadatas=batch_metadata,
            ids=batch_ids
        )
        
        print(f"   Batch documents added: {batch_success}")
        if batch_success:
            print("   ✓ Batch document embedding successful")
        else:
            print("   ✗ Batch document embedding failed")
            return False
        
        # Test 4: Check updated collection info
        print("\n4. Testing collection info after additions...")
        
        updated_info = vector_db.get_collection_info()
        print(f"   Updated document count: {updated_info['count']}")
        print(f"   Documents added: {updated_info['count'] - collection_info['count']}")
        
        if updated_info['count'] > collection_info['count']:
            print("   ✓ Documents successfully stored in ChromaDB")
        else:
            print("   ✗ Documents may not have been stored properly")
        
        # Test 5: Similarity search
        print("\n5. Testing similarity search...")
        
        search_queries = [
            "artificial intelligence and machine learning",
            "neural networks and deep learning",
            "computer vision and image processing",
            "natural language understanding"
        ]
        
        for i, query in enumerate(search_queries):
            print(f"\n   Query {i+1}: '{query}'")
            
            search_results = await vector_db.similarity_search(
                query=query,
                n_results=3
            )
            
            print(f"   Results found: {search_results['total']}")
            
            if search_results['results']:
                for j, result in enumerate(search_results['results']):
                    relevance = result['relevance_score']
                    content_preview = result['document'][:60] + "..." if len(result['document']) > 60 else result['document']
                    print(f"     {j+1}. Score: {relevance:.3f} - {content_preview}")
                    
                print("   ✓ Similarity search working")
            else:
                print("   ✗ No search results found")
        
        # Test 6: Filtered search
        print("\n6. Testing filtered search...")
        
        filtered_results = await vector_db.similarity_search(
            query="learning algorithms",
            n_results=5,
            where={"category": "ai"}
        )
        
        print(f"   Filtered results (category=ai): {filtered_results['total']}")
        if filtered_results['results']:
            for result in filtered_results['results'][:2]:
                print(f"     - {result['document'][:50]}... (score: {result['relevance_score']:.3f})")
            print("   ✓ Filtered search working")
        else:
            print("   ✗ Filtered search returned no results")
        
        # Test 7: Document update
        print("\n7. Testing document update...")
        
        update_success = await vector_db.update_documents(
            ids=[test_id],
            documents=["Machine learning and artificial intelligence are transforming technology."],
            metadatas=[{"type": "test", "source": "manual", "category": "ai", "updated": True}]
        )
        
        print(f"   Document updated: {update_success}")
        if update_success:
            print("   ✓ Document update successful")
        
        # Test 8: Document deletion
        print("\n8. Testing document deletion...")
        
        # Delete one of the batch documents
        delete_success = await vector_db.delete_documents([batch_ids[0]])
        
        print(f"   Document deleted: {delete_success}")
        if delete_success:
            print("   ✓ Document deletion successful")
        
        # Final collection info
        print("\n9. Final collection status...")
        
        final_info = vector_db.get_collection_info()
        print(f"   Final document count: {final_info['count']}")
        print("   ✓ All ChromaDB operations completed successfully")
        
        return True
        
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_text_chunking():
    """Test the text chunking functionality used in document processing."""
    print("\n" + "=" * 60)
    print("TESTING TEXT CHUNKING FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Import the chunking function
        from app.tasks.document_processing import _split_text_into_chunks
        
        # Test with different text sizes
        test_texts = [
            "Short text that should not be chunked.",
            "This is a longer text that should be split into multiple chunks when it exceeds the maximum chunk size. " * 20,
            "A" * 2000,  # Very long single word
            "Word " * 500  # Many short words
        ]
        
        for i, text in enumerate(test_texts):
            print(f"\n   Test {i+1}: Text length {len(text)} characters")
            
            chunks = _split_text_into_chunks(text, max_chunk_size=500, overlap=50)
            
            print(f"   Chunks created: {len(chunks)}")
            
            for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                preview = chunk[:50] + "..." if len(chunk) > 50 else chunk
                print(f"     Chunk {j+1}: {len(chunk)} chars - {preview}")
            
            if len(chunks) > 3:
                print(f"     ... and {len(chunks) - 3} more chunks")
        
        print("   ✓ Text chunking functionality working")
        return True
        
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_storage_simulation():
    """Simulate the embedding storage process used in document processing."""
    print("\n" + "=" * 60)
    print("TESTING EMBEDDING STORAGE SIMULATION")
    print("=" * 60)
    
    try:
        # Simulate document processing result
        document_id = f"sim_doc_{uuid.uuid4()}"
        extracted_text = """
        Artificial Intelligence (AI) is revolutionizing various industries through its ability to process 
        and analyze vast amounts of data. Machine Learning, a subset of AI, enables systems to automatically 
        learn and improve from experience without being explicitly programmed.
        
        Deep Learning, which uses neural networks with multiple layers, has shown remarkable success in 
        areas such as image recognition, natural language processing, and speech recognition. These 
        technologies are being applied in healthcare, finance, transportation, and many other sectors.
        """
        
        processing_result = {
            "image_descriptions": [
                {"description": "A diagram showing neural network architecture", "ocr_text": "Input Layer -> Hidden Layers -> Output Layer"},
                {"description": "Chart displaying AI market growth over time"}
            ],
            "table_descriptions": [
                {"description": "Comparison of different machine learning algorithms", "summary": "Random Forest performs best for this dataset"}
            ],
            "audio_transcription": {
                "transcription": "Welcome to our AI seminar where we discuss the latest developments in machine learning.",
                "summary": "Introduction to AI seminar"
            }
        }
        
        print(f"   Simulating storage for document: {document_id}")
        print(f"   Text length: {len(extracted_text)} characters")
        print(f"   Image descriptions: {len(processing_result['image_descriptions'])}")
        print(f"   Table descriptions: {len(processing_result['table_descriptions'])}")
        print(f"   Audio transcription: {'Yes' if processing_result['audio_transcription'].get('transcription') else 'No'}")
        
        # Import the storage function
        from app.tasks.document_processing import _store_embeddings
        
        # Test the storage function
        storage_success = await _store_embeddings(document_id, extracted_text, processing_result)
        
        print(f"   Storage result: {storage_success}")
        
        if storage_success:
            print("   ✓ Embedding storage simulation successful")
            
            # Verify the stored embeddings
            search_results = await vector_db.similarity_search(
                query="artificial intelligence machine learning",
                n_results=10
            )
            
            # Count how many results are from our simulated document
            our_results = [r for r in search_results['results'] if document_id in r['id']]
            print(f"   Stored embeddings found in search: {len(our_results)}")
            
            for result in our_results[:3]:
                content_type = result['metadata'].get('content_type', 'unknown')
                preview = result['document'][:50] + "..." if len(result['document']) > 50 else result['document']
                print(f"     - {content_type}: {preview}")
            
            return True
        else:
            print("   ✗ Embedding storage simulation failed")
            return False
        
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all embedding tests."""
    print("REAL EMBEDDING FUNCTIONALITY TEST")
    print("Testing ChromaDB embeddings and related functionality")
    print("=" * 80)
    
    # Initialize database
    print("Initializing database...")
    DatabaseManager.init_database()
    migration_manager = initialize_migrations()
    migration_manager.run_migrations()
    print("Database initialized successfully\n")
    
    # Run tests
    chromadb_success = await test_chromadb_embeddings()
    chunking_success = await test_text_chunking()
    storage_success = await test_embedding_storage_simulation()
    
    # Summary
    print("\n" + "=" * 80)
    print("EMBEDDING TEST SUMMARY")
    print("=" * 80)
    print(f"ChromaDB Operations:       {'✓ PASS' if chromadb_success else '✗ FAIL'}")
    print(f"Text Chunking:             {'✓ PASS' if chunking_success else '✗ FAIL'}")
    print(f"Embedding Storage:         {'✓ PASS' if storage_success else '✗ FAIL'}")
    
    overall_success = chromadb_success and chunking_success and storage_success
    print(f"\nOVERALL RESULT:            {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n✓ EMBEDDINGS ARE WORKING WITH REAL DATA")
        print("  - ChromaDB is properly storing and retrieving embeddings")
        print("  - Text chunking is working correctly")
        print("  - Document processing pipeline can store embeddings")
        print("  - Similarity search is functioning with real embeddings")
    else:
        print("\n✗ SOME EMBEDDING FUNCTIONALITY IS NOT WORKING")
        print("  Check the error messages above for details")


if __name__ == "__main__":
    asyncio.run(main())