"""
Error handling and retry mechanisms for the atomic scraper tool.

Provides centralized error handling with categorized error types,
retry logic for recoverable errors, and graceful degradation strategies.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable, Union, Type
from dataclasses import dataclass
from enum import Enum

from atomic_scraper_tool.core.exceptions import (
    ScrapingError, NetworkError, ParsingError, ValidationError,
    ConfigurationError, RateLimitError, QualityError
)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    """Retry strategy types."""
    NONE = "none"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_errors: List[Type[Exception]] = None
    
    def __post_init__(self):
        """Set default retryable errors if not provided."""
        if self.retryable_errors is None:
            self.retryable_errors = [NetworkError, RateLimitError]


@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    url: Optional[str] = None
    attempt: int = 1
    max_attempts: int = 3
    start_time: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.start_time is None:
            self.start_time = time.time()
        if self.metadata is None:
            self.metadata = {}


class ErrorHandler:
    """
    Centralized error handling with retry logic and graceful degradation.
    
    Handles different types of scraping errors with appropriate retry strategies
    and provides mechanisms for partial data recovery.
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize error handler.
        
        Args:
            retry_config: Configuration for retry behavior
        """
        self.retry_config = retry_config or RetryConfig()
        self.logger = logging.getLogger(__name__)
        self._error_stats = {
            "total_errors": 0,
            "retried_errors": 0,
            "recovered_errors": 0,
            "failed_operations": 0
        }
    
    def handle_error(self, error: Exception, context: ErrorContext) -> bool:
        """
        Handle an error with appropriate strategy.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            bool: True if operation should be retried, False otherwise
        """
        self._error_stats["total_errors"] += 1
        
        # Log the error
        self._log_error(error, context)
        
        # Determine if error is retryable
        if not self._is_retryable(error, context):
            self.logger.info(f"Error not retryable: {error}")
            return False
        
        # Check if we've exceeded max attempts
        if context.attempt >= context.max_attempts:
            self.logger.warning(f"Max retry attempts ({context.max_attempts}) exceeded for {context.operation}")
            self._error_stats["failed_operations"] += 1
            return False
        
        # Calculate delay and retry
        delay = self._calculate_delay(context.attempt)
        self.logger.info(f"Retrying {context.operation} in {delay:.2f} seconds (attempt {context.attempt + 1}/{context.max_attempts})")
        
        time.sleep(delay)
        self._error_stats["retried_errors"] += 1
        return True
    
    async def handle_error_async(self, error: Exception, context: ErrorContext) -> bool:
        """
        Async version of handle_error.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            bool: True if operation should be retried, False otherwise
        """
        self._error_stats["total_errors"] += 1
        
        # Log the error
        self._log_error(error, context)
        
        # Determine if error is retryable
        if not self._is_retryable(error, context):
            self.logger.info(f"Error not retryable: {error}")
            return False
        
        # Check if we've exceeded max attempts
        if context.attempt >= context.max_attempts:
            self.logger.warning(f"Max retry attempts ({context.max_attempts}) exceeded for {context.operation}")
            self._error_stats["failed_operations"] += 1
            return False
        
        # Calculate delay and retry
        delay = self._calculate_delay(context.attempt)
        self.logger.info(f"Retrying {context.operation} in {delay:.2f} seconds (attempt {context.attempt + 1}/{context.max_attempts})")
        
        await asyncio.sleep(delay)
        self._error_stats["retried_errors"] += 1
        return True
    
    def handle_network_error(self, error: NetworkError, context: ErrorContext) -> bool:
        """
        Handle network-specific errors with specialized logic.
        
        Args:
            error: Network error that occurred
            context: Context information about the error
            
        Returns:
            bool: True if operation should be retried, False otherwise
        """
        # Handle rate limiting with special delay
        if isinstance(error, RateLimitError) and error.retry_after:
            delay = min(error.retry_after, self.retry_config.max_delay)
            self.logger.info(f"Rate limited, waiting {delay} seconds before retry")
            time.sleep(delay)
            return context.attempt < context.max_attempts
        
        # Handle HTTP status codes
        if hasattr(error, 'status_code') and error.status_code:
            if error.status_code in [429, 503, 502, 504]:  # Retryable status codes
                return self.handle_error(error, context)
            elif error.status_code in [404, 403, 401]:  # Non-retryable status codes
                self.logger.info(f"Non-retryable HTTP status {error.status_code}")
                return False
        
        return self.handle_error(error, context)
    
    def handle_parsing_error(self, error: ParsingError, context: ErrorContext) -> Optional[Dict[str, Any]]:
        """
        Handle parsing errors with partial data recovery.
        
        Args:
            error: Parsing error that occurred
            context: Context information about the error
            
        Returns:
            Optional[Dict[str, Any]]: Partial data if recoverable, None otherwise
        """
        self.logger.warning(f"Parsing error in {context.operation}: {error}")
        
        # Attempt to recover partial data
        partial_data = self._attempt_partial_recovery(error, context)
        
        if partial_data:
            self.logger.info(f"Recovered partial data: {len(partial_data)} items")
            self._error_stats["recovered_errors"] += 1
            return partial_data
        
        return None
    
    def handle_quality_error(self, error: QualityError, context: ErrorContext) -> bool:
        """
        Handle data quality errors with graceful degradation.
        
        Args:
            error: Quality error that occurred
            context: Context information about the error
            
        Returns:
            bool: True if item should be included despite quality issues
        """
        quality_score = error.quality_score
        threshold = error.threshold
        
        # Allow items with quality score above 30% of threshold
        min_acceptable = threshold * 0.3
        
        if quality_score >= min_acceptable:
            self.logger.warning(f"Including low-quality item (score: {quality_score:.2f}, threshold: {threshold:.2f})")
            return True
        
        self.logger.info(f"Rejecting item with quality score {quality_score:.2f} (below minimum {min_acceptable:.2f})")
        return False
    
    def with_retry(self, operation: Callable, context: ErrorContext, *args, **kwargs) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Function to execute
            context: Error context for the operation
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Any: Result of the operation
            
        Raises:
            Exception: Last exception if all retries failed
        """
        last_exception = None
        
        for attempt in range(1, context.max_attempts + 1):
            context.attempt = attempt
            
            try:
                result = operation(*args, **kwargs)
                if attempt > 1:
                    self.logger.info(f"Operation {context.operation} succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.handle_error(e, context):
                    break
        
        # All retries failed
        self.logger.error(f"Operation {context.operation} failed after {context.max_attempts} attempts")
        raise last_exception
    
    async def with_retry_async(self, operation: Callable, context: ErrorContext, *args, **kwargs) -> Any:
        """
        Async version of with_retry.
        
        Args:
            operation: Async function to execute
            context: Error context for the operation
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Any: Result of the operation
            
        Raises:
            Exception: Last exception if all retries failed
        """
        last_exception = None
        
        for attempt in range(1, context.max_attempts + 1):
            context.attempt = attempt
            
            try:
                result = await operation(*args, **kwargs)
                if attempt > 1:
                    self.logger.info(f"Operation {context.operation} succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                last_exception = e
                
                if not await self.handle_error_async(e, context):
                    break
        
        # All retries failed
        self.logger.error(f"Operation {context.operation} failed after {context.max_attempts} attempts")
        raise last_exception
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Get error handling statistics.
        
        Returns:
            Dict[str, int]: Error statistics
        """
        return self._error_stats.copy()
    
    def reset_stats(self):
        """Reset error statistics."""
        self._error_stats = {
            "total_errors": 0,
            "retried_errors": 0,
            "recovered_errors": 0,
            "failed_operations": 0
        }
    
    def _is_retryable(self, error: Exception, context: ErrorContext) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The exception to check
            context: Error context
            
        Returns:
            bool: True if error is retryable
        """
        # Check if error type is in retryable list
        for retryable_type in self.retry_config.retryable_errors:
            if isinstance(error, retryable_type):
                return True
        
        # Special cases for specific error types
        if isinstance(error, NetworkError):
            # Retry network errors except for authentication/authorization
            if hasattr(error, 'status_code') and error.status_code in [401, 403]:
                return False
            return True
        
        if isinstance(error, RateLimitError):
            return True
        elif isinstance(error, NetworkError):
            # Don't retry client errors (4xx status codes)
            if hasattr(error, 'status_code') and error.status_code and 400 <= error.status_code < 500:
                return False
            return True
        
        # Don't retry configuration or validation errors
        if isinstance(error, (ConfigurationError, ValidationError)):
            return False
        
        return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            float: Delay in seconds
        """
        if self.retry_config.strategy == RetryStrategy.NONE:
            return 0.0
        
        elif self.retry_config.strategy == RetryStrategy.FIXED_DELAY:
            return self.retry_config.base_delay
        
        elif self.retry_config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.retry_config.base_delay * attempt
        
        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.retry_config.base_delay * (self.retry_config.backoff_multiplier ** (attempt - 1))
        
        else:
            delay = self.retry_config.base_delay
        
        return min(delay, self.retry_config.max_delay)
    
    def _log_error(self, error: Exception, context: ErrorContext):
        """
        Log error with appropriate level and context.
        
        Args:
            error: The exception to log
            context: Error context
        """
        severity = self._get_error_severity(error)
        
        log_message = f"Error in {context.operation} (attempt {context.attempt}/{context.max_attempts}): {error}"
        
        if context.url:
            log_message += f" [URL: {context.url}]"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _get_error_severity(self, error: Exception) -> ErrorSeverity:
        """
        Determine error severity level.
        
        Args:
            error: The exception to evaluate
            
        Returns:
            ErrorSeverity: Severity level
        """
        if isinstance(error, ConfigurationError):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, NetworkError) and hasattr(error, 'status_code'):
            if error.status_code in [500, 502, 503, 504]:
                return ErrorSeverity.HIGH
            elif error.status_code in [401, 403, 404]:
                return ErrorSeverity.MEDIUM
        elif isinstance(error, (ParsingError, QualityError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, RateLimitError):
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _attempt_partial_recovery(self, error: ParsingError, context: ErrorContext) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover partial data from parsing errors.
        
        Args:
            error: Parsing error that occurred
            context: Error context
            
        Returns:
            Optional[Dict[str, Any]]: Partial data if recoverable
        """
        # This is a placeholder for partial recovery logic
        # In a real implementation, this would attempt to extract
        # whatever data is available despite the parsing error
        
        self.logger.info(f"Attempting partial recovery for parsing error: {error}")
        
        # Example recovery strategies:
        # 1. Try alternative selectors
        # 2. Extract text content even if structure is malformed
        # 3. Return whatever fields were successfully parsed
        
        # For now, return None to indicate no recovery possible
        # This would be implemented based on specific parsing logic
        return None