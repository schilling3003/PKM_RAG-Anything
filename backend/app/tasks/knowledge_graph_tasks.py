"""
Knowledge graph related Celery tasks.
"""

import asyncio
import logging
from typing import Dict, Any, List
from celery import current_task

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.database import Note, Document
from app.services.knowledge_graph import knowledge_graph_service
from app.core.websocket import manager

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.knowledge_graph_tasks.build_graph_from_note")
def build_graph_from_note_task(self, note_id: str) -> Dict[str, Any]:
    """
    Background task to build knowledge graph from a note.
    
    Args:
        note_id: ID of the note to process
        
    Returns:
        Dict containing graph building results
    """
    task_id = self.request.id
    
    try:
        logger.info(f"Building knowledge graph from note {note_id}")
        
        # Get note from database
        db = SessionLocal()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                raise ValueError(f"Note {note_id} not found")
            
            note_data = {
                "title": note.title,
                "content": note.content,
                "tags": note.tags or []
            }
        finally:
            db.close()
        
        # Build knowledge graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                knowledge_graph_service.build_graph_from_note(
                    note_id=note_id,
                    content=note_data["content"],
                    title=note_data["title"],
                    tags=note_data["tags"]
                )
            )
        finally:
            loop.close()
        
        # Send WebSocket update
        asyncio.create_task(_send_graph_update(note_id, "note", result))
        
        logger.info(f"Knowledge graph built from note {note_id}: "
                   f"{result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to build knowledge graph from note {note_id}: {error_msg}")
        
        result = {
            "success": False,
            "note_id": note_id,
            "error": error_msg,
            "nodes_added": 0,
            "edges_added": 0
        }
        
        # Send error update
        asyncio.create_task(_send_graph_update(note_id, "note", result))
        
        return result


@celery_app.task(bind=True, name="app.tasks.knowledge_graph_tasks.rebuild_entire_graph")
def rebuild_entire_graph_task(self) -> Dict[str, Any]:
    """
    Background task to rebuild the entire knowledge graph from all documents and notes.
    
    Returns:
        Dict containing rebuild results
    """
    task_id = self.request.id
    
    try:
        logger.info("Starting complete knowledge graph rebuild")
        
        # Get all documents and notes
        db = SessionLocal()
        try:
            documents = db.query(Document).filter(
                Document.processing_status == "completed",
                Document.extracted_text.isnot(None)
            ).all()
            
            notes = db.query(Note).all()
        finally:
            db.close()
        
        total_items = len(documents) + len(notes)
        processed_items = 0
        failed_items = []
        
        logger.info(f"Rebuilding knowledge graph from {len(documents)} documents and {len(notes)} notes")
        
        # Process documents
        for doc in documents:
            try:
                # Prepare metadata
                metadata = {
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "type": "document"
                }
                
                # Build graph from document
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        knowledge_graph_service.build_graph_from_document(
                            document_id=doc.id,
                            content=doc.extracted_text or "",
                            metadata=metadata
                        )
                    )
                finally:
                    loop.close()
                
                if result.get("success"):
                    processed_items += 1
                    logger.info(f"Processed document {doc.id}: "
                               f"{result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                else:
                    failed_items.append({
                        "type": "document",
                        "id": doc.id,
                        "filename": doc.filename,
                        "error": result.get("error", "Unknown error")
                    })
                
            except Exception as e:
                logger.error(f"Failed to process document {doc.id}: {e}")
                failed_items.append({
                    "type": "document",
                    "id": doc.id,
                    "filename": doc.filename,
                    "error": str(e)
                })
        
        # Process notes
        for note in notes:
            try:
                # Build graph from note
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        knowledge_graph_service.build_graph_from_note(
                            note_id=note.id,
                            content=note.content,
                            title=note.title,
                            tags=note.tags or []
                        )
                    )
                finally:
                    loop.close()
                
                if result.get("success"):
                    processed_items += 1
                    logger.info(f"Processed note {note.id}: "
                               f"{result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
                else:
                    failed_items.append({
                        "type": "note",
                        "id": note.id,
                        "title": note.title,
                        "error": result.get("error", "Unknown error")
                    })
                
            except Exception as e:
                logger.error(f"Failed to process note {note.id}: {e}")
                failed_items.append({
                    "type": "note",
                    "id": note.id,
                    "title": note.title,
                    "error": str(e)
                })
        
        # Get final graph statistics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            graph_stats = loop.run_until_complete(
                knowledge_graph_service.get_graph_statistics()
            )
        finally:
            loop.close()
        
        result = {
            "success": True,
            "total_items": total_items,
            "processed_successfully": processed_items,
            "failed_items": len(failed_items),
            "failed_details": failed_items,
            "final_graph_stats": graph_stats
        }
        
        # Send WebSocket update about rebuild completion
        asyncio.create_task(_send_rebuild_complete_update(result))
        
        logger.info(f"Knowledge graph rebuild completed: {processed_items}/{total_items} items processed successfully")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Knowledge graph rebuild failed: {error_msg}")
        
        result = {
            "success": False,
            "error": error_msg,
            "total_items": 0,
            "processed_successfully": 0,
            "failed_items": 0,
            "failed_details": []
        }
        
        # Send error update
        asyncio.create_task(_send_rebuild_complete_update(result))
        
        return result


@celery_app.task(bind=True, name="app.tasks.knowledge_graph_tasks.update_graph_real_time")
def update_graph_real_time_task(self, content_id: str, content_type: str, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Background task to update knowledge graph in real-time when content changes.
    
    Args:
        content_id: ID of the content (document or note)
        content_type: Type of content ("document" or "note")
        content: Content text
        metadata: Additional metadata
        
    Returns:
        Dict containing update results
    """
    try:
        logger.info(f"Real-time knowledge graph update for {content_type} {content_id}")
        
        # Update knowledge graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                knowledge_graph_service.update_graph_real_time(
                    content_id=content_id,
                    content_type=content_type,
                    content=content,
                    metadata=metadata
                )
            )
        finally:
            loop.close()
        
        return {
            "success": True,
            "content_id": content_id,
            "content_type": content_type,
            "message": "Knowledge graph updated successfully"
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Real-time knowledge graph update failed for {content_type} {content_id}: {error_msg}")
        
        return {
            "success": False,
            "content_id": content_id,
            "content_type": content_type,
            "error": error_msg
        }


@celery_app.task(name="app.tasks.knowledge_graph_tasks.cleanup_orphaned_nodes")
def cleanup_orphaned_nodes_task() -> Dict[str, Any]:
    """
    Background task to clean up orphaned nodes in the knowledge graph.
    
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info("Starting knowledge graph cleanup")
        
        # Get all document and note IDs from database
        db = SessionLocal()
        try:
            existing_doc_ids = set(doc.id for doc in db.query(Document.id).all())
            existing_note_ids = set(note.id for note in db.query(Note.id).all())
        finally:
            db.close()
        
        # Load knowledge graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Load graph if needed
            if knowledge_graph_service.graph.number_of_nodes() == 0:
                loop.run_until_complete(knowledge_graph_service._load_networkx_graph())
            
            # Find orphaned nodes
            orphaned_nodes = []
            for node_id, node_data in knowledge_graph_service.graph.nodes(data=True):
                source_doc_id = node_data.get("source_id")
                if source_doc_id:
                    # Check if source document/note still exists
                    if (source_doc_id not in existing_doc_ids and 
                        source_doc_id not in existing_note_ids):
                        orphaned_nodes.append(node_id)
            
            # Remove orphaned nodes
            removed_count = 0
            for node_id in orphaned_nodes:
                try:
                    knowledge_graph_service.graph.remove_node(node_id)
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove orphaned node {node_id}: {e}")
            
            # Save updated graph
            if removed_count > 0:
                loop.run_until_complete(knowledge_graph_service._save_networkx_graph())
            
            # Get updated statistics
            graph_stats = loop.run_until_complete(
                knowledge_graph_service.get_graph_statistics()
            )
            
        finally:
            loop.close()
        
        result = {
            "success": True,
            "orphaned_nodes_found": len(orphaned_nodes),
            "orphaned_nodes_removed": removed_count,
            "final_graph_stats": graph_stats
        }
        
        logger.info(f"Knowledge graph cleanup completed: {removed_count} orphaned nodes removed")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Knowledge graph cleanup failed: {error_msg}")
        
        return {
            "success": False,
            "error": error_msg,
            "orphaned_nodes_found": 0,
            "orphaned_nodes_removed": 0
        }


async def _send_graph_update(content_id: str, content_type: str, result: Dict[str, Any]):
    """Send WebSocket update about knowledge graph changes."""
    try:
        await manager.broadcast_message({
            "type": "knowledge_graph_update",
            "content_id": content_id,
            "content_type": content_type,
            "success": result.get("success", False),
            "nodes_added": result.get("nodes_added", 0),
            "edges_added": result.get("edges_added", 0),
            "error": result.get("error")
        })
    except Exception as e:
        logger.error(f"Failed to send graph update WebSocket message: {e}")


async def _send_rebuild_complete_update(result: Dict[str, Any]):
    """Send WebSocket update about knowledge graph rebuild completion."""
    try:
        await manager.broadcast_message({
            "type": "knowledge_graph_rebuild_complete",
            "success": result.get("success", False),
            "total_items": result.get("total_items", 0),
            "processed_successfully": result.get("processed_successfully", 0),
            "failed_items": result.get("failed_items", 0),
            "final_graph_stats": result.get("final_graph_stats", {}),
            "error": result.get("error")
        })
    except Exception as e:
        logger.error(f"Failed to send rebuild complete WebSocket message: {e}")