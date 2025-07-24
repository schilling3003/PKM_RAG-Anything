"""
Search and embedding generation Celery tasks.
"""

import time
from typing import List, Dict, Any
from celery import current_task
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.vector_db import vector_db
from app.models.database import Document, Note

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.search_tasks.build_embeddings")
def build_embeddings_task(content_id: str, content_type: str, content_text: str) -> Dict[str, Any]:
    """
    Generate embeddings for content and store in vector database.
    
    Args:
        content_id: ID of the content (document or note)
        content_type: Type of content ('document' or 'note')
        content_text: Text content to generate embeddings for
        
    Returns:
        Dict containing embedding generation results
    """
    start_time = time.time()
    
    try:
        logger.info(f"Generating embeddings for {content_type} {content_id}")
        
        # Prepare metadata
        metadata = {
            "content_id": content_id,
            "content_type": content_type,
            "created_at": time.time()
        }
        
        # Get additional metadata from database
        db = SessionLocal()
        try:
            if content_type == "document":
                item = db.query(Document).filter(Document.id == content_id).first()
                if item:
                    metadata.update({
                        "filename": item.filename,
                        "file_type": item.file_type,
                        "file_size": item.file_size
                    })
            elif content_type == "note":
                item = db.query(Note).filter(Note.id == content_id).first()
                if item:
                    metadata.update({
                        "title": item.title,
                        "tags": item.tags,
                        "word_count": item.word_count
                    })
        finally:
            db.close()
        
        # Add to vector database (ChromaDB will generate embeddings automatically)
        # Note: This needs to be run in an async context
        import asyncio
        
        async def add_embeddings():
            return await vector_db.add_documents(
                documents=[content_text],
                metadatas=[metadata],
                ids=[f"{content_type}_{content_id}"]
            )
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(add_embeddings())
        finally:
            loop.close()
        
        if success:
            processing_time = time.time() - start_time
            logger.info(f"Embeddings generated successfully for {content_type} {content_id}")
            
            return {
                "status": "completed",
                "content_id": content_id,
                "content_type": content_type,
                "processing_time": processing_time,
                "text_length": len(content_text)
            }
        else:
            raise Exception("Failed to add embeddings to vector database")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Embedding generation failed for {content_type} {content_id}: {error_msg}")
        raise


@celery_app.task(name="app.tasks.search_tasks.rebuild_all_embeddings")
def rebuild_all_embeddings_task() -> Dict[str, Any]:
    """
    Rebuild all embeddings for documents and notes.
    
    Returns:
        Dict containing rebuild results
    """
    start_time = time.time()
    
    try:
        logger.info("Starting full embeddings rebuild")
        
        # Reset vector database
        vector_db.reset_collection()
        
        db = SessionLocal()
        try:
            # Get all documents with extracted text
            documents = db.query(Document).filter(
                Document.processing_status == "completed",
                Document.extracted_text.isnot(None)
            ).all()
            
            # Get all notes
            notes = db.query(Note).all()
            
        finally:
            db.close()
        
        # Process documents
        document_tasks = []
        for doc in documents:
            if doc.extracted_text:
                task = build_embeddings_task.delay(
                    doc.id, "document", doc.extracted_text
                )
                document_tasks.append(task.id)
        
        # Process notes
        note_tasks = []
        for note in notes:
            if note.content:
                task = build_embeddings_task.delay(
                    note.id, "note", f"{note.title}\n\n{note.content}"
                )
                note_tasks.append(task.id)
        
        total_time = time.time() - start_time
        
        result = {
            "status": "completed",
            "documents_queued": len(document_tasks),
            "notes_queued": len(note_tasks),
            "total_queued": len(document_tasks) + len(note_tasks),
            "processing_time": total_time,
            "document_task_ids": document_tasks,
            "note_task_ids": note_tasks
        }
        
        logger.info(f"Embeddings rebuild queued: {result['total_queued']} items")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Embeddings rebuild failed: {error_msg}")
        raise


@celery_app.task(name="app.tasks.search_tasks.update_search_index")
def update_search_index_task(content_id: str, content_type: str) -> Dict[str, Any]:
    """
    Update search index for specific content.
    
    Args:
        content_id: ID of the content to update
        content_type: Type of content ('document' or 'note')
        
    Returns:
        Dict containing update results
    """
    try:
        logger.info(f"Updating search index for {content_type} {content_id}")
        
        db = SessionLocal()
        try:
            if content_type == "document":
                item = db.query(Document).filter(Document.id == content_id).first()
                content_text = item.extracted_text if item else None
            elif content_type == "note":
                item = db.query(Note).filter(Note.id == content_id).first()
                content_text = f"{item.title}\n\n{item.content}" if item else None
            else:
                raise ValueError(f"Unknown content type: {content_type}")
                
        finally:
            db.close()
        
        if not content_text:
            raise ValueError(f"No content found for {content_type} {content_id}")
        
        # Update embeddings
        task = build_embeddings_task.delay(content_id, content_type, content_text)
        
        return {
            "status": "queued",
            "content_id": content_id,
            "content_type": content_type,
            "embedding_task_id": task.id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Search index update failed for {content_type} {content_id}: {error_msg}")
        raise