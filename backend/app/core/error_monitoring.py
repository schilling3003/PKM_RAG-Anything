"""
Enhanced error monitoring and alerting system.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from app.core.exceptions import PKMException, ErrorSeverity, ErrorCategory, error_monitor
from app.core.service_health import service_health_monitor, ServiceStatus

logger = structlog.get_logger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorAlert:
    """Error alert data structure."""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    error_details: Dict[str, Any]
    service_affected: Optional[str]
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "resolution_time": self.resolution_time.isoformat() if self.resolution_time else None
        }


class ErrorAggregator:
    """
    Aggregates similar errors to prevent alert spam.
    """
    
    def __init__(self, window_minutes: int = 5, threshold: int = 3):
        self.window_minutes = window_minutes
        self.threshold = threshold
        self.error_buckets = {}
        self.last_cleanup = datetime.utcnow()
    
    def should_alert(self, error: PKMException) -> bool:
        """
        Determine if an error should trigger an alert based on aggregation rules.
        
        Args:
            error: The error to check
            
        Returns:
            True if alert should be sent, False if suppressed
        """
        # Create bucket key based on error type and category
        bucket_key = f"{error.category.value}:{error.error_code}"
        
        current_time = datetime.utcnow()
        
        # Clean up old buckets periodically
        if (current_time - self.last_cleanup).seconds > 300:  # 5 minutes
            self._cleanup_old_buckets(current_time)
        
        # Initialize bucket if not exists
        if bucket_key not in self.error_buckets:
            self.error_buckets[bucket_key] = []
        
        # Add current error to bucket
        self.error_buckets[bucket_key].append(current_time)
        
        # Count errors in current window
        window_start = current_time - timedelta(minutes=self.window_minutes)
        recent_errors = [
            ts for ts in self.error_buckets[bucket_key] 
            if ts >= window_start
        ]
        
        # Update bucket with only recent errors
        self.error_buckets[bucket_key] = recent_errors
        
        # Alert on first error or when threshold is reached
        error_count = len(recent_errors)
        
        if error_count == 1:
            # First occurrence - always alert
            return True
        elif error_count == self.threshold:
            # Threshold reached - alert about pattern
            logger.warning(
                f"Error pattern detected",
                bucket_key=bucket_key,
                error_count=error_count,
                window_minutes=self.window_minutes
            )
            return True
        elif error_count > self.threshold and error_count % (self.threshold * 2) == 0:
            # Exponential backoff for continued errors
            return True
        
        return False
    
    def _cleanup_old_buckets(self, current_time: datetime):
        """Remove old error entries from buckets."""
        window_start = current_time - timedelta(minutes=self.window_minutes * 2)
        
        for bucket_key in list(self.error_buckets.keys()):
            self.error_buckets[bucket_key] = [
                ts for ts in self.error_buckets[bucket_key]
                if ts >= window_start
            ]
            
            # Remove empty buckets
            if not self.error_buckets[bucket_key]:
                del self.error_buckets[bucket_key]
        
        self.last_cleanup = current_time


class ErrorMonitoringService:
    """
    Enhanced error monitoring service with alerting and recovery suggestions.
    """
    
    def __init__(self):
        self.aggregator = ErrorAggregator()
        self.active_alerts = {}
        self.alert_handlers = []
        self.recovery_strategies = {}
        self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self):
        """Setup automated recovery strategies for common errors."""
        self.recovery_strategies = {
            ErrorCategory.EXTERNAL_SERVICE: self._recover_external_service,
            ErrorCategory.DATABASE: self._recover_database,
            ErrorCategory.FILE_SYSTEM: self._recover_file_system,
            ErrorCategory.PROCESSING: self._recover_processing_error,
            ErrorCategory.NETWORK: self._recover_network_error
        }
    
    async def handle_error(
        self, 
        error: PKMException, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error with monitoring, alerting, and recovery attempts.
        
        Args:
            error: The error to handle
            context: Additional context information
            
        Returns:
            Dict containing handling results
        """
        handling_context = {
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "timestamp": error.timestamp,
            "context": context or {}
        }
        
        try:
            logger.info("Handling error", **handling_context)
            
            # Record error in global monitor
            error_monitor.record_error(error)
            
            # Check if we should alert
            should_alert = self.aggregator.should_alert(error)
            
            alert_sent = False
            if should_alert:
                alert = await self._create_alert(error, context)
                await self._send_alert(alert)
                alert_sent = True
            
            # Attempt automated recovery
            recovery_attempted = False
            recovery_successful = False
            
            if error.category in self.recovery_strategies:
                try:
                    recovery_result = await self.recovery_strategies[error.category](error, context)
                    recovery_attempted = True
                    recovery_successful = recovery_result.get("success", False)
                    
                    if recovery_successful:
                        logger.info("Automated recovery successful", **handling_context)
                    else:
                        logger.warning("Automated recovery failed", 
                                     recovery_result=recovery_result,
                                     **handling_context)
                        
                except Exception as recovery_error:
                    logger.error("Recovery strategy failed", 
                               recovery_error=str(recovery_error),
                               **handling_context)
            
            # Update service health if needed
            if error.category == ErrorCategory.EXTERNAL_SERVICE:
                service_name = error.details.get("service")
                if service_name:
                    service_health_monitor.clear_health_cache(service_name)
            
            return {
                "error_handled": True,
                "alert_sent": alert_sent,
                "recovery_attempted": recovery_attempted,
                "recovery_successful": recovery_successful,
                "handling_context": handling_context
            }
            
        except Exception as handling_error:
            logger.error("Error handling failed", 
                        handling_error=str(handling_error),
                        **handling_context)
            return {
                "error_handled": False,
                "handling_error": str(handling_error),
                "handling_context": handling_context
            }
    
    async def _create_alert(self, error: PKMException, context: Optional[Dict[str, Any]]) -> ErrorAlert:
        """Create an alert for the error."""
        # Determine alert level based on error severity
        if error.severity == ErrorSeverity.CRITICAL:
            level = AlertLevel.CRITICAL
        elif error.severity == ErrorSeverity.HIGH:
            level = AlertLevel.ERROR
        elif error.severity == ErrorSeverity.MEDIUM:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO
        
        # Create alert title and message
        title = f"{error.category.value.title()} Error: {error.error_code}"
        message = f"{error.user_message}\n\nTechnical details: {error.message}"
        
        # Add context information
        error_details = {
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "user_message": error.user_message,
            "details": error.details,
            "recovery_suggestions": error.recovery_suggestions,
            "context": context or {}
        }
        
        alert = ErrorAlert(
            alert_id=f"{error.error_code}_{int(time.time())}",
            level=level,
            title=title,
            message=message,
            error_details=error_details,
            service_affected=error.details.get("service"),
            timestamp=datetime.utcnow()
        )
        
        # Store active alert
        self.active_alerts[alert.alert_id] = alert
        
        return alert
    
    async def _send_alert(self, alert: ErrorAlert):
        """Send alert through configured channels."""
        try:
            # Log the alert
            logger.error(
                f"ALERT: {alert.title}",
                alert_id=alert.alert_id,
                level=alert.level.value,
                message=alert.message,
                service_affected=alert.service_affected,
                error_details=alert.error_details
            )
            
            # Send through registered alert handlers
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed", handler=str(handler), error=str(e))
            
        except Exception as e:
            logger.error(f"Failed to send alert", alert_id=alert.alert_id, error=str(e))
    
    async def _recover_external_service(self, error: PKMException, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to recover from external service errors."""
        service_name = error.details.get("service")
        
        if not service_name:
            return {"success": False, "reason": "No service name provided"}
        
        try:
            # Clear health cache to force fresh check
            service_health_monitor.clear_health_cache(service_name)
            
            # Wait a moment for service to potentially recover
            await asyncio.sleep(2)
            
            # Check if service is now available
            health_check = await service_health_monitor.check_service_health(service_name, force_check=True)
            
            if health_check.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                return {
                    "success": True,
                    "action": "service_recovered",
                    "service": service_name,
                    "health_status": health_check.status.value
                }
            
            return {
                "success": False,
                "reason": f"Service {service_name} still unhealthy",
                "health_status": health_check.status.value
            }
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _recover_database(self, error: PKMException, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to recover from database errors."""
        try:
            # Check database health
            health_check = await service_health_monitor.check_service_health("database", force_check=True)
            
            if health_check.status == ServiceStatus.HEALTHY:
                return {
                    "success": True,
                    "action": "database_recovered",
                    "health_status": health_check.status.value
                }
            
            return {
                "success": False,
                "reason": "Database still unhealthy",
                "health_status": health_check.status.value
            }
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _recover_file_system(self, error: PKMException, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to recover from file system errors."""
        try:
            # Check storage health
            health_check = await service_health_monitor.check_service_health("storage", force_check=True)
            
            if health_check.status == ServiceStatus.HEALTHY:
                return {
                    "success": True,
                    "action": "storage_recovered",
                    "health_status": health_check.status.value
                }
            
            # Try to create missing directories
            from app.core.config import settings
            import os
            
            directories_created = []
            for directory in [settings.UPLOAD_DIR, settings.PROCESSED_DIR, settings.RAG_STORAGE_DIR]:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory, exist_ok=True)
                        directories_created.append(directory)
                    except Exception as dir_error:
                        logger.warning(f"Failed to create directory {directory}: {dir_error}")
            
            if directories_created:
                return {
                    "success": True,
                    "action": "directories_created",
                    "directories": directories_created
                }
            
            return {"success": False, "reason": "Storage still unhealthy"}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _recover_processing_error(self, error: PKMException, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to recover from processing errors."""
        try:
            # Check if this is a temporary processing issue
            document_id = error.details.get("document_id")
            
            if document_id:
                # Could implement retry logic here
                return {
                    "success": False,
                    "reason": "Processing errors require manual intervention",
                    "suggestion": "Document can be reprocessed manually"
                }
            
            return {"success": False, "reason": "No recovery strategy for processing error"}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _recover_network_error(self, error: PKMException, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt to recover from network errors."""
        try:
            # Network errors usually resolve themselves
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "network_wait",
                "note": "Network errors often resolve automatically"
            }
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    def add_alert_handler(self, handler: Callable[[ErrorAlert], None]):
        """Add a custom alert handler."""
        self.alert_handlers.append(handler)
    
    def get_active_alerts(self) -> List[ErrorAlert]:
        """Get list of active alerts."""
        return list(self.active_alerts.values())
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].resolution_time = datetime.utcnow()
            return True
        return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        base_stats = error_monitor.get_error_stats()
        health_status = error_monitor.get_health_status()
        
        return {
            **base_stats,
            "system_health": health_status,
            "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
            "total_alerts": len(self.active_alerts),
            "alert_breakdown": {
                level.value: len([
                    a for a in self.active_alerts.values() 
                    if a.level == level and not a.resolved
                ])
                for level in AlertLevel
            }
        }


# Global instance
error_monitoring_service = ErrorMonitoringService()


# Example alert handler for logging
async def log_alert_handler(alert: ErrorAlert):
    """Example alert handler that logs alerts."""
    logger.error(
        f"ALERT HANDLER: {alert.title}",
        alert_id=alert.alert_id,
        level=alert.level.value,
        service_affected=alert.service_affected,
        timestamp=alert.timestamp.isoformat()
    )


# Register default alert handler
error_monitoring_service.add_alert_handler(log_alert_handler)