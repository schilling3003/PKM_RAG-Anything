"""
Knowledge graph API endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from app.models.schemas import (
    BaseResponse, GraphResponse, GraphData, GraphFilters,
    GraphNode, GraphEdge
)
from app.services.knowledge_graph import knowledge_graph_service
from app.core.exceptions import KnowledgeGraphError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.get("/", response_model=GraphResponse)
async def get_knowledge_graph(
    node_types: Optional[List[str]] = Query(None, description="Filter by node types"),
    relationship_types: Optional[List[str]] = Query(None, description="Filter by relationship types"),
    min_weight: Optional[float] = Query(None, ge=0.0, description="Minimum edge weight"),
    max_nodes: int = Query(100, ge=1, le=1000, description="Maximum number of nodes to return")
):
    """
    Get knowledge graph data for visualization.
    
    Returns filtered graph data based on the provided parameters.
    """
    try:
        # Create filters
        filters = GraphFilters(
            node_types=node_types,
            relationship_types=relationship_types,
            min_weight=min_weight,
            max_nodes=max_nodes
        )
        
        # Get graph data
        graph_data = await knowledge_graph_service.get_graph_data(filters)
        
        return GraphResponse(
            graph=graph_data,
            total_nodes=len(graph_data.nodes),
            total_edges=len(graph_data.edges),
            message="Knowledge graph retrieved successfully"
        )
        
    except KnowledgeGraphError as e:
        logger.error(f"Knowledge graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve knowledge graph")


@router.get("/node/{node_id}")
async def get_node_details(node_id: str):
    """
    Get detailed information about a specific node.
    
    Args:
        node_id: ID of the node to retrieve
        
    Returns:
        Node details with properties and relationships
    """
    try:
        # Load graph if needed
        if knowledge_graph_service.graph.number_of_nodes() == 0:
            await knowledge_graph_service._load_networkx_graph()
        
        # Check if node exists
        if node_id not in knowledge_graph_service.graph:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
        # Get node data
        node_data = knowledge_graph_service.graph.nodes[node_id]
        
        # Get relationships
        relationships = []
        for neighbor in knowledge_graph_service.graph.neighbors(node_id):
            edge_data = knowledge_graph_service.graph.get_edge_data(node_id, neighbor)
            for key, data in edge_data.items():
                relationships.append({
                    "target_node_id": neighbor,
                    "target_label": knowledge_graph_service.graph.nodes[neighbor].get("label", neighbor),
                    "relationship": data.get("relationship", "related"),
                    "weight": data.get("weight", 1.0),
                    "direction": "outgoing"
                })
        
        # Get incoming relationships
        for predecessor in knowledge_graph_service.graph.predecessors(node_id):
            edge_data = knowledge_graph_service.graph.get_edge_data(predecessor, node_id)
            for key, data in edge_data.items():
                relationships.append({
                    "target_node_id": predecessor,
                    "target_label": knowledge_graph_service.graph.nodes[predecessor].get("label", predecessor),
                    "relationship": data.get("relationship", "related"),
                    "weight": data.get("weight", 1.0),
                    "direction": "incoming"
                })
        
        return {
            "success": True,
            "node": {
                "id": node_id,
                "label": node_data.get("label", node_id),
                "type": node_data.get("type", "unknown"),
                "description": node_data.get("description", ""),
                "properties": node_data,
                "relationships": relationships
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node details for {node_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve node details")


@router.get("/node/{node_id}/related")
async def get_related_nodes(
    node_id: str,
    max_depth: int = Query(2, ge=1, le=5, description="Maximum traversal depth"),
    relationship_types: Optional[List[str]] = Query(None, description="Filter by relationship types")
):
    """
    Find nodes related to a specific node.
    
    Args:
        node_id: ID of the starting node
        max_depth: Maximum traversal depth
        relationship_types: Optional filter for relationship types
        
    Returns:
        List of related nodes with relationship paths
    """
    try:
        related_nodes = await knowledge_graph_service.find_related_nodes(
            node_id=node_id,
            max_depth=max_depth,
            relationship_types=relationship_types
        )
        
        return {
            "success": True,
            "node_id": node_id,
            "related_nodes": related_nodes,
            "total_related": len(related_nodes)
        }
        
    except Exception as e:
        logger.error(f"Error finding related nodes for {node_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to find related nodes")


@router.get("/path/{source_id}/{target_id}")
async def get_shortest_path(source_id: str, target_id: str):
    """
    Find shortest path between two nodes.
    
    Args:
        source_id: Starting node ID
        target_id: Target node ID
        
    Returns:
        Shortest path between the nodes
    """
    try:
        path = await knowledge_graph_service.find_shortest_path(source_id, target_id)
        
        if not path:
            return {
                "success": True,
                "source_id": source_id,
                "target_id": target_id,
                "path": [],
                "path_length": 0,
                "message": "No path found between the specified nodes"
            }
        
        return {
            "success": True,
            "source_id": source_id,
            "target_id": target_id,
            "path": path,
            "path_length": len(path)
        }
        
    except Exception as e:
        logger.error(f"Error finding path from {source_id} to {target_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to find shortest path")


@router.get("/clusters")
async def get_node_clusters(
    algorithm: str = Query("louvain", description="Clustering algorithm (louvain, label_propagation)")
):
    """
    Get node clusters/communities in the knowledge graph.
    
    Args:
        algorithm: Clustering algorithm to use
        
    Returns:
        Node clusters with cluster assignments
    """
    try:
        clusters = await knowledge_graph_service.get_node_clusters(algorithm)
        
        # Add cluster statistics
        cluster_stats = {}
        for cluster_id, nodes in clusters.items():
            cluster_stats[cluster_id] = {
                "node_count": len(nodes),
                "nodes": nodes
            }
        
        return {
            "success": True,
            "algorithm": algorithm,
            "clusters": cluster_stats,
            "total_clusters": len(clusters)
        }
        
    except Exception as e:
        logger.error(f"Error getting node clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get node clusters")


@router.get("/centrality")
async def get_node_centrality(
    centrality_type: str = Query("betweenness", description="Centrality type (betweenness, closeness, degree, eigenvector)")
):
    """
    Get node centrality measures.
    
    Args:
        centrality_type: Type of centrality to calculate
        
    Returns:
        Node centrality scores
    """
    try:
        centrality_scores = await knowledge_graph_service.get_node_centrality(centrality_type)
        
        # Sort by centrality score
        sorted_scores = sorted(
            centrality_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "success": True,
            "centrality_type": centrality_type,
            "centrality_scores": dict(sorted_scores),
            "top_nodes": sorted_scores[:10]  # Top 10 most central nodes
        }
        
    except Exception as e:
        logger.error(f"Error calculating {centrality_type} centrality: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate node centrality")


@router.get("/search")
async def search_nodes(
    query: str = Query(..., min_length=1, description="Search query"),
    search_fields: Optional[List[str]] = Query(["label", "description"], description="Fields to search in"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Search for nodes in the knowledge graph.
    
    Args:
        query: Search query
        search_fields: Fields to search in
        limit: Maximum number of results
        
    Returns:
        Matching nodes with relevance scores
    """
    try:
        matching_nodes = await knowledge_graph_service.search_nodes(query, search_fields)
        
        # Limit results
        limited_results = matching_nodes[:limit]
        
        return {
            "success": True,
            "query": query,
            "results": limited_results,
            "total_matches": len(matching_nodes),
            "returned_count": len(limited_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching nodes: {e}")
        raise HTTPException(status_code=500, detail="Failed to search nodes")


@router.get("/statistics")
async def get_graph_statistics():
    """
    Get statistics about the knowledge graph.
    
    Returns:
        Graph statistics including node/edge counts, connectivity, etc.
    """
    try:
        stats = await knowledge_graph_service.get_graph_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting graph statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get graph statistics")


@router.post("/rebuild")
async def rebuild_knowledge_graph():
    """
    Rebuild the entire knowledge graph from existing documents and notes.
    
    This is a maintenance operation that should be used sparingly.
    """
    try:
        from app.tasks.knowledge_graph_tasks import rebuild_entire_graph_task
        
        # Start background task for rebuilding
        task = rebuild_entire_graph_task.delay()
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "Knowledge graph rebuild initiated",
            "note": "This operation runs in the background and may take some time to complete"
        }
        
    except Exception as e:
        logger.error(f"Error rebuilding knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to rebuild knowledge graph")


@router.post("/cleanup")
async def cleanup_knowledge_graph():
    """
    Clean up orphaned nodes in the knowledge graph.
    
    This removes nodes that reference deleted documents or notes.
    """
    try:
        from app.tasks.knowledge_graph_tasks import cleanup_orphaned_nodes_task
        
        # Start background task for cleanup
        task = cleanup_orphaned_nodes_task.delay()
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "Knowledge graph cleanup initiated",
            "note": "This operation runs in the background"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up knowledge graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup knowledge graph")


@router.delete("/node/{node_id}")
async def delete_node(node_id: str):
    """
    Delete a specific node from the knowledge graph.
    
    Args:
        node_id: ID of the node to delete
        
    Returns:
        Deletion confirmation
    """
    try:
        # Load graph if needed
        if knowledge_graph_service.graph.number_of_nodes() == 0:
            await knowledge_graph_service._load_networkx_graph()
        
        # Check if node exists
        if node_id not in knowledge_graph_service.graph:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
        # Remove node from NetworkX graph
        knowledge_graph_service.graph.remove_node(node_id)
        
        # Save updated graph
        await knowledge_graph_service._save_networkx_graph()
        
        # TODO: Also remove from database
        
        return {
            "success": True,
            "message": f"Node {node_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node {node_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete node")