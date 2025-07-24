"""
Maintenance and monitoring Celery tasks.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal, DatabaseManager
from app.core.vector_db import vector_db
from app.models.database import BackgroundTask, SearchHistory

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.maintenance.cleanup_old_tasks")
def cleanup_old_tasks() -> Dict[str, Any]:
    """
    Clean up old completed/failed tasks from the database.
    
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info("Starting cleanup of old tasks")
        
        # Remove tasks older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        db = SessionLocal()
        try:
            # Count tasks to be deleted
            old_tasks = db.query(BackgroundTask).filter(
                BackgroundTask.created_at < cutoff_time,
                BackgroundTask.status.in_(["completed", "failed"])
            )
            
            count_to_delete = old_tasks.count()
            
            # Delete old tasks
            deleted_count = old_tasks.delete(synchronize_session=False)
            db.commit()
            
        finally:
            db.close()
        
        logger.info(f"Cleaned up {deleted_count} old tasks")
        
        return {
            "status": "completed",
            "deleted_tasks": deleted_count,
            "cutoff_time": cutoff_time.isoformat()
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task cleanup failed: {error_msg}")
        raise


@celery_app.task(name="app.tasks.maintenance.cleanup_old_search_history")
def cleanup_old_search_history() -> Dict[str, Any]:
    """
    Clean up old search history entries.
    
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info("Starting cleanup of old search history")
        
        # Remove search history older than 30 days
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        
        db = SessionLocal()
        try:
            # Count entries to be deleted
            old_searches = db.query(SearchHistory).filter(
                SearchHistory.created_at < cutoff_time
            )
            
            count_to_delete = old_searches.count()
            
            # Delete old search history
            deleted_count = old_searches.delete(synchronize_session=False)
            db.commit()
            
        finally:
            db.close()
        
        logger.info(f"Cleaned up {deleted_count} old search history entries")
        
        return {
            "status": "completed",
            "deleted_entries": deleted_count,
            "cutoff_time": cutoff_time.isoformat()
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Search history cleanup failed: {error_msg}")
        raise


@celery_app.task(name="app.tasks.maintenance.health_check")
def health_check() -> Dict[str, Any]:
    """
    Perform system health check.
    
    Returns:
        Dict containing health check results
    """
    try:
        logger.info("Performing system health check")
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # Check database
        try:
            db_info = DatabaseManager.get_database_info()
            health_status["components"]["database"] = {
                "status": "healthy",
                "tables": len(db_info["tables"]),
                "engine": db_info["engine"]
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check vector database
        try:
            vector_info = vector_db.get_collection_info()
            health_status["components"]["vector_db"] = {
                "status": "healthy",
                "collection": vector_info["name"],
                "document_count": vector_info["count"]
            }
        except Exception as e:
            health_status["components"]["vector_db"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check task queue (this task running means it's working)
        health_status["components"]["task_queue"] = {
            "status": "healthy",
            "message": "Task queue is processing tasks"
        }
        
        # Get system statistics
        db = SessionLocal()
        try:
            from app.models.database import Document, Note, BackgroundTask
            
            stats = {
                "total_documents": db.query(Document).count(),
                "completed_documents": db.query(Document).filter(
                    Document.processing_status == "completed"
                ).count(),
                "total_notes": db.query(Note).count(),
                "active_tasks": db.query(BackgroundTask).filter(
                    BackgroundTask.status.in_(["pending", "processing"])
                ).count()
            }
            
            health_status["statistics"] = stats
            
        finally:
            db.close()
        
        logger.info(f"Health check completed: {health_status['status']}")
        return health_status
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Health check failed: {error_msg}")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": error_msg
        }


@celery_app.task(name="app.tasks.maintenance.database_maintenance")
def database_maintenance() -> Dict[str, Any]:
    """
    Perform database maintenance operations.
    
    Returns:
        Dict containing maintenance results
    """
    try:
        logger.info("Starting database maintenance")
        
        start_time = time.time()
        
        # Vacuum database to reclaim space
        DatabaseManager.vacuum_database()
        
        # Get database statistics
        db_info = DatabaseManager.get_database_info()
        
        maintenance_time = time.time() - start_time
        
        result = {
            "status": "completed",
            "maintenance_time": maintenance_time,
            "database_info": db_info,
            "operations_performed": ["vacuum", "optimize"]
        }
        
        logger.info(f"Database maintenance completed in {maintenance_time:.2f} seconds")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Database maintenance failed: {error_msg}")
        raise