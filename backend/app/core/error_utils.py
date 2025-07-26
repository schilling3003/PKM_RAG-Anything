"""
Error handling utilities and context helpers.
"""

from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import asyncio
import time

from app.core.exceptions import (
    PKMException, 
    DatabaseError, 
    FileStorageError, 
    ExternalServiceError,
    ErrorSeverity,
    ErrorCategory
)


class ErrorContext:
    """Context manager for error handling with automatic recovery suggestions."""
    
    def __init__(
        self,
        operation: str,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        self.operation = operation
        self.category = category
        self.severity = severity
        self.user_message = user_message
        self.recovery_suggestions = recovery_suggestions or []
        self.start_time = None
        self.context_data = {}
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not isinstance(exc_val, PKMException):
            # Convert generic exceptions to PKM exceptions
            duration = time.time() - self.start_time if self.start_time else 0
            
            # Add operation context to details
            details = {
                "operation": self.operation,
                "duration_seconds": round(duration, 3),
                "original_exception": str(exc_val),
                "exception_type": exc_type.__name__,
                **self.context_data
            }
            
            # Create appropriate PKM exception
            if "database" in self.operation.lower() or "db" in self.operation.lower():
                raise DatabaseError(
                    message=f"Database operation failed: {self.operation}",
                    details=details,
                    user_message=self.user_message or "Database operation failed. Please try again.",
                    recovery_suggestions=self.recovery_suggestions or [
                        "Wait a moment and try again",
                        "Check if the database is accessible",
                        "Contact support if the issue persists"
                    ]
                ) from exc_val
            
            elif "file" in self.operation.lower() or "storage" in self.operation.lower():
                raise FileStorageError(
                    message=f"File operation failed: {self.operation}",
                    details=details,
                    user_message=self.user_message or "File operation failed. Please try again.",
                    recovery_suggestions=self.recovery_suggestions or [
                        "Check if the file exists and is accessible",
                        "Verify sufficient disk space is available",
                        "Ensure proper file permissions",
                        "Try with a different file if applicable"
                    ]
                ) from exc_val
            
            else:
                raise PKMException(
                    message=f"Operation failed: {self.operation}",
                    details=details,
                    category=self.category,
                    severity=self.severity,
                    user_message=self.user_message or f"Operation '{self.operation}' failed. Please try again.",
                    recovery_suggestions=self.recovery_suggestions or [
                        "Try the operation again",
                        "Check your input and try again",
                        "Contact support if the issue persists"
                    ]
                ) from exc_val
        
        return False  # Don't suppress exceptions
    
    def add_context(self, key: str, value: Any):
        """Add context data to the error."""
        self.context_data[key] = value


def handle_errors(
    operation: str,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: Optional[str] = None,
    recovery_suggestions: Optional[List[str]] = None
):
    """Decorator for automatic error handling."""
    
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with ErrorContext(
                    operation=operation,
                    category=category,
                    severity=severity,
                    user_message=user_message,
                    recovery_suggestions=recovery_suggestions
                ) as ctx:
                    # Add function context
                    ctx.add_context("function", func.__name__)
                    ctx.add_context("module", func.__module__)
                    ctx.add_context("args_count", len(args))
                    ctx.add_context("kwargs_keys", list(kwargs.keys()))
                    
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with ErrorContext(
                    operation=operation,
                    category=category,
                    severity=severity,
                    user_message=user_message,
                    recovery_suggestions=recovery_suggestions
                ) as ctx:
                    # Add function context
                    ctx.add_context("function", func.__name__)
                    ctx.add_context("module", func.__module__)
                    ctx.add_context("args_count", len(args))
                    ctx.add_context("kwargs_keys", list(kwargs.keys()))
                    
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


class RetryHandler:
    """Handler for automatic retry logic with exponential backoff."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[List[type]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or [
            DatabaseError,
            ExternalServiceError,
            FileStorageError
        ]
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should trigger a retry."""
        if attempt >= self.max_attempts:
            return False
        
        # Check if exception type is retryable
        if not any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions):
            return False
        
        # Check if PKM exception has appropriate severity
        if isinstance(exception, PKMException):
            return exception.severity not in [ErrorSeverity.CRITICAL]
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    raise
                
                if attempt < self.max_attempts:
                    delay = self.get_delay(attempt)
                    await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        if isinstance(last_exception, PKMException):
            # Add retry information to the exception
            last_exception.details["retry_attempts"] = self.max_attempts
            last_exception.recovery_suggestions.insert(0, 
                f"Operation failed after {self.max_attempts} attempts")
        
        raise last_exception


def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: Optional[List[type]] = None
):
    """Decorator for automatic retry functionality."""
    
    def decorator(func: Callable):
        retry_handler = RetryHandler(
            max_attempts=max_attempts,
            base_delay=base_delay,
            retryable_exceptions=retryable_exceptions
        )
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_handler.execute_with_retry(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(retry_handler.execute_with_retry(func, *args, **kwargs))
            return sync_wrapper
    
    return decorator


class ErrorBoundary:
    """Context manager that provides error boundaries with fallback values."""
    
    def __init__(
        self,
        operation: str,
        fallback_value: Any = None,
        suppress_errors: bool = False
    ):
        self.operation = operation
        self.fallback_value = fallback_value
        self.suppress_errors = suppress_errors
        self.result = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        if isinstance(exc_val, PKMException):
            if not self.suppress_errors:
                return False  # Re-raise the exception
            self.result = self.fallback_value
            return True  # Suppress the exception
        
        if not self.suppress_errors:
            # Convert to PKM exception
            raise PKMException(
                message=f"Error in {self.operation}: {str(exc_val)}",
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.MEDIUM,
                user_message=f"An error occurred during {self.operation}. Please try again.",
                details={"original_error": str(exc_val), "operation": self.operation}
            ) from exc_val
        
        self.result = self.fallback_value
        return True  # Suppress the exception


class ErrorRecoveryHelper:
    """Helper class for generating context-aware recovery suggestions."""
    
    @staticmethod
    def get_suggestions_for_operation(operation: str, error_type: type) -> List[str]:
        """Get recovery suggestions based on operation and error type."""
        base_suggestions = []
        
        # Operation-specific suggestions
        if "upload" in operation.lower():
            base_suggestions.extend([
                "Check if the file format is supported",
                "Verify the file is not corrupted",
                "Try uploading a smaller file",
                "Ensure stable internet connection"
            ])
        
        elif "search" in operation.lower():
            base_suggestions.extend([
                "Try different search terms",
                "Check spelling and try again",
                "Use more specific or general keywords",
                "Ensure your knowledge base has content"
            ])
        
        elif "process" in operation.lower():
            base_suggestions.extend([
                "Wait for current processing to complete",
                "Check if the input data is valid",
                "Try processing smaller batches",
                "Verify system resources are available"
            ])
        
        # Error type-specific suggestions
        if error_type == DatabaseError:
            base_suggestions.extend([
                "Check database connectivity",
                "Verify database permissions",
                "Wait for database maintenance to complete"
            ])
        
        elif error_type == FileStorageError:
            base_suggestions.extend([
                "Check available disk space",
                "Verify file system permissions",
                "Try a different storage location"
            ])
        
        elif error_type == ExternalServiceError:
            base_suggestions.extend([
                "Check external service status",
                "Verify API credentials",
                "Try again after service recovery"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in base_suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions