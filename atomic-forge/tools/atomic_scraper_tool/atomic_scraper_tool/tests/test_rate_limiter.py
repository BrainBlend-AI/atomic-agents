"""
Unit tests for rate limiter functionality.
"""

import time
import threading
from unittest.mock import Mock, patch
import pytest

from atomic_scraper_tool.compliance.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    DomainStats,
    RespectfulCrawler
)
from atomic_scraper_tool.core.exceptions import ScrapingError


class TestRateLimitConfig:
    """Test cases for RateLimitConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        
        assert config.default_delay == 1.0
        assert config.max_concurrent_requests == 5
        assert config.adaptive_delay_enabled is True
        assert config.min_delay == 0.1
        assert config.max_delay == 30.0
        assert config.backoff_factor == 2.0
        assert config.max_retries == 3
        assert config.respect_retry_after is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            default_delay=2.0,
            max_concurrent_requests=10,
            adaptive_delay_enabled=False,
            min_delay=0.5,
            max_delay=60.0
        )
        
        assert config.default_delay == 2.0
        assert config.max_concurrent_requests == 10
        assert config.adaptive_delay_enabled is False
        assert config.min_delay == 0.5
        assert config.max_delay == 60.0


class TestDomainStats:
    """Test cases for DomainStats model."""
    
    def test_default_stats(self):
        """Test default domain statistics."""
        stats = DomainStats(domain="example.com")
        
        assert stats.domain == "example.com"
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.average_response_time == 0.0
        assert stats.last_request_time == 0.0
        assert stats.current_delay == 1.0
        assert stats.consecutive_failures == 0
        assert stats.active_requests == 0
        assert stats.request_times == []


class TestRateLimiter:
    """Test cases for RateLimiter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(
            default_delay=0.1,  # Short delay for testing
            max_concurrent_requests=2,
            min_delay=0.05,
            max_delay=1.0
        )
        self.rate_limiter = RateLimiter(self.config)
    
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        limiter = RateLimiter()
        assert limiter.config.default_delay == 1.0
        assert limiter._domain_stats == {}
    
    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        assert self.rate_limiter.config.default_delay == 0.1
        assert self.rate_limiter.config.max_concurrent_requests == 2
    
    def test_get_domain(self):
        """Test domain extraction from URLs."""
        assert self.rate_limiter.get_domain("https://example.com/path") == "example.com"
        assert self.rate_limiter.get_domain("http://subdomain.example.com") == "subdomain.example.com"
        assert self.rate_limiter.get_domain("https://EXAMPLE.COM/PATH") == "example.com"
    
    def test_get_domain_stats(self):
        """Test domain statistics retrieval and creation."""
        domain = "example.com"
        
        # First call should create new stats
        stats1 = self.rate_limiter.get_domain_stats(domain)
        assert stats1.domain == domain
        assert stats1.current_delay == self.config.default_delay
        
        # Second call should return same stats
        stats2 = self.rate_limiter.get_domain_stats(domain)
        assert stats1 is stats2
    
    def test_calculate_delay_no_adaptive(self):
        """Test delay calculation with adaptive delay disabled."""
        config = RateLimitConfig(adaptive_delay_enabled=False, default_delay=2.0)
        limiter = RateLimiter(config)
        
        delay = limiter.calculate_delay("example.com", response_time=5.0)
        assert delay == 2.0  # Should use default delay
    
    def test_calculate_delay_adaptive(self):
        """Test adaptive delay calculation."""
        domain = "example.com"
        
        # First request with slow response time
        delay1 = self.rate_limiter.calculate_delay(domain, response_time=2.0)
        
        # Should increase delay based on response time
        assert delay1 > self.config.default_delay
        
        # Second request with fast response time
        delay2 = self.rate_limiter.calculate_delay(domain, response_time=0.1)
        
        # Should adjust delay based on average
        stats = self.rate_limiter.get_domain_stats(domain)
        assert len(stats.request_times) == 2
        assert stats.average_response_time == 1.05  # (2.0 + 0.1) / 2
    
    def test_calculate_delay_bounds(self):
        """Test delay calculation respects min/max bounds."""
        domain = "example.com"
        
        # Very slow response should be capped at max_delay
        delay = self.rate_limiter.calculate_delay(domain, response_time=100.0)
        assert delay <= self.config.max_delay
        
        # Very fast response should not go below min_delay
        stats = self.rate_limiter.get_domain_stats(domain)
        stats.current_delay = self.config.min_delay
        delay = self.rate_limiter.calculate_delay(domain, response_time=0.001)
        assert delay >= self.config.min_delay
    
    def test_apply_backoff_failure(self):
        """Test backoff application for failures."""
        domain = "example.com"
        stats = self.rate_limiter.get_domain_stats(domain)
        initial_delay = stats.current_delay
        
        # Apply backoff for failure
        self.rate_limiter.apply_backoff(domain, is_failure=True)
        
        assert stats.consecutive_failures == 1
        assert stats.failed_requests == 1
        assert stats.total_requests == 1
        assert stats.current_delay > initial_delay
    
    def test_apply_backoff_success(self):
        """Test backoff reset on success."""
        domain = "example.com"
        stats = self.rate_limiter.get_domain_stats(domain)
        
        # First, apply some failures
        self.rate_limiter.apply_backoff(domain, is_failure=True)
        self.rate_limiter.apply_backoff(domain, is_failure=True)
        
        assert stats.consecutive_failures == 2
        high_delay = stats.current_delay
        
        # Then apply success
        self.rate_limiter.apply_backoff(domain, is_failure=False)
        
        assert stats.consecutive_failures == 0
        assert stats.successful_requests == 1
        assert stats.current_delay < high_delay  # Should reduce delay
    
    def test_should_retry(self):
        """Test retry decision logic."""
        domain = "example.com"
        
        # Should retry within max_retries
        assert self.rate_limiter.should_retry(domain, 0) is True
        assert self.rate_limiter.should_retry(domain, 2) is True
        
        # Should not retry beyond max_retries
        assert self.rate_limiter.should_retry(domain, 3) is False
        assert self.rate_limiter.should_retry(domain, 5) is False
    
    def test_get_retry_delay_with_retry_after(self):
        """Test retry delay calculation with Retry-After header."""
        domain = "example.com"
        
        delay = self.rate_limiter.get_retry_delay(domain, 0, retry_after=5)
        assert delay == 5.0
    
    def test_get_retry_delay_exponential_backoff(self):
        """Test exponential backoff for retry delays."""
        domain = "example.com"
        
        delay0 = self.rate_limiter.get_retry_delay(domain, 0)
        delay1 = self.rate_limiter.get_retry_delay(domain, 1)
        delay2 = self.rate_limiter.get_retry_delay(domain, 2)
        
        # Should increase exponentially
        assert delay1 > delay0
        assert delay2 > delay1
        assert delay2 == delay0 * (self.config.backoff_factor ** 2)
    
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_request_no_wait(self, mock_time, mock_sleep):
        """Test wait_for_request when no wait is needed."""
        mock_time.side_effect = [100.0, 100.0]  # Same time for both calls
        
        url = "https://example.com/test"
        domain = self.rate_limiter.get_domain(url)
        stats = self.rate_limiter.get_domain_stats(domain)
        stats.last_request_time = 90.0  # 10 seconds ago
        
        wait_time = self.rate_limiter.wait_for_request(url)
        
        assert wait_time == 0.0
        mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_request_with_wait(self, mock_time, mock_sleep):
        """Test wait_for_request when wait is needed."""
        mock_time.side_effect = [100.0, 100.05]  # 0.05 seconds later after sleep
        
        url = "https://example.com/test"
        domain = self.rate_limiter.get_domain(url)
        stats = self.rate_limiter.get_domain_stats(domain)
        stats.last_request_time = 99.95  # 0.05 seconds ago, need to wait 0.05 more
        
        wait_time = self.rate_limiter.wait_for_request(url)
        
        assert abs(wait_time - 0.05) < 0.001  # Allow for floating point precision
        # Check that sleep was called with approximately the right value
        mock_sleep.assert_called_once()
        sleep_arg = mock_sleep.call_args[0][0]
        assert abs(sleep_arg - 0.05) < 0.001
    
    def test_acquire_release_request_slot(self):
        """Test request slot acquisition and release."""
        url = "https://example.com/test"
        
        # Should be able to acquire up to max_concurrent_requests
        assert self.rate_limiter.acquire_request_slot(url) is True
        assert self.rate_limiter.acquire_request_slot(url) is True
        
        # Should fail to acquire beyond limit
        assert self.rate_limiter.acquire_request_slot(url) is False
        
        # Should be able to acquire after release
        self.rate_limiter.release_request_slot(url)
        assert self.rate_limiter.acquire_request_slot(url) is True
    
    def test_record_request_result(self):
        """Test request result recording."""
        url = "https://example.com/test"
        domain = self.rate_limiter.get_domain(url)
        
        # Record successful request
        self.rate_limiter.record_request_result(url, success=True, response_time=0.5)
        
        stats = self.rate_limiter.get_domain_stats(domain)
        assert stats.successful_requests == 1
        assert stats.total_requests == 1
        assert 0.5 in stats.request_times
        
        # Record failed request
        self.rate_limiter.record_request_result(url, success=False, response_time=1.0)
        
        assert stats.failed_requests == 1
        assert stats.total_requests == 2
        assert stats.consecutive_failures == 1
    
    def test_get_stats_summary(self):
        """Test statistics summary generation."""
        url1 = "https://example.com/test"
        url2 = "https://other.com/test"
        
        # Record some requests
        self.rate_limiter.record_request_result(url1, success=True, response_time=0.5)
        self.rate_limiter.record_request_result(url1, success=False, response_time=1.0)
        self.rate_limiter.record_request_result(url2, success=True, response_time=0.3)
        
        summary = self.rate_limiter.get_stats_summary()
        
        assert "example.com" in summary
        assert "other.com" in summary
        
        example_stats = summary["example.com"]
        assert example_stats["total_requests"] == 2
        assert example_stats["successful_requests"] == 1
        assert example_stats["failed_requests"] == 1
        assert example_stats["success_rate"] == 0.5
        
        other_stats = summary["other.com"]
        assert other_stats["total_requests"] == 1
        assert other_stats["successful_requests"] == 1
        assert other_stats["success_rate"] == 1.0
    
    def test_reset_domain_stats(self):
        """Test domain statistics reset."""
        url = "https://example.com/test"
        domain = self.rate_limiter.get_domain(url)
        
        # Record some activity
        self.rate_limiter.record_request_result(url, success=False)
        stats = self.rate_limiter.get_domain_stats(domain)
        assert stats.total_requests == 1
        
        # Reset stats
        self.rate_limiter.reset_domain_stats(domain)
        stats = self.rate_limiter.get_domain_stats(domain)
        assert stats.total_requests == 0
        assert stats.current_delay == self.config.default_delay
    
    def test_clear_all_stats(self):
        """Test clearing all statistics."""
        # Record activity for multiple domains
        self.rate_limiter.record_request_result("https://example.com/test", success=True)
        self.rate_limiter.record_request_result("https://other.com/test", success=True)
        
        assert len(self.rate_limiter._domain_stats) == 2
        
        # Clear all stats
        self.rate_limiter.clear_all_stats()
        
        assert len(self.rate_limiter._domain_stats) == 0
        assert len(self.rate_limiter._semaphores) == 0


class TestRespectfulCrawler:
    """Test cases for RespectfulCrawler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = Mock()
        self.robots_parser = Mock()
        self.crawler = RespectfulCrawler(self.rate_limiter, self.robots_parser)
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        crawler = RespectfulCrawler()
        assert crawler.rate_limiter is not None
        assert crawler.robots_parser is None
    
    def test_init_custom(self):
        """Test initialization with custom parameters."""
        assert self.crawler.rate_limiter is self.rate_limiter
        assert self.crawler.robots_parser is self.robots_parser
    
    def test_can_make_request_allowed(self):
        """Test can_make_request when request is allowed."""
        url = "https://example.com/test"
        user_agent = "TestBot"
        
        # Mock robots.txt allows request
        self.robots_parser.can_fetch.return_value = True
        
        # Mock rate limiter allows request
        self.rate_limiter.acquire_request_slot.return_value = True
        
        can_request, reason = self.crawler.can_make_request(url, user_agent)
        
        assert can_request is True
        assert reason == "Request allowed"
        
        # Should check robots.txt
        self.robots_parser.can_fetch.assert_called_once_with(url, user_agent)
        
        # Should acquire and release slot for testing
        assert self.rate_limiter.acquire_request_slot.call_count == 1
        assert self.rate_limiter.release_request_slot.call_count == 1
    
    def test_can_make_request_robots_disallowed(self):
        """Test can_make_request when robots.txt disallows request."""
        url = "https://example.com/test"
        user_agent = "TestBot"
        
        # Mock robots.txt disallows request
        self.robots_parser.can_fetch.return_value = False
        
        can_request, reason = self.crawler.can_make_request(url, user_agent)
        
        assert can_request is False
        assert reason == "Disallowed by robots.txt"
        
        # Should not check rate limiter if robots.txt disallows
        self.rate_limiter.acquire_request_slot.assert_not_called()
    
    def test_can_make_request_rate_limit_exceeded(self):
        """Test can_make_request when rate limit is exceeded."""
        url = "https://example.com/test"
        user_agent = "TestBot"
        
        # Mock robots.txt allows request
        self.robots_parser.can_fetch.return_value = True
        
        # Mock rate limiter denies request
        self.rate_limiter.acquire_request_slot.return_value = False
        
        can_request, reason = self.crawler.can_make_request(url, user_agent)
        
        assert can_request is False
        assert reason == "Maximum concurrent requests reached for domain"
    
    def test_can_make_request_no_robots_parser(self):
        """Test can_make_request without robots parser."""
        crawler = RespectfulCrawler(self.rate_limiter, None)
        url = "https://example.com/test"
        
        # Mock rate limiter allows request
        self.rate_limiter.acquire_request_slot.return_value = True
        
        can_request, reason = crawler.can_make_request(url)
        
        assert can_request is True
        assert reason == "Request allowed"
    
    def test_prepare_request_success(self):
        """Test successful request preparation."""
        url = "https://example.com/test"
        user_agent = "TestBot"
        
        # Mock successful checks
        self.robots_parser.can_fetch.return_value = True
        self.rate_limiter.acquire_request_slot.return_value = True
        self.rate_limiter.wait_for_request.return_value = 0.5
        
        success, delay = self.crawler.prepare_request(url, user_agent)
        
        assert success is True
        assert delay == 0.5
        
        # Should acquire slot and apply delay
        self.rate_limiter.acquire_request_slot.assert_called_once_with(url)
        self.rate_limiter.wait_for_request.assert_called_once_with(url)
    
    def test_prepare_request_not_allowed(self):
        """Test request preparation when request is not allowed."""
        url = "https://example.com/test"
        user_agent = "TestBot"
        
        # Mock robots.txt disallows request
        self.robots_parser.can_fetch.return_value = False
        
        with pytest.raises(ScrapingError) as exc_info:
            self.crawler.prepare_request(url, user_agent)
        
        assert "Request not allowed" in str(exc_info.value)
        assert exc_info.value.error_type == "rate_limit_error"
    
    def test_prepare_request_slot_unavailable(self):
        """Test request preparation when slot is unavailable."""
        url = "https://example.com/test"
        
        # Mock robots.txt allows but slot acquisition fails
        self.robots_parser.can_fetch.return_value = True
        self.rate_limiter.acquire_request_slot.return_value = False
        
        with pytest.raises(ScrapingError) as exc_info:
            self.crawler.prepare_request(url)
        
        assert "Maximum concurrent requests reached for domain" in str(exc_info.value)
        assert exc_info.value.error_type == "rate_limit_error"
    
    def test_complete_request(self):
        """Test request completion."""
        url = "https://example.com/test"
        success = True
        response_time = 0.5
        
        self.crawler.complete_request(url, success, response_time)
        
        # Should record result and release slot
        self.rate_limiter.record_request_result.assert_called_once_with(
            url, success, response_time
        )
        self.rate_limiter.release_request_slot.assert_called_once_with(url)


class TestRateLimiterIntegration:
    """Integration tests for rate limiter functionality."""
    
    def test_concurrent_requests_limiting(self):
        """Test that concurrent requests are properly limited."""
        config = RateLimitConfig(
            max_concurrent_requests=2,
            default_delay=0.01  # Very short delay for testing
        )
        rate_limiter = RateLimiter(config)
        url = "https://example.com/test"
        
        # Acquire maximum slots
        assert rate_limiter.acquire_request_slot(url) is True
        assert rate_limiter.acquire_request_slot(url) is True
        
        # Should fail to acquire more
        assert rate_limiter.acquire_request_slot(url) is False
        
        # Release one slot
        rate_limiter.release_request_slot(url)
        
        # Should be able to acquire again
        assert rate_limiter.acquire_request_slot(url) is True
    
    def test_adaptive_delay_behavior(self):
        """Test adaptive delay behavior with real timing."""
        config = RateLimitConfig(
            default_delay=0.1,
            adaptive_delay_enabled=True,
            min_delay=0.05,
            max_delay=1.0
        )
        rate_limiter = RateLimiter(config)
        domain = "example.com"
        
        # Record slow response times
        for _ in range(3):
            rate_limiter.calculate_delay(domain, response_time=2.0)
        
        stats = rate_limiter.get_domain_stats(domain)
        
        # Delay should increase due to slow responses
        assert stats.current_delay > config.default_delay
        assert stats.average_response_time == 2.0
        
        # Record fast response times
        for _ in range(5):
            rate_limiter.calculate_delay(domain, response_time=0.1)
        
        # Delay should decrease due to faster responses
        new_delay = stats.current_delay
        assert new_delay < 2.0  # Should be less than the high delay from slow responses