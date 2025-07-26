"""
Retry utilities for handling transient failures.
"""

import asyncio
import functools
import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime, timedelta
import structlog
import redis

from app.core.exceptions import ExternalServiceError, DatabaseError, FileStorageError
from app.core.service_health import service_health_monitor

logger = structlog.get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        max_backoff: float = 60.0,
        jitter: bool = True,
        exponential: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self.jitter = jitter
        self.exponential = exponential
        self.retryable_exceptions = retryable_exceptions or [
            ConnectionError,
            TimeoutError,
            ExternalServiceError,
            DatabaseError,
            FileStorageError
        ]


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    backoff_factor: float = 1.5,
    max_backoff: float = 60.0,
    jitter: bool = True,
    exponential: bool = True
) -> float:
    """
    Calculate backoff delay for retry attempts.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        backoff_factor: Multiplier for exponential backoff
        max_backoff: Maximum delay in seconds
        jitter: Add random jitter to prevent thundering herd
        exponential: Use exponential backoff vs linear
        
    Returns:
        Delay in seconds
    """
    if exponential:
        delay = base_delay * (backoff_factor ** attempt)
    else:
        delay = base_delay + (backoff_factor * attempt)
    
    # Cap at max_backoff
    delay = min(delay, max_backoff)
    
    # Add jitter to prevent thundering herd
    if jitter:
        jitter_range = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    service_name: Optional[str] = None,
    operation_name: Optional[str] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration
        service_name: Name of the service being called (for health checks)
        operation_name: Name of the operation being performed
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    # Check service health before retry (except first attempt)
                    if attempt > 0 and service_name:
                        try:
                            await service_health_monitor.ensure_service_available(
                                service_name, operation_name
                            )
                        except ExternalServiceError as e:
                            # If service is still unhealthy, don't retry
                            logger.warning(
                                f"Service {service_name} still unhealthy, aborting retry",
                                attempt=attempt,
                                operation=operation_name
                            )
                            raise e
                    
                    # Attempt the operation
                    result = await func(*args, **kwargs)
                    
                    # Log successful retry
                    if attempt > 0:
                        logger.info(
                            f"Operation succeeded after retry",
                            function=func.__name__,
                            attempt=attempt,
                            service=service_name,
                            operation=operation_name
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.info(
                            f"Non-retryable exception, not retrying",
                            function=func.__name__,
                            exception=str(e),
                            exception_type=type(e).__name__
                        )
                        raise e
                    
                    # Don't retry on last attempt
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries exceeded",
                            function=func.__name__,
                            max_retries=config.max_retries,
                            service=service_name,
                            operation=operation_name,
                            final_error=str(e)
                        )
                        break
                    
                    # Calculate delay
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        backoff_factor=config.backoff_factor,
                        max_backoff=config.max_backoff,
                        jitter=config.jitter,
                        exponential=config.exponential
                    )
                    
                    logger.warning(
                        f"Operation failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=config.max_retries,
                        delay=delay,
                        service=service_name,
                        operation=operation_name,
                        error=str(e)
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # All retries exhausted
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    # Attempt the operation
                    result = func(*args, **kwargs)
                    
                    # Log successful retry
                    if attempt > 0:
                        logger.info(
                            f"Operation succeeded after retry",
                            function=func.__name__,
                            attempt=attempt,
                            service=service_name,
                            operation=operation_name
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.info(
                            f"Non-retryable exception, not retrying",
                            function=func.__name__,
                            exception=str(e),
                            exception_type=type(e).__name__
                        )
                        raise e
                    
                    # Don't retry on last attempt
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries exceeded",
                            function=func.__name__,
                            max_retries=config.max_retries,
                            service=service_name,
                            operation=operation_name,
                            final_error=str(e)
                        )
                        break
                    
                    # Calculate delay
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        backoff_factor=config.backoff_factor,
                        max_backoff=config.max_backoff,
                        jitter=config.jitter,
                        exponential=config.exponential
                    )
                    
                    logger.warning(
                        f"Operation failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=config.max_retries,
                        delay=delay,
                        service=service_name,
                        operation=operation_name,
                        error=str(e)
                    )
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # All retries exhausted
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                    logger.info(f"Circuit breaker half-open for {func.__name__}")
                else:
                    raise ExternalServiceError(
                        message=f"Circuit breaker is open for {func.__name__}",
                        service_name=getattr(func, '__service_name__', 'unknown'),
                        user_message="Service is temporarily unavailable due to repeated failures"
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                    logger.info(f"Circuit breaker half-open for {func.__name__}")
                else:
                    raise ExternalServiceError(
                        message=f"Circuit breaker is open for {func.__name__}",
                        service_name=getattr(func, '__service_name__', 'unknown'),
                        user_message="Service is temporarily unavailable due to repeated failures"
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "closed"
        logger.info("Circuit breaker reset to closed state")
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )


def with_graceful_degradation(
    fallback_func: Optional[Callable] = None,
    fallback_value: Any = None,
    service_name: Optional[str] = None
):
    """
    Decorator for graceful degradation when services are unavailable.
    
    Args:
        fallback_func: Function to call as fallback
        fallback_value: Static value to return as fallback
        service_name: Name of the service for logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except (ExternalServiceError, ConnectionError, TimeoutError) as e:
                logger.warning(
                    f"Service degradation triggered",
                    function=func.__name__,
                    service=service_name,
                    error=str(e)
                )
                
                if fallback_func:
                    try:
                        if asyncio.iscoroutinefunction(fallback_func):
                            return await fallback_func(*args, **kwargs)
                        else:
                            return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback function failed",
                            function=func.__name__,
                            fallback_error=str(fallback_error)
                        )
                        raise e
                
                return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except (ExternalServiceError, ConnectionError, TimeoutError) as e:
                logger.warning(
                    f"Service degradation triggered",
                    function=func.__name__,
                    service=service_name,
                    error=str(e)
                )
                
                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback function failed",
                            function=func.__name__,
                            fallback_error=str(fallback_error)
                        )
                        raise e
                
                return fallback_value
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Predefined retry configurations for common services
REDIS_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    backoff_factor=1.5,
    max_backoff=10.0,
    retryable_exceptions=[ConnectionError, TimeoutError, redis.RedisError]
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    backoff_factor=2.0,
    max_backoff=15.0,
    retryable_exceptions=[DatabaseError, ConnectionError]
)

OPENAI_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    backoff_factor=2.0,
    max_backoff=30.0,
    retryable_exceptions=[ExternalServiceError, ConnectionError, TimeoutError]
)

FILE_STORAGE_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    backoff_factor=1.0,
    max_backoff=5.0,
    retryable_exceptions=[FileStorageError, OSError, IOError]
)


# Convenience decorators
def retry_redis_operation(operation_name: str = None):
    """Retry decorator specifically for Redis operations."""
    return retry_with_backoff(
        config=REDIS_RETRY_CONFIG,
        service_name="redis",
        operation_name=operation_name
    )


def retry_database_operation(operation_name: str = None):
    """Retry decorator specifically for database operations."""
    return retry_with_backoff(
        config=DATABASE_RETRY_CONFIG,
        service_name="database",
        operation_name=operation_name
    )


def retry_openai_operation(operation_name: str = None):
    """Retry decorator specifically for OpenAI API operations."""
    return retry_with_backoff(
        config=OPENAI_RETRY_CONFIG,
        service_name="openai",
        operation_name=operation_name
    )


def retry_file_operation(operation_name: str = None):
    """Retry decorator specifically for file operations."""
    return retry_with_backoff(
        config=FILE_STORAGE_RETRY_CONFIG,
        service_name="storage",
        operation_name=operation_name
    )