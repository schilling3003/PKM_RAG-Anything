"""
Celery application configuration.
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "pkm_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.document_processing", "app.tasks.search_tasks", "app.tasks.maintenance"]
)

# Configure Celery
celery_app.conf.update(
    # Task routing - using default queue for now
    # task_routes={
    #     "app.tasks.document_processing.*": {"queue": "document_processing"},
    #     "app.tasks.search_tasks.*": {"queue": "search"},
    # },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "app.tasks.maintenance.cleanup_old_tasks",
            "schedule": 3600.0,  # Every hour
        },
        "health-check": {
            "task": "app.tasks.maintenance.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)

# Task annotations for specific configuration
celery_app.conf.task_annotations = {
    "app.tasks.document_processing.process_document": {
        "rate_limit": "10/m",  # 10 tasks per minute
        "time_limit": 1800,    # 30 minutes for large documents
        "soft_time_limit": 1500,  # 25 minutes soft limit
    },
    "app.tasks.document_processing.batch_process_documents": {
        "rate_limit": "5/m",   # 5 batch tasks per minute
        "time_limit": 3600,    # 1 hour for batch processing
        "soft_time_limit": 3300,  # 55 minutes soft limit
    },
    "app.tasks.document_processing.process_folder": {
        "rate_limit": "2/m",   # 2 folder tasks per minute
        "time_limit": 7200,    # 2 hours for large folders
        "soft_time_limit": 6600,  # 110 minutes soft limit
    },
    "app.tasks.search_tasks.build_embeddings": {
        "rate_limit": "20/m",
        "time_limit": 300,
        "soft_time_limit": 240,
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])

if __name__ == "__main__":
    celery_app.start()