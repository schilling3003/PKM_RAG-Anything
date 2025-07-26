"""
Document management API endpoints.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.models.database import Document
from app.models.schemas import (
    DocumentUpload, DocumentResponse, DocumentsListResponse,
    ProcessingStatusResponse, BaseResponse
)
from app.services.file_manager import file_manager
from app.services.document_processor import document_processor
from app.tasks.document_processing import process_document_task, batch_process_documents_task
from app.core.exceptions import DocumentProcessingError, FileStorageError, ValidationError
from app.core.service_health import service_health_monitor
from app.core.retry_utils import retry_database_operation

router = APIRouter()


@router.post("/upload", response_model=DocumentUpload)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and queue document for processing with comprehensive error handling.
    
    Args:
        file: Uploaded file
        db: Database session
        
    Returns:
        Document upload response with task information
    """
    # Generate document ID
    document_id = str(uuid.uuid4())
    
    upload_context = {
        "document_id": document_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "endpoint": "upload_document"
    }
    
    try:
        # Check service availability before processing
        await service_health_monitor.ensure_service_available("storage", "document upload")
        await service_health_monitor.ensure_service_available("database", "document upload")
        await service_health_monitor.ensure_service_available("celery", "document upload")
        
        # Save uploaded file
        file_info = await file_manager.save_uploaded_file(file, document_id)
        
        upload_context.update({
            "file_size": file_info["file_size"],
            "file_path": file_info["file_path"]
        })
        
        # Create document record in database with retry
        @retry_database_operation("document_creation")
        def create_document_record():
            document = Document(
                id=document_id,
                filename=file_info["original_filename"],
                file_path=file_info["file_path"],
                file_type=file_info["file_type"],
                file_size=file_info["file_size"],
                processing_status="queued"
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        
        document = create_document_record()
        
        # Queue background processing task
        try:
            task = process_document_task.delay(document_id, file_info["file_path"])
            
            # Update document with task ID
            document.task_id = task.id
            db.commit()
            
            upload_context["task_id"] = task.id
            
        except Exception as e:
            # If task queuing fails, update document status
            document.processing_status = "failed"
            document.processing_error = f"Failed to queue processing task: {str(e)}"
            db.commit()
            
            raise DocumentProcessingError(
                f"Failed to queue document processing: {str(e)}",
                details=upload_context,
                user_message="Document uploaded but processing could not be started. Please try reprocessing.",
                recovery_suggestions=[
                    "Try reprocessing the document from the document list",
                    "Check if the system is under heavy load",
                    "Contact support if the issue persists"
                ]
            )
        
        return DocumentUpload(
            document_id=document_id,
            task_id=task.id,
            status="queued",
            message="Document uploaded and queued for processing"
        )
        
    except (FileStorageError, ValidationError, DocumentProcessingError) as e:
        # These are already properly formatted PKM exceptions
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Upload failed due to unexpected error",
                "message": str(e),
                "context": upload_context,
                "suggestions": [
                    "Try uploading the file again",
                    "Check if the file is corrupted",
                    "Contact support if the problem persists"
                ]
            }
        )


@router.post("/upload-multiple")
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple documents for batch processing.
    
    Args:
        files: List of uploaded files
        db: Database session
        
    Returns:
        Batch upload response
    """
    try:
        uploaded_documents = []
        document_ids = []
        
        for file in files:
            try:
                # Generate document ID
                document_id = str(uuid.uuid4())
                
                # Save uploaded file
                file_info = await file_manager.save_uploaded_file(file, document_id)
                
                # Create document record
                document = Document(
                    id=document_id,
                    filename=file_info["original_filename"],
                    file_path=file_info["file_path"],
                    file_type=file_info["file_type"],
                    file_size=file_info["file_size"],
                    processing_status="queued"
                )
                
                db.add(document)
                document_ids.append(document_id)
                
                uploaded_documents.append({
                    "document_id": document_id,
                    "filename": file_info["original_filename"],
                    "status": "uploaded"
                })
                
            except Exception as e:
                uploaded_documents.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        db.commit()
        
        # Queue batch processing task
        if document_ids:
            batch_task = batch_process_documents_task.delay(document_ids)
            
            return {
                "total_files": len(files),
                "uploaded_successfully": len(document_ids),
                "failed_uploads": len(files) - len(document_ids),
                "batch_task_id": batch_task.id,
                "documents": uploaded_documents
            }
        else:
            return {
                "total_files": len(files),
                "uploaded_successfully": 0,
                "failed_uploads": len(files),
                "documents": uploaded_documents
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@router.get("/", response_model=DocumentsListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List documents with optional filtering.
    
    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        status: Filter by processing status
        db: Database session
        
    Returns:
        List of documents
    """
    try:
        query = db.query(Document)
        
        if status:
            query = query.filter(Document.processing_status == status)
        
        total = query.count()
        documents = query.offset(skip).limit(limit).all()
        
        return DocumentsListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total,
            message=f"Retrieved {len(documents)} documents"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Get specific document details.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Document details
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(document_id: str, db: Session = Depends(get_db)):
    """
    Get document processing status.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Processing status information
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get detailed progress from Celery task if processing
        progress = 0
        current_step = ""
        estimated_time = None
        
        if document.processing_status == "processing" and document.task_id:
            try:
                from app.core.celery_app import celery_app
                from app.models.database import BackgroundTask
                
                # Check background task table for detailed progress
                bg_task = db.query(BackgroundTask).filter(BackgroundTask.id == document.task_id).first()
                if bg_task:
                    progress = bg_task.progress
                    current_step = bg_task.current_step
                else:
                    # Fallback to Celery task info
                    celery_task = celery_app.AsyncResult(document.task_id)
                    if celery_task.info:
                        progress = celery_task.info.get("progress", 0)
                        current_step = celery_task.info.get("current_step", "")
                        
            except Exception as e:
                # If we can't get detailed progress, just return basic status
                pass
        
        return ProcessingStatusResponse(
            document_id=document_id,
            status=document.processing_status,
            progress=progress,
            current_step=current_step,
            error=document.processing_error,
            estimated_time_remaining=estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")


@router.delete("/{document_id}", response_model=BaseResponse)
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete document and associated files.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from storage
        if document.file_path:
            file_manager.delete_file(document.file_path)
        
        # Delete processed files directory
        import os
        from app.core.config import settings
        processed_dir = os.path.join(settings.PROCESSED_DIR, document_id)
        if os.path.exists(processed_dir):
            import shutil
            shutil.rmtree(processed_dir)
        
        # Delete database record
        db.delete(document)
        db.commit()
        
        return BaseResponse(
            success=True,
            message=f"Document {document_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/{document_id}/download")
async def download_document(document_id: str, db: Session = Depends(get_db)):
    """
    Download original document file.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        File download response
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.file_path or not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        return FileResponse(
            path=document.file_path,
            filename=document.filename,
            media_type=document.file_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")


@router.post("/{document_id}/reprocess", response_model=DocumentUpload)
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reprocess an existing document.
    
    Args:
        document_id: Document ID
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Reprocessing task information
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.file_path or not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Reset processing status
        document.processing_status = "queued"
        document.processing_error = None
        document.extracted_text = None
        
        # Queue new processing task
        task = process_document_task.delay(document_id, document.file_path)
        document.task_id = task.id
        
        db.commit()
        
        return DocumentUpload(
            document_id=document_id,
            task_id=task.id,
            status="queued",
            message="Document queued for reprocessing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {str(e)}")


@router.get("/storage/stats")
async def get_storage_stats():
    """
    Get storage usage statistics.
    
    Returns:
        Storage statistics
    """
    try:
        stats = file_manager.get_storage_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")


@router.post("/storage/cleanup")
async def cleanup_old_files(days_old: int = 30):
    """
    Clean up old files from storage.
    
    Args:
        days_old: Number of days after which files are considered old
        
    Returns:
        Cleanup results
    """
    try:
        result = file_manager.cleanup_old_files(days_old)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/process-folder")
async def process_folder(
    folder_path: str,
    file_extensions: Optional[List[str]] = None,
    recursive: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Process all documents in a folder.
    
    Args:
        folder_path: Path to folder containing documents
        file_extensions: List of file extensions to process
        recursive: Whether to process subdirectories recursively
        
    Returns:
        Folder processing task information
    """
    try:
        from app.tasks.document_processing import process_folder_task
        
        # Validate folder path
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="Folder not found")
        
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        # Queue folder processing task
        task = process_folder_task.delay(folder_path, file_extensions, recursive)
        
        return {
            "task_id": task.id,
            "folder_path": folder_path,
            "file_extensions": file_extensions,
            "recursive": recursive,
            "status": "queued",
            "message": "Folder processing queued successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process folder: {str(e)}")


@router.post("/batch-process")
async def batch_process_documents(
    document_ids: List[str],
    max_concurrent: int = 3,
    retry_failed: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Process multiple documents in batch.
    
    Args:
        document_ids: List of document IDs to process
        max_concurrent: Maximum number of concurrent processing tasks
        retry_failed: Whether to retry failed documents
        
    Returns:
        Batch processing task information
    """
    try:
        from app.tasks.document_processing import batch_process_documents_task
        
        if not document_ids:
            raise HTTPException(status_code=400, detail="No document IDs provided")
        
        # Validate that documents exist
        existing_docs = db.query(Document).filter(Document.id.in_(document_ids)).all()
        existing_ids = {doc.id for doc in existing_docs}
        missing_ids = set(document_ids) - existing_ids
        
        if missing_ids:
            raise HTTPException(
                status_code=404, 
                detail=f"Documents not found: {list(missing_ids)}"
            )
        
        # Queue batch processing task
        batch_options = {
            "max_concurrent": max_concurrent,
            "retry_failed": retry_failed
        }
        
        task = batch_process_documents_task.delay(document_ids, batch_options)
        
        return {
            "batch_task_id": task.id,
            "document_count": len(document_ids),
            "batch_options": batch_options,
            "status": "queued",
            "message": f"Batch processing of {len(document_ids)} documents queued successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch processing: {str(e)}")


@router.post("/{document_id}/regenerate-embeddings")
async def regenerate_embeddings(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Regenerate embeddings for a specific document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Embedding regeneration task information
    """
    try:
        from app.tasks.document_processing import regenerate_embeddings_task
        
        # Validate document exists
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.extracted_text:
            raise HTTPException(
                status_code=400, 
                detail="Document has no extracted text to generate embeddings from"
            )
        
        # Queue embedding regeneration task
        task = regenerate_embeddings_task.delay(document_id)
        
        return {
            "task_id": task.id,
            "document_id": document_id,
            "status": "queued",
            "message": "Embedding regeneration queued successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate embeddings: {str(e)}")


@router.get("/batch-status/{batch_task_id}")
async def get_batch_status(batch_task_id: str):
    """
    Get status of a batch processing task.
    
    Args:
        batch_task_id: Batch task ID
        
    Returns:
        Batch processing status
    """
    try:
        from app.core.celery_app import celery_app
        from app.models.database import BackgroundTask
        
        # Get task from Celery
        celery_task = celery_app.AsyncResult(batch_task_id)
        
        # Get detailed progress from database if available
        db = SessionLocal()
        try:
            bg_task = db.query(BackgroundTask).filter(BackgroundTask.id == batch_task_id).first()
        finally:
            db.close()
        
        result = {
            "batch_task_id": batch_task_id,
            "status": celery_task.status,
            "result": celery_task.result,
            "progress": 0,
            "current_step": ""
        }
        
        if bg_task:
            result.update({
                "progress": bg_task.progress,
                "current_step": bg_task.current_step,
                "created_at": bg_task.created_at.isoformat(),
                "updated_at": bg_task.updated_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")