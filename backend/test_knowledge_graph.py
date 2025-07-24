#!/usr/bin/env python3
"""
Test script for knowledge graph functionality.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.knowledge_graph import knowledge_graph_service
from app.core.database import DatabaseManager
from app.core.migrations import initialize_migrations


async def test_knowledge_graph():
    """Test knowledge graph functionality."""
    print("Testing Knowledge Graph Service...")
    
    # Initialize database
    print("1. Initializing database...")
    DatabaseManager.init_database()
    migration_manager = initialize_migrations()
    migration_manager.run_migrations()
    
    # Test building graph from sample content
    print("2. Testing graph construction from sample document...")
    
    sample_content = """
    Artificial Intelligence and Machine Learning
    
    Artificial Intelligence (AI) is a broad field of computer science that aims to create 
    intelligent machines. Machine Learning (ML) is a subset of AI that focuses on algorithms 
    that can learn from data.
    
    Deep Learning is a subset of Machine Learning that uses neural networks with multiple 
    layers. Natural Language Processing (NLP) is another important area of AI that deals 
    with understanding human language.
    
    Computer Vision is an AI field that enables machines to interpret visual information.
    It often uses Deep Learning techniques for image recognition and object detection.
    """
    
    # Build knowledge graph from sample content
    result = await knowledge_graph_service.build_graph_from_document(
        document_id="test_doc_1",
        content=sample_content,
        metadata={"title": "AI Overview", "type": "document"}
    )
    
    print(f"   Graph construction result: {result}")
    
    # Test building graph from a note
    print("3. Testing graph construction from sample note...")
    
    note_content = """
    # My Notes on Neural Networks
    
    Neural networks are inspired by biological neural networks. They consist of 
    interconnected nodes (neurons) that process information. Backpropagation is 
    the key algorithm used to train neural networks.
    
    Convolutional Neural Networks (CNNs) are particularly effective for image 
    processing tasks. They use convolution operations to detect features in images.
    """
    
    result = await knowledge_graph_service.build_graph_from_note(
        note_id="test_note_1",
        content=note_content,
        title="Neural Networks Notes",
        tags=["ai", "neural-networks", "deep-learning"]
    )
    
    print(f"   Note graph construction result: {result}")
    
    # Test graph data retrieval
    print("4. Testing graph data retrieval...")
    
    graph_data = await knowledge_graph_service.get_graph_data()
    print(f"   Total nodes: {len(graph_data.nodes)}")
    print(f"   Total edges: {len(graph_data.edges)}")
    
    if graph_data.nodes:
        print("   Sample nodes:")
        for i, node in enumerate(graph_data.nodes[:3]):
            print(f"     - {node.id}: {node.label} ({node.type})")
    
    if graph_data.edges:
        print("   Sample edges:")
        for i, edge in enumerate(graph_data.edges[:3]):
            print(f"     - {edge.source} -> {edge.target}: {edge.relationship}")
    
    # Test node search
    print("5. Testing node search...")
    
    search_results = await knowledge_graph_service.search_nodes("artificial intelligence")
    print(f"   Search results for 'artificial intelligence': {len(search_results)} matches")
    
    for result in search_results[:3]:
        print(f"     - {result['node_id']}: {result['label']} (score: {result['relevance_score']})")
    
    # Test graph statistics
    print("6. Testing graph statistics...")
    
    stats = await knowledge_graph_service.get_graph_statistics()
    print(f"   Graph statistics: {stats}")
    
    # Test related nodes finding
    if graph_data.nodes:
        print("7. Testing related nodes finding...")
        
        first_node_id = graph_data.nodes[0].id
        related_nodes = await knowledge_graph_service.find_related_nodes(first_node_id, max_depth=2)
        print(f"   Related nodes for '{first_node_id}': {len(related_nodes)} found")
        
        for related in related_nodes[:3]:
            print(f"     - {related['node_id']}: {related['label']} (depth: {related['depth']})")
    
    # Test clustering
    print("8. Testing node clustering...")
    
    clusters = await knowledge_graph_service.get_node_clusters()
    print(f"   Found {len(clusters)} clusters")
    
    for cluster_id, nodes in list(clusters.items())[:3]:
        print(f"     - {cluster_id}: {len(nodes)} nodes")
    
    print("\nKnowledge Graph Service test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_knowledge_graph())