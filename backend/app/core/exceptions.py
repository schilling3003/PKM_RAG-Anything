"""
Custom exception classes and error handlers.
"""

from typing import Any, Dict, Optional, List
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
import structlog
from datetime import datetime
from enum import Enum

logger = structlog.get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for better classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    PROCESSING = "processing"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    INTERNAL = "internal"


class PKMException(Exception):
    """Base exception for PKM application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.category = category
        self.severity = severity
        self.user_message = user_message or message
        self.recovery_suggestions = recovery_suggestions or []
        self.error_code = error_code or f"{category.value.upper()}_{status_code}"
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "status_code": self.status_code,
            "timestamp": self.timestamp,
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions
        }


class DocumentProcessingError(PKMException):
    """Exception raised during document processing."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message or "Failed to process document. Please check the file format and try again.",
            recovery_suggestions=recovery_suggestions or [
                "Verify the document format is supported (PDF, DOCX, TXT, etc.)",
                "Check if the file is corrupted or password-protected",
                "Try uploading a smaller file if the document is very large",
                "Contact support if the issue persists"
            ]
        )


class SearchError(PKMException):
    """Exception raised during search operations."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.LOW,
            user_message=user_message or "Search operation failed. Please try a different query.",
            recovery_suggestions=recovery_suggestions or [
                "Try using different keywords or phrases",
                "Check your spelling and try again",
                "Use more specific or more general search terms",
                "Ensure your knowledge base contains relevant content"
            ]
        )


class DatabaseError(PKMException):
    """Exception raised during database operations."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            user_message=user_message or "A database error occurred. Please try again later.",
            recovery_suggestions=recovery_suggestions or [
                "Wait a moment and try the operation again",
                "Check if the system is under maintenance",
                "Restart the application if you have admin access",
                "Contact support if the problem persists"
            ]
        )


class NotFoundError(PKMException):
    """Exception raised when resource is not found."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            user_message=user_message or "The requested resource was not found.",
            recovery_suggestions=recovery_suggestions or [
                "Check if the resource ID or name is correct",
                "Verify the resource hasn't been deleted",
                "Try refreshing the page or reloading the data",
                "Use the search function to find similar resources"
            ]
        )


class ValidationError(PKMException):
    """Exception raised when validation fails."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            user_message=user_message or "The provided data is invalid. Please check your input.",
            recovery_suggestions=recovery_suggestions or [
                "Review the highlighted fields and correct any errors",
                "Ensure all required fields are filled out",
                "Check that data formats match the expected patterns",
                "Refer to the documentation for valid input examples"
            ]
        )


class KnowledgeGraphError(PKMException):
    """Exception raised during knowledge graph operations."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message or "Knowledge graph operation failed. Please try again.",
            recovery_suggestions=recovery_suggestions or [
                "Wait for any ongoing document processing to complete",
                "Try refreshing the knowledge graph view",
                "Check if there's sufficient processed content",
                "Contact support if the graph consistently fails to load"
            ]
        )


class FileStorageError(PKMException):
    """Exception raised during file storage operations."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.HIGH,
            user_message=user_message or "File storage operation failed. Please try again.",
            recovery_suggestions=recovery_suggestions or [
                "Check if there's sufficient disk space available",
                "Verify file permissions are correctly set",
                "Try uploading a smaller file",
                "Contact administrator if storage issues persist"
            ]
        )


class RateLimitError(PKMException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={**(details or {}), "retry_after": retry_after},
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            user_message="Too many requests. Please wait before trying again.",
            recovery_suggestions=[
                f"Wait {retry_after} seconds before retrying" if retry_after else "Wait a moment before retrying",
                "Reduce the frequency of your requests",
                "Consider batching multiple operations together"
            ]
        )


class ExternalServiceError(PKMException):
    """Exception raised when external services fail."""
    
    def __init__(
        self, 
        message: str, 
        service_name: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={**(details or {}), "service": service_name},
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message or f"External service ({service_name}) is currently unavailable.",
            recovery_suggestions=[
                "Wait a few minutes and try again",
                "Check if the external service is experiencing issues",
                "Try using alternative features if available",
                "Contact support if the service remains unavailable"
            ]
        )


class ConfigurationError(PKMException):
    """Exception raised when configuration is invalid."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**(details or {}), "config_key": config_key},
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            user_message="System configuration error. Please contact administrator.",
            recovery_suggestions=[
                "Contact system administrator",
                "Check system configuration files",
                "Restart the application if you have admin access"
            ]
        )


class AuthenticationError(PKMException):
    """Exception raised when authentication fails."""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Authentication required. Please log in.",
            recovery_suggestions=[
                "Check your credentials and try again",
                "Clear browser cache and cookies",
                "Contact support if you've forgotten your password"
            ]
        )


class AuthorizationError(PKMException):
    """Exception raised when authorization fails."""
    
    def __init__(
        self, 
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details={**(details or {}), "required_permission": required_permission},
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="You don't have permission to perform this action.",
            recovery_suggestions=[
                "Contact administrator to request access",
                "Check if you're logged in with the correct account",
                "Verify your account has the necessary permissions"
            ]
        )


class ConflictError(PKMException):
    """Exception raised when there's a resource conflict."""
    
    def __init__(
        self, 
        message: str,
        conflicting_resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details={**(details or {}), "conflicting_resource": conflicting_resource},
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            user_message="The operation conflicts with existing data.",
            recovery_suggestions=[
                "Check if the resource already exists",
                "Try using a different name or identifier",
                "Refresh the page to see current data",
                "Contact support if the conflict persists"
            ]
        )


class ErrorMonitor:
    """Error monitoring and metrics collection."""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
        self.max_history_size = 1000
    
    def record_error(self, exception: PKMException, request: Request = None):
        """Record error occurrence for monitoring."""
        error_key = f"{exception.category.value}:{exception.error_code}"
        
        # Update error counts
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Add to history
        error_record = {
            "timestamp": exception.timestamp,
            "error_code": exception.error_code,
            "category": exception.category.value,
            "severity": exception.severity.value,
            "message": exception.message,
            "status_code": exception.status_code,
            "request_id": getattr(request.state, 'request_id', None) if request else None,
            "url": str(request.url) if request else None,
            "method": request.method if request else None,
            "user_agent": request.headers.get("user-agent") if request else None
        }
        
        self.error_history.append(error_record)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        
        # Log structured error data
        logger.error(
            "Error recorded",
            error_code=exception.error_code,
            category=exception.category.value,
            severity=exception.severity.value,
            message=exception.message,
            details=exception.details,
            request_id=error_record["request_id"],
            url=error_record["url"]
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = sum(self.error_counts.values())
        
        # Calculate error rates by category
        category_counts = {}
        severity_counts = {}
        
        for error_record in self.error_history:
            category = error_record["category"]
            severity = error_record["severity"]
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": total_errors,
            "unique_error_types": len(self.error_counts),
            "error_counts": self.error_counts,
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "recent_errors": self.error_history[-10:] if self.error_history else []
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health based on error patterns."""
        stats = self.get_error_stats()
        
        # Determine health status based on error patterns
        critical_errors = stats["severity_distribution"].get("critical", 0)
        high_errors = stats["severity_distribution"].get("high", 0)
        total_errors = stats["total_errors"]
        
        if critical_errors > 0:
            health_status = "critical"
        elif high_errors > 5:
            health_status = "degraded"
        elif total_errors > 50:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "total_errors": total_errors,
            "critical_errors": critical_errors,
            "high_severity_errors": high_errors,
            "recommendations": self._get_health_recommendations(health_status, stats)
        }
    
    def _get_health_recommendations(self, status: str, stats: Dict[str, Any]) -> List[str]:
        """Get health recommendations based on error patterns."""
        recommendations = []
        
        if status == "critical":
            recommendations.append("Immediate attention required - critical errors detected")
            recommendations.append("Check system logs for detailed error information")
            recommendations.append("Consider restarting affected services")
        
        elif status == "degraded":
            recommendations.append("System performance may be impacted")
            recommendations.append("Monitor error patterns closely")
            recommendations.append("Consider scaling resources if needed")
        
        elif status == "warning":
            recommendations.append("Elevated error rate detected")
            recommendations.append("Review recent changes or deployments")
            recommendations.append("Monitor system resources")
        
        # Category-specific recommendations
        category_counts = stats.get("category_distribution", {})
        
        if category_counts.get("database", 0) > 5:
            recommendations.append("High database error rate - check database health")
        
        if category_counts.get("external_service", 0) > 3:
            recommendations.append("External service issues detected - verify service status")
        
        if category_counts.get("file_system", 0) > 2:
            recommendations.append("File system errors - check disk space and permissions")
        
        return recommendations


# Global error monitor instance
error_monitor = ErrorMonitor()


async def pkm_exception_handler(request: Request, exc: PKMException) -> JSONResponse:
    """Handle custom PKM exceptions with enhanced monitoring."""
    # Record error for monitoring
    error_monitor.record_error(exc, request)
    
    # Enhanced error handling with monitoring service
    request_context = {
        "request_id": getattr(request.state, 'request_id', None),
        "url": str(request.url),
        "method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "client_ip": request.client.host if request.client else None
    }
    
    # Handle error through monitoring service
    try:
        from app.core.error_monitoring import error_monitoring_service
        handling_result = await error_monitoring_service.handle_error(exc, request_context)
        
        # Add handling info to response in development
        import os
        if os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev"]:
            request_context["error_handling"] = handling_result
            
    except Exception as monitoring_error:
        logger.error(
            "Error monitoring service failed",
            monitoring_error=str(monitoring_error),
            original_error=exc.error_code
        )
    
    # Log error with structured data
    logger.error(
        "PKM Exception occurred",
        error_code=exc.error_code,
        category=exc.category.value,
        severity=exc.severity.value,
        message=exc.message,
        user_message=exc.user_message,
        status_code=exc.status_code,
        details=exc.details,
        request_context=request_context,
        traceback=traceback.format_exc() if exc.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
    )
    
    # Return user-friendly error response
    response_content = {
        "error": exc.to_dict(),
        "request_id": request_context.get("request_id"),
        "timestamp": exc.timestamp
    }
    
    # Add debug information in development
    import os
    if os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev"]:
        response_content["debug"] = {
            "exception_type": exc.__class__.__name__,
            "traceback": traceback.format_exc(),
            "request_context": request_context
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    # Convert to PKM exception for consistent handling
    if exc.status_code == 404:
        pkm_exc = NotFoundError(
            message=str(exc.detail),
            user_message="The requested page or resource was not found."
        )
    elif exc.status_code == 405:
        pkm_exc = ValidationError(
            message=f"Method {request.method} not allowed",
            user_message="This action is not supported for this resource."
        )
    elif exc.status_code == 500:
        pkm_exc = PKMException(
            message=str(exc.detail),
            status_code=exc.status_code,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            user_message="An internal server error occurred."
        )
    else:
        pkm_exc = PKMException(
            message=str(exc.detail),
            status_code=exc.status_code,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            user_message=str(exc.detail)
        )
    
    return await pkm_exception_handler(request, pkm_exc)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    # Format validation errors for better user experience
    formatted_errors = []
    field_errors = {}
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_msg = error["msg"]
        error_type = error["type"]
        
        formatted_errors.append({
            "field": field_path,
            "message": error_msg,
            "type": error_type,
            "input": error.get("input")
        })
        
        field_errors[field_path] = error_msg
    
    # Create user-friendly message
    if len(formatted_errors) == 1:
        user_message = f"Invalid {formatted_errors[0]['field']}: {formatted_errors[0]['message']}"
    else:
        user_message = f"Validation failed for {len(formatted_errors)} fields. Please check your input."
    
    # Convert to PKM exception
    pkm_exc = ValidationError(
        message="Request validation failed",
        details={
            "validation_errors": formatted_errors,
            "field_errors": field_errors
        },
        user_message=user_message,
        recovery_suggestions=[
            "Check the highlighted fields for errors",
            "Ensure all required fields are provided",
            "Verify data types match the expected format",
            "Refer to API documentation for valid input examples"
        ]
    )
    
    return await pkm_exception_handler(request, pkm_exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    # Create PKM exception for unexpected errors
    pkm_exc = PKMException(
        message=f"Unexpected error: {str(exc)}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.CRITICAL,
        user_message="An unexpected error occurred. Our team has been notified.",
        recovery_suggestions=[
            "Try refreshing the page",
            "Wait a moment and try again",
            "Contact support if the problem persists",
            "Check if the system is under maintenance"
        ],
        details={
            "exception_type": exc.__class__.__name__,
            "exception_module": exc.__class__.__module__,
            "traceback": traceback.format_exc()
        }
    )
    
    return await pkm_exception_handler(request, pkm_exc)