"""
Unit tests for the error handler module.

Tests error handling, retry mechanisms, and graceful degradation.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from atomic_scraper_tool.core.error_handler import (
    ErrorHandler, ErrorContext, RetryConfig, RetryStrategy, ErrorSeverity
)
from atomic_scraper_tool.core.exceptions import (
    ScrapingError, NetworkError, ParsingError, ValidationError,
    ConfigurationError, RateLimitError, QualityError
)


class TestRetryConfig:
    """Test RetryConfig dataclass."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_multiplier == 2.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert NetworkError in config.retryable_errors
        assert RateLimitError in config.retryable_errors
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            strategy=RetryStrategy.FIXED_DELAY,
            retryable_errors=[NetworkError]
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.strategy == RetryStrategy.FIXED_DELAY
        assert config.retryable_errors == [NetworkError]


class TestErrorContext:
    """Test ErrorContext dataclass."""
    
    def test_default_context(self):
        """Test default error context."""
        context = ErrorContext(operation="test_operation")
        
        assert context.operation == "test_operation"
        assert context.url is None
        assert context.attempt == 1
        assert context.max_attempts == 3
        assert context.start_time is not None
        assert context.metadata == {}
    
    def test_custom_context(self):
        """Test custom error context."""
        metadata = {"key": "value"}
        context = ErrorContext(
            operation="custom_op",
            url="https://example.com",
            attempt=2,
            max_attempts=5,
            metadata=metadata
        )
        
        assert context.operation == "custom_op"
        assert context.url == "https://example.com"
        assert context.attempt == 2
        assert context.max_attempts == 5
        assert context.metadata == metadata


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
        self.context = ErrorContext(operation="test_operation", max_attempts=3)
    
    def test_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler()
        assert handler.retry_config is not None
        assert handler._error_stats["total_errors"] == 0
        
        custom_config = RetryConfig(max_attempts=5)
        handler_custom = ErrorHandler(custom_config)
        assert handler_custom.retry_config.max_attempts == 5
    
    def test_handle_retryable_error(self):
        """Test handling of retryable errors."""
        error = NetworkError("Connection failed", "https://example.com")
        
        # First attempt should be retryable
        with patch('time.sleep'):
            result = self.handler.handle_error(error, self.context)
        
        assert result is True
        assert self.handler._error_stats["total_errors"] == 1
        assert self.handler._error_stats["retried_errors"] == 1
    
    def test_handle_non_retryable_error(self):
        """Test handling of non-retryable errors."""
        error = ConfigurationError("Invalid config")
        
        result = self.handler.handle_error(error, self.context)
        
        assert result is False
        assert self.handler._error_stats["total_errors"] == 1
        assert self.handler._error_stats["retried_errors"] == 0
    
    def test_max_attempts_exceeded(self):
        """Test behavior when max attempts are exceeded."""
        error = NetworkError("Connection failed")
        self.context.attempt = 3  # At max attempts
        
        result = self.handler.handle_error(error, self.context)
        
        assert result is False
        assert self.handler._error_stats["failed_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_handle_error_async(self):
        """Test async error handling."""
        error = NetworkError("Connection failed")
        
        with patch('asyncio.sleep'):
            result = await self.handler.handle_error_async(error, self.context)
        
        assert result is True
        assert self.handler._error_stats["retried_errors"] == 1
    
    def test_handle_network_error_with_rate_limit(self):
        """Test handling network error with rate limiting."""
        error = RateLimitError("Rate limited", retry_after=5)
        
        with patch('time.sleep') as mock_sleep:
            result = self.handler.handle_network_error(error, self.context)
        
        assert result is True
        mock_sleep.assert_called_with(5)
    
    def test_handle_network_error_non_retryable_status(self):
        """Test handling network error with non-retryable status code."""
        error = NetworkError("Unauthorized", status_code=401)
        
        result = self.handler.handle_network_error(error, self.context)
        
        assert result is False
    
    def test_handle_parsing_error_no_recovery(self):
        """Test handling parsing error with no recovery."""
        error = ParsingError("Invalid HTML", selector=".content")
        
        result = self.handler.handle_parsing_error(error, self.context)
        
        assert result is None
        assert self.handler._error_stats["total_errors"] == 0  # Not counted as error in this method
    
    def test_handle_quality_error_acceptable(self):
        """Test handling quality error with acceptable score."""
        error = QualityError("Low quality", quality_score=40.0, threshold=100.0)
        
        result = self.handler.handle_quality_error(error, self.context)
        
        assert result is True  # 40 > 30% of 100
    
    def test_handle_quality_error_unacceptable(self):
        """Test handling quality error with unacceptable score."""
        error = QualityError("Very low quality", quality_score=10.0, threshold=100.0)
        
        result = self.handler.handle_quality_error(error, self.context)
        
        assert result is False  # 10 < 30% of 100
    
    def test_with_retry_success_first_attempt(self):
        """Test with_retry when operation succeeds on first attempt."""
        mock_operation = Mock(return_value="success")
        
        result = self.handler.with_retry(mock_operation, self.context, "arg1", key="value")
        
        assert result == "success"
        mock_operation.assert_called_once_with("arg1", key="value")
    
    def test_with_retry_success_after_retry(self):
        """Test with_retry when operation succeeds after retry."""
        mock_operation = Mock(side_effect=[NetworkError("Failed"), "success"])
        
        with patch('time.sleep'):
            result = self.handler.with_retry(mock_operation, self.context)
        
        assert result == "success"
        assert mock_operation.call_count == 2
    
    def test_with_retry_all_attempts_fail(self):
        """Test with_retry when all attempts fail."""
        error = NetworkError("Persistent failure")
        mock_operation = Mock(side_effect=error)
        
        with patch('time.sleep'):
            with pytest.raises(NetworkError):
                self.handler.with_retry(mock_operation, self.context)
        
        assert mock_operation.call_count == 3  # max_attempts
        assert self.handler._error_stats["failed_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_with_retry_async_success(self):
        """Test async with_retry when operation succeeds."""
        async def mock_operation():
            return "async_success"
        
        result = await self.handler.with_retry_async(mock_operation, self.context)
        
        assert result == "async_success"
    
    @pytest.mark.asyncio
    async def test_with_retry_async_with_retry(self):
        """Test async with_retry with retry logic."""
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("First attempt failed")
            return "async_success"
        
        with patch('asyncio.sleep'):
            result = await self.handler.with_retry_async(mock_operation, self.context)
        
        assert result == "async_success"
        assert call_count == 2
    
    def test_get_error_stats(self):
        """Test getting error statistics."""
        # Generate some errors
        error = NetworkError("Test error")
        with patch('time.sleep'):
            self.handler.handle_error(error, self.context)
        
        stats = self.handler.get_error_stats()
        
        assert stats["total_errors"] == 1
        assert stats["retried_errors"] == 1
        assert stats["recovered_errors"] == 0
        assert stats["failed_operations"] == 0
    
    def test_reset_stats(self):
        """Test resetting error statistics."""
        # Generate some errors first
        error = NetworkError("Test error")
        with patch('time.sleep'):
            self.handler.handle_error(error, self.context)
        
        assert self.handler._error_stats["total_errors"] > 0
        
        self.handler.reset_stats()
        
        assert self.handler._error_stats["total_errors"] == 0
        assert self.handler._error_stats["retried_errors"] == 0
    
    def test_is_retryable_network_error(self):
        """Test retryability of network errors."""
        retryable_error = NetworkError("Connection timeout")
        non_retryable_error = NetworkError("Unauthorized", status_code=401)
        
        assert self.handler._is_retryable(retryable_error, self.context) is True
        assert self.handler._is_retryable(non_retryable_error, self.context) is False
    
    def test_is_retryable_configuration_error(self):
        """Test retryability of configuration errors."""
        error = ConfigurationError("Invalid setting")
        
        assert self.handler._is_retryable(error, self.context) is False
    
    def test_calculate_delay_fixed(self):
        """Test delay calculation with fixed strategy."""
        config = RetryConfig(strategy=RetryStrategy.FIXED_DELAY, base_delay=2.0)
        handler = ErrorHandler(config)
        
        assert handler._calculate_delay(1) == 2.0
        assert handler._calculate_delay(3) == 2.0
    
    def test_calculate_delay_linear(self):
        """Test delay calculation with linear backoff."""
        config = RetryConfig(strategy=RetryStrategy.LINEAR_BACKOFF, base_delay=1.0)
        handler = ErrorHandler(config)
        
        assert handler._calculate_delay(1) == 1.0
        assert handler._calculate_delay(2) == 2.0
        assert handler._calculate_delay(3) == 3.0
    
    def test_calculate_delay_exponential(self):
        """Test delay calculation with exponential backoff."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0
        )
        handler = ErrorHandler(config)
        
        assert handler._calculate_delay(1) == 1.0
        assert handler._calculate_delay(2) == 2.0
        assert handler._calculate_delay(3) == 4.0
    
    def test_calculate_delay_max_limit(self):
        """Test delay calculation respects max limit."""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=10.0,
            max_delay=15.0,
            backoff_multiplier=2.0
        )
        handler = ErrorHandler(config)
        
        assert handler._calculate_delay(1) == 10.0
        assert handler._calculate_delay(2) == 15.0  # Capped at max_delay
    
    def test_get_error_severity(self):
        """Test error severity determination."""
        config_error = ConfigurationError("Config issue")
        network_error_500 = NetworkError("Server error", status_code=500)
        network_error_404 = NetworkError("Not found", status_code=404)
        parsing_error = ParsingError("Parse failed")
        rate_limit_error = RateLimitError("Rate limited")
        
        assert self.handler._get_error_severity(config_error) == ErrorSeverity.CRITICAL
        assert self.handler._get_error_severity(network_error_500) == ErrorSeverity.HIGH
        assert self.handler._get_error_severity(network_error_404) == ErrorSeverity.MEDIUM
        assert self.handler._get_error_severity(parsing_error) == ErrorSeverity.MEDIUM
        assert self.handler._get_error_severity(rate_limit_error) == ErrorSeverity.LOW


class TestErrorHandlerIntegration:
    """Integration tests for error handler."""
    
    def test_complete_retry_workflow(self):
        """Test complete retry workflow with different error types."""
        handler = ErrorHandler(RetryConfig(max_attempts=3, base_delay=0.1))
        
        # Simulate a function that fails twice then succeeds
        call_count = 0
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise NetworkError(f"Attempt {call_count} failed")
            return f"Success on attempt {call_count}"
        
        context = ErrorContext(operation="flaky_test", max_attempts=3)
        
        with patch('time.sleep'):
            result = handler.with_retry(flaky_operation, context)
        
        assert result == "Success on attempt 3"
        assert call_count == 3
        
        stats = handler.get_error_stats()
        assert stats["total_errors"] == 2
        assert stats["retried_errors"] == 2
        assert stats["failed_operations"] == 0
    
    def test_mixed_error_types_handling(self):
        """Test handling of mixed error types in sequence."""
        handler = ErrorHandler()
        context = ErrorContext(operation="mixed_test")
        
        # Test different error types
        network_error = NetworkError("Network issue")
        config_error = ConfigurationError("Config issue")
        rate_limit_error = RateLimitError("Rate limited", retry_after=1)
        
        with patch('time.sleep'):
            # Network error should be retryable
            assert handler.handle_error(network_error, context) is True
            
            # Config error should not be retryable
            assert handler.handle_error(config_error, context) is False
            
            # Rate limit error should be retryable
            assert handler.handle_error(rate_limit_error, context) is True
        
        stats = handler.get_error_stats()
        assert stats["total_errors"] == 3
        assert stats["retried_errors"] == 2  # network and rate limit errors


if __name__ == "__main__":
    pytest.main([__file__])