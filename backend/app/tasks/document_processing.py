"""
Document processing Celery tasks with RAG-Anything integration.
"""

import os
import time
import asyncio
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional, List
from celery import current_task
from celery.exceptions import Retry
import logging

from app.core.celery_app import celery_app
from app.core.database import get_db, SessionLocal
from app.models.database import Document, BackgroundTask
from app.core.exceptions import DocumentProcessingError, DatabaseError, ExternalServiceError
from app.services.document_processor import document_processor
from app.core.websocket import manager
from app.core.service_health import service_health_monitor
from app.core.retry_utils import retry_database_operation, retry_with_backoff, RetryConfig

logger = logging.getLogger(__name__)


@retry_database_operation("task_progress_update")
def update_task_progress(task_id: str, progress: int, current_step: str, status: str = "processing"):
    """Update task progress in database with retry logic."""
    db = SessionLocal()
    try:
        task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        if task:
            task.progress = progress
            task.current_step = current_step
            task.status = status
            task.updated_at = datetime.utcnow()
            db.commit()
        else:
            # Create new task record
            new_task = BackgroundTask(
                id=task_id,
                task_type="document_processing",
                status=status,
                progress=progress,
                current_step=current_step
            )
            db.add(new_task)
            db.commit()
            
        logger.info("Task progress updated", 
                   extra={
                       "task_id": task_id,
                       "progress": progress,
                       "status": status,
                       "current_step": current_step
                   })
                   
    except Exception as e:
        logger.error("Failed to update task progress", 
                    extra={
                        "task_id": task_id,
                        "error": str(e)
                    })
        db.rollback()
        raise DatabaseError(f"Failed to update task progress: {str(e)}")
    finally:
        db.close()


@retry_database_operation("document_status_update")
def update_document_status(document_id: str, status: str, error: Optional[str] = None):
    """Update document processing status with retry logic."""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_status = status
            document.updated_at = datetime.utcnow()
            if error:
                document.processing_error = error
            db.commit()
            
            logger.info("Document status updated",
                       extra={
                           "document_id": document_id,
                           "status": status,
                           "has_error": bool(error)
                       })
        else:
            logger.warning("Document not found for status update", 
                          extra={"document_id": document_id})
            
    except Exception as e:
        logger.error("Failed to update document status",
                    extra={
                        "document_id": document_id,
                        "error": str(e)
                    })
        db.rollback()
        raise DatabaseError(f"Failed to update document status: {str(e)}")
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.document_processing.process_document")
def process_document_task(self, document_id: str, file_path: str) -> Dict[str, Any]:
    """
    Background task for processing uploaded documents with RAG-Anything.
    
    Args:
        document_id: ID of the document to process
        file_path: Path to the uploaded file
        
    Returns:
        Dict containing processing results
    """
    task_id = self.request.id
    start_time = time.time()
    
    try:
        logger.info(f"Starting RAG-Anything document processing for {document_id}")
        
        # Update initial status
        update_task_progress(task_id, 0, "Initializing RAG-Anything processing", "processing")
        update_document_status(document_id, "processing")
        
        # Send WebSocket update (will be handled in event loop later)
        
        # Step 1: Validate file exists
        update_task_progress(task_id, 5, "Validating file")
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"File not found: {file_path}")
        
        # Step 2: Validate file with document processor
        update_task_progress(task_id, 10, "Validating file format")
        validation_result = document_processor.validate_file(file_path)
        if not validation_result["valid"]:
            raise DocumentProcessingError(f"File validation failed: {validation_result['error']}")
        
        logger.info(f"Processing {validation_result['file_type']} file of size {validation_result['file_size']} bytes")
        
        # Step 3: Process document with RAG-Anything + MinerU
        update_task_progress(task_id, 20, "Processing with RAG-Anything + MinerU 2.0")
        
        # Run async processing in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Send websocket update in the event loop
            loop.run_until_complete(_send_websocket_update(document_id, "processing", 20, "Processing with RAG-Anything"))
            
            processing_result = loop.run_until_complete(
                document_processor.process_document(file_path, document_id)
            )
        finally:
            loop.close()
        
        if not processing_result.get("success", True):
            raise DocumentProcessingError(f"RAG-Anything processing failed: {processing_result.get('error', 'Unknown error')}")
        
        # Step 4: Extract and process content
        update_task_progress(task_id, 60, "Extracting multimodal content")
        extracted_text = processing_result.get("extracted_text", "")
        images = processing_result.get("images", [])
        tables = processing_result.get("tables", [])
        image_descriptions = processing_result.get("image_descriptions", [])
        table_descriptions = processing_result.get("table_descriptions", [])
        audio_transcription = processing_result.get("audio_transcription", {})
        pdf_analysis = processing_result.get("pdf_analysis", {})
        
        # Step 5: Prepare full content for knowledge graph and embeddings
        update_task_progress(task_id, 70, "Preparing content for knowledge graph")
        
        # Determine content types
        has_audio = audio_transcription.get("processing_success", False)
        has_pdf_analysis = pdf_analysis.get("processing_success", False)
        
        # Combine all extracted content
        full_content = extracted_text
        
        if image_descriptions:
            full_content += "\n\n--- Image Descriptions ---\n"
            for img_desc in image_descriptions:
                full_content += f"\nImage: {img_desc['description']}\n"
                if img_desc.get('ocr_text'):
                    full_content += f"OCR Text: {img_desc['ocr_text']}\n"
        
        if table_descriptions:
            full_content += "\n\n--- Table Analysis ---\n"
            for table_desc in table_descriptions:
                full_content += f"\nTable: {table_desc['description']}\n"
                if table_desc.get('summary'):
                    full_content += f"Summary: {table_desc['summary']}\n"
        
        if has_audio and audio_transcription.get("transcription"):
            full_content += "\n\n--- Audio Transcription ---\n"
            full_content += audio_transcription["transcription"]
            if audio_transcription.get("summary"):
                full_content += f"\n\nSummary: {audio_transcription['summary']}\n"
        
        if has_pdf_analysis and pdf_analysis.get("text_content"):
            # For PDFs, the text_content might be very long, so we add it carefully
            pdf_text = pdf_analysis["text_content"]
            if len(pdf_text) > 10000:  # If very long, add summary info
                full_content += "\n\n--- PDF Analysis ---\n"
                full_content += f"PDF with {pdf_analysis.get('page_count', 0)} pages\n"
                full_content += pdf_text[:5000] + "\n[Content truncated for length]"
            else:
                full_content += "\n\n--- PDF Content ---\n"
                full_content += pdf_text
        
        # Step 6: Prepare metadata for knowledge graph
        metadata = {
            "file_type": validation_result["file_type"],
            "file_size": validation_result["file_size"],
            "processing_time": time.time() - start_time,
            "images_count": len(images),
            "tables_count": len(tables),
            "has_audio_content": has_audio,
            "has_pdf_analysis": has_pdf_analysis,
            "has_multimodal_content": len(images) > 0 or len(tables) > 0 or has_audio or has_pdf_analysis,
        }
        
        # Step 7: Build knowledge graph
        update_task_progress(task_id, 75, "Building knowledge graph with LightRAG")
        
        # Build knowledge graph from extracted content
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            knowledge_graph_result = loop.run_until_complete(
                _build_knowledge_graph(document_id, full_content, metadata)
            )
        finally:
            loop.close()
        
        # Step 7: Generate embeddings for vector storage
        update_task_progress(task_id, 85, "Generating embeddings for semantic search")
        
        # Store embeddings in ChromaDB
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            embeddings_stored = loop.run_until_complete(
                _store_embeddings(document_id, extracted_text, processing_result)
            )
        finally:
            loop.close()
        
        # Step 8: Update database with comprehensive results
        update_task_progress(task_id, 95, "Saving results to database")
        
        # Update metadata with processing results
        metadata.update({
            "processing_time": time.time() - start_time,
            "embeddings_stored": embeddings_stored,
            "knowledge_graph_built": knowledge_graph_result.get("success", False),
            "kg_nodes_added": knowledge_graph_result.get("nodes_added", 0),
            "kg_edges_added": knowledge_graph_result.get("edges_added", 0),
            "rag_anything_version": "latest",
            "mineru_version": "2.0",
            "audio_duration": audio_transcription.get("metadata", {}).get("duration", 0) if has_audio else 0,
            "pdf_pages": pdf_analysis.get("page_count", 0) if has_pdf_analysis else 0
        })
        
        _save_processing_results(document_id, full_content, metadata)
        
        # Step 9: Complete
        update_task_progress(task_id, 100, "Processing completed successfully", "completed")
        update_document_status(document_id, "completed")
        
        # Send final WebSocket update (skip for now to avoid async issues)
        
        result = {
            "status": "completed",
            "document_id": document_id,
            "extracted_text_length": len(full_content),
            "processing_time": time.time() - start_time,
            "file_type": validation_result["file_type"],
            "file_size": validation_result["file_size"],
            "images_processed": len(images),
            "tables_processed": len(tables),
            "audio_processed": has_audio,
            "pdf_analyzed": has_pdf_analysis,
            "multimodal_content": len(images) > 0 or len(tables) > 0 or has_audio or has_pdf_analysis,
            "embeddings_stored": embeddings_stored,
            "knowledge_graph_built": knowledge_graph_result.get("success", False),
            "kg_nodes_added": knowledge_graph_result.get("nodes_added", 0),
            "kg_edges_added": knowledge_graph_result.get("edges_added", 0)
        }
        
        logger.info(f"RAG-Anything document processing completed for {document_id}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Document processing failed for {document_id}: {error_msg}")
        
        # Update status to failed
        update_task_progress(task_id, 0, f"Processing failed: {error_msg}", "failed")
        update_document_status(document_id, "failed", error_msg)
        
        # Send WebSocket error update (skip for now to avoid async issues)
        
        # Re-raise the exception
        raise


@celery_app.task(bind=True, name="app.tasks.document_processing.batch_process_documents")
def batch_process_documents_task(self, document_ids: list, batch_options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process multiple documents in batch with enhanced progress tracking.
    
    Args:
        document_ids: List of document IDs to process
        batch_options: Optional batch processing configuration
        
    Returns:
        Dict containing batch processing results
    """
    batch_task_id = self.request.id
    start_time = time.time()
    
    # Default batch options
    if batch_options is None:
        batch_options = {}
    
    max_concurrent = batch_options.get("max_concurrent", 3)
    retry_failed = batch_options.get("retry_failed", True)
    
    try:
        logger.info(f"Starting batch processing of {len(document_ids)} documents")
        
        # Create batch task record
        update_task_progress(batch_task_id, 0, f"Initializing batch processing of {len(document_ids)} documents", "processing")
        
        results = []
        failed_count = 0
        processed_count = 0
        
        # Process documents in smaller batches to avoid overwhelming the system
        batch_size = max_concurrent
        total_batches = (len(document_ids) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(document_ids))
            batch_doc_ids = document_ids[start_idx:end_idx]
            
            # Update progress
            progress = int((batch_num / total_batches) * 90)  # Reserve 10% for final steps
            update_task_progress(
                batch_task_id, 
                progress, 
                f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_doc_ids)} documents)"
            )
            
            # Process current batch
            batch_results = []
            for doc_id in batch_doc_ids:
                try:
                    # Get document info from database
                    db = SessionLocal()
                    document = db.query(Document).filter(Document.id == doc_id).first()
                    db.close()
                    
                    if not document:
                        logger.warning(f"Document {doc_id} not found")
                        failed_count += 1
                        continue
                    
                    # Queue document for processing
                    result = process_document_task.delay(doc_id, document.file_path)
                    batch_results.append({
                        "document_id": doc_id,
                        "task_id": result.id,
                        "status": "queued",
                        "filename": document.filename
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to queue document {doc_id}: {e}")
                    failed_count += 1
                    batch_results.append({
                        "document_id": doc_id,
                        "status": "failed_to_queue",
                        "error": str(e)
                    })
            
            results.extend(batch_results)
            processed_count += len(batch_doc_ids)
            
            # Small delay between batches to prevent overwhelming
            if batch_num < total_batches - 1:
                time.sleep(1)
        
        # Final progress update
        update_task_progress(batch_task_id, 100, "Batch processing completed", "completed")
        
        batch_result = {
            "batch_task_id": batch_task_id,
            "total_documents": len(document_ids),
            "queued_successfully": len([r for r in results if r.get("status") == "queued"]),
            "failed_to_queue": failed_count,
            "processing_time": time.time() - start_time,
            "results": results,
            "batch_options": batch_options
        }
        
        logger.info(f"Batch processing completed: {batch_result['queued_successfully']}/{len(document_ids)} documents queued")
        return batch_result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Batch processing failed: {error_msg}")
        
        update_task_progress(batch_task_id, 0, f"Batch processing failed: {error_msg}", "failed")
        
        return {
            "batch_task_id": batch_task_id,
            "total_documents": len(document_ids),
            "queued_successfully": 0,
            "failed_to_queue": len(document_ids),
            "processing_time": time.time() - start_time,
            "error": error_msg,
            "results": []
        }


@celery_app.task(bind=True, name="app.tasks.document_processing.process_folder")
def process_folder_task(self, folder_path: str, file_extensions: List[str] = None, recursive: bool = True) -> Dict[str, Any]:
    """
    Process all documents in a folder.
    
    Args:
        folder_path: Path to folder containing documents
        file_extensions: List of file extensions to process
        recursive: Whether to process subdirectories
        
    Returns:
        Dict containing folder processing results
    """
    task_id = self.request.id
    start_time = time.time()
    
    try:
        logger.info(f"Starting folder processing: {folder_path}")
        
        update_task_progress(task_id, 0, f"Scanning folder: {folder_path}", "processing")
        
        if not os.path.exists(folder_path):
            raise DocumentProcessingError(f"Folder not found: {folder_path}")
        
        # Default file extensions
        if file_extensions is None:
            file_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.jpg', '.jpeg', '.png', '.mp3', '.wav', '.mp4']
        
        # Find all files to process
        files_to_process = []
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file.lower().endswith(ext) for ext in file_extensions):
                        files_to_process.append(file_path)
        else:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in file_extensions):
                    files_to_process.append(file_path)
        
        update_task_progress(task_id, 20, f"Found {len(files_to_process)} files to process")
        
        if not files_to_process:
            return {
                "folder_path": folder_path,
                "total_files": 0,
                "processed_files": [],
                "failed_files": [],
                "processing_time": time.time() - start_time,
                "message": "No files found to process"
            }
        
        # Create document records and queue for processing
        document_ids = []
        failed_files = []
        
        db = SessionLocal()
        try:
            for i, file_path in enumerate(files_to_process):
                try:
                    # Update progress
                    progress = 20 + int((i / len(files_to_process)) * 60)
                    update_task_progress(task_id, progress, f"Processing file {i+1}/{len(files_to_process)}")
                    
                    # Generate document ID
                    document_id = str(uuid.uuid4())
                    
                    # Get file info
                    file_stats = os.stat(file_path)
                    file_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                    
                    # Create document record
                    document = Document(
                        id=document_id,
                        filename=os.path.basename(file_path),
                        safe_filename=f"{document_id}_{os.path.basename(file_path)}",
                        file_path=file_path,
                        file_type=file_type,
                        file_size=file_stats.st_size,
                        processing_status="queued"
                    )
                    
                    db.add(document)
                    document_ids.append(document_id)
                    
                except Exception as e:
                    logger.error(f"Failed to create document record for {file_path}: {e}")
                    failed_files.append({
                        "file_path": file_path,
                        "error": str(e)
                    })
            
            db.commit()
            
        finally:
            db.close()
        
        # Queue batch processing
        update_task_progress(task_id, 90, "Queuing documents for processing")
        
        if document_ids:
            batch_task = batch_process_documents_task.delay(
                document_ids, 
                {"max_concurrent": 2, "retry_failed": True}
            )
            
            batch_task_id = batch_task.id
        else:
            batch_task_id = None
        
        update_task_progress(task_id, 100, "Folder processing completed", "completed")
        
        return {
            "folder_path": folder_path,
            "total_files": len(files_to_process),
            "queued_successfully": len(document_ids),
            "failed_files": failed_files,
            "batch_task_id": batch_task_id,
            "processing_time": time.time() - start_time,
            "file_extensions": file_extensions,
            "recursive": recursive
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Folder processing failed: {error_msg}")
        
        update_task_progress(task_id, 0, f"Folder processing failed: {error_msg}", "failed")
        
        return {
            "folder_path": folder_path,
            "total_files": 0,
            "queued_successfully": 0,
            "failed_files": [],
            "processing_time": time.time() - start_time,
            "error": error_msg
        }


@celery_app.task(name="app.tasks.document_processing.regenerate_embeddings")
def regenerate_embeddings_task(document_id: str) -> Dict[str, Any]:
    """
    Regenerate embeddings for a specific document.
    
    Args:
        document_id: Document ID to regenerate embeddings for
        
    Returns:
        Dict containing regeneration results
    """
    try:
        logger.info(f"Regenerating embeddings for document {document_id}")
        
        # Get document from database
        db = SessionLocal()
        document = db.query(Document).filter(Document.id == document_id).first()
        db.close()
        
        if not document:
            raise DocumentProcessingError(f"Document {document_id} not found")
        
        if not document.extracted_text:
            raise DocumentProcessingError(f"No extracted text found for document {document_id}")
        
        # Remove existing embeddings
        from app.core.vector_db import vector_db
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(vector_db.delete_document_embeddings(document_id))
        finally:
            loop.close()
        
        # Regenerate embeddings
        processing_result = {
            "extracted_text": document.extracted_text,
            "image_descriptions": [],
            "table_descriptions": [],
            "audio_transcription": {}
        }
        
        # Try to get additional content from metadata
        if document.doc_metadata:
            # This would be enhanced based on how metadata is stored
            pass
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            embeddings_stored = loop.run_until_complete(
                _store_embeddings(document_id, document.extracted_text, processing_result)
            )
        finally:
            loop.close()
        
        return {
            "document_id": document_id,
            "embeddings_regenerated": embeddings_stored,
            "success": embeddings_stored
        }
        
    except Exception as e:
        logger.error(f"Failed to regenerate embeddings for {document_id}: {e}")
        return {
            "document_id": document_id,
            "embeddings_regenerated": False,
            "success": False,
            "error": str(e)
        }


def _get_file_type(file_path: str) -> str:
    """Determine file type from file extension."""
    _, ext = os.path.splitext(file_path.lower())
    
    type_mapping = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.mp4': 'video/mp4',
        '.avi': 'video/avi'
    }
    
    return type_mapping.get(ext, 'application/octet-stream')


async def _store_embeddings(document_id: str, extracted_text: str, processing_result: Dict[str, Any]) -> bool:
    """Store document embeddings in vector database with progress tracking."""
    try:
        from app.core.vector_db import vector_db
        
        embeddings_count = 0
        total_items = 0
        
        # Count total items to process
        if extracted_text.strip():
            chunks = _split_text_into_chunks(extracted_text, max_chunk_size=1000)
            total_items += len(chunks)
        
        image_descriptions = processing_result.get("image_descriptions", [])
        total_items += len([img for img in image_descriptions if img.get("description")])
        
        table_descriptions = processing_result.get("table_descriptions", [])
        total_items += len([table for table in table_descriptions if table.get("description")])
        
        audio_transcription = processing_result.get("audio_transcription", {})
        if audio_transcription.get("transcription"):
            total_items += 1
        
        logger.info(f"Storing {total_items} embeddings for document {document_id}")
        
        # Generate embeddings for the main text
        if extracted_text.strip():
            chunks = _split_text_into_chunks(extracted_text, max_chunk_size=1000)
            
            for i, chunk in enumerate(chunks):
                try:
                    chunk_id = f"{document_id}_chunk_{i}"
                    
                    # Store in ChromaDB (embedding generation handled by vector_db)
                    await vector_db.add_document(
                        document_id=chunk_id,
                        content=chunk,
                        metadata={
                            "parent_document_id": document_id,
                            "chunk_index": i,
                            "content_type": "text",
                            "chunk_size": len(chunk)
                        }
                    )
                    embeddings_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to store text chunk {i} for {document_id}: {e}")
        
        # Store image descriptions as separate embeddings
        for i, img_desc in enumerate(image_descriptions):
            if img_desc.get("description"):
                try:
                    chunk_id = f"{document_id}_image_{i}"
                    
                    # Combine description with OCR text if available
                    content = img_desc["description"]
                    if img_desc.get("ocr_text"):
                        content += f"\n\nOCR Text: {img_desc['ocr_text']}"
                    
                    await vector_db.add_document(
                        document_id=chunk_id,
                        content=content,
                        metadata={
                            "parent_document_id": document_id,
                            "content_type": "image_description",
                            "image_path": img_desc.get("path", ""),
                            "has_ocr": bool(img_desc.get("ocr_text"))
                        }
                    )
                    embeddings_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to store image embedding {i} for {document_id}: {e}")
        
        # Store table descriptions as separate embeddings
        for i, table_desc in enumerate(table_descriptions):
            if table_desc.get("description"):
                try:
                    chunk_id = f"{document_id}_table_{i}"
                    
                    # Combine description with summary and insights
                    content = table_desc["description"]
                    if table_desc.get("summary"):
                        content += f"\n\nSummary: {table_desc['summary']}"
                    if table_desc.get("insights"):
                        content += f"\n\nKey Insights: {'; '.join(table_desc['insights'])}"
                    
                    await vector_db.add_document(
                        document_id=chunk_id,
                        content=content,
                        metadata={
                            "parent_document_id": document_id,
                            "content_type": "table_description",
                            "has_insights": bool(table_desc.get("insights"))
                        }
                    )
                    embeddings_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to store table embedding {i} for {document_id}: {e}")
        
        # Store audio transcription as embedding
        if audio_transcription.get("transcription"):
            try:
                chunk_id = f"{document_id}_audio"
                
                content = audio_transcription["transcription"]
                if audio_transcription.get("summary"):
                    content += f"\n\nSummary: {audio_transcription['summary']}"
                
                await vector_db.add_document(
                    document_id=chunk_id,
                    content=content,
                    metadata={
                        "parent_document_id": document_id,
                        "content_type": "audio_transcription",
                        "duration": audio_transcription.get("metadata", {}).get("duration", 0),
                        "has_summary": bool(audio_transcription.get("summary"))
                    }
                )
                embeddings_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store audio embedding for {document_id}: {e}")
        
        logger.info(f"Successfully stored {embeddings_count}/{total_items} embeddings for document {document_id}")
        return embeddings_count > 0
        
    except Exception as e:
        logger.error(f"Failed to store embeddings for {document_id}: {e}")
        return False


async def _build_knowledge_graph(document_id: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Build knowledge graph from document content using LightRAG."""
    try:
        from app.services.knowledge_graph import knowledge_graph_service
        
        logger.info(f"Building knowledge graph for document {document_id}")
        
        # Build knowledge graph from document content
        result = await knowledge_graph_service.build_graph_from_document(
            document_id=document_id,
            content=content,
            metadata=metadata
        )
        
        if result.get("success"):
            logger.info(f"Knowledge graph built successfully for document {document_id}: "
                       f"{result.get('nodes_added', 0)} nodes, {result.get('edges_added', 0)} edges")
        else:
            logger.warning(f"Knowledge graph building failed for document {document_id}: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to build knowledge graph for document {document_id}: {e}")
        return {
            "success": False,
            "document_id": document_id,
            "error": str(e),
            "nodes_added": 0,
            "edges_added": 0
        }


def _split_text_into_chunks(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks for better embedding storage."""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 200 characters
            sentence_end = text.rfind('.', start + max_chunk_size - 200, end)
            if sentence_end > start:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = max(start + max_chunk_size - overlap, end)
    
    return chunks


async def _send_websocket_update(document_id: str, status: str, progress: int, current_step: str):
    """Send WebSocket update for real-time progress tracking."""
    try:
        await manager.broadcast_processing_update({
            "type": "document_processing",
            "document_id": document_id,
            "status": status,
            "progress": progress,
            "current_step": current_step
        })
    except Exception as e:
        logger.error(f"Failed to send WebSocket update: {e}")


def _save_processing_results(document_id: str, extracted_text: str, metadata: Dict[str, Any]):
    """Save processing results to database."""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.extracted_text = extracted_text
            document.doc_metadata = metadata
            db.commit()
    except Exception as e:
        logger.error(f"Failed to save processing results: {e}")
        db.rollback()
    finally:
        db.close()