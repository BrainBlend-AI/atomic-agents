"""
Rate limiter for respectful web crawling.

This module provides rate limiting functionality to ensure respectful crawling
by implementing configurable delays, request throttling, and adaptive rate limiting.
"""

import asyncio
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from atomic_scraper_tool.core.exceptions import ScrapingError


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    default_delay: float = 1.0  # Default delay between requests in seconds
    max_concurrent_requests: int = 5  # Maximum concurrent requests per domain
    adaptive_delay_enabled: bool = True  # Enable adaptive delay based on response times
    min_delay: float = 0.1  # Minimum delay between requests
    max_delay: float = 30.0  # Maximum delay between requests
    backoff_factor: float = 2.0  # Backoff factor for failed requests
    max_retries: int = 3  # Maximum number of retries for failed requests
    respect_retry_after: bool = True  # Respect Retry-After headers


class DomainStats(BaseModel):
    """Statistics for a specific domain."""
    domain: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: float = 0.0
    current_delay: float = 1.0
    consecutive_failures: int = 0
    active_requests: int = 0
    request_times: list = Field(default_factory=list)  # Last 10 request times for adaptive delay


class RateLimiter:
    """
    Rate limiter for respectful web crawling.
    
    This class implements various rate limiting strategies including:
    - Fixed delays between requests
    - Adaptive delays based on server response times
    - Concurrent request limiting per domain
    - Backoff strategies for failed requests
    - Respect for Retry-After headers
    """
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize the rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config or RateLimitConfig()
        self._domain_stats: Dict[str, DomainStats] = {}
        self._domain_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._request_queues: Dict[str, deque] = defaultdict(deque)
        self._semaphores: Dict[str, threading.Semaphore] = {}
        self._lock = threading.Lock()
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def get_domain_stats(self, domain: str) -> DomainStats:
        """Get statistics for a domain."""
        with self._lock:
            if domain not in self._domain_stats:
                self._domain_stats[domain] = DomainStats(
                    domain=domain,
                    current_delay=self.config.default_delay
                )
            return self._domain_stats[domain]
    
    def get_semaphore(self, domain: str) -> threading.Semaphore:
        """Get or create semaphore for domain concurrency control."""
        with self._lock:
            if domain not in self._semaphores:
                self._semaphores[domain] = threading.Semaphore(
                    self.config.max_concurrent_requests
                )
            return self._semaphores[domain]
    
    def calculate_delay(self, domain: str, response_time: Optional[float] = None) -> float:
        """
        Calculate the appropriate delay for the next request to a domain.
        
        Args:
            domain: The domain to calculate delay for
            response_time: Response time of the last request (for adaptive delay)
            
        Returns:
            Delay in seconds before the next request
        """
        stats = self.get_domain_stats(domain)
        
        if not self.config.adaptive_delay_enabled:
            return stats.current_delay
        
        # If we have response time, use it for adaptive delay calculation
        if response_time is not None:
            # Keep track of recent response times (last 10)
            stats.request_times.append(response_time)
            if len(stats.request_times) > 10:
                stats.request_times.pop(0)
            
            # Calculate average response time
            if stats.request_times:
                avg_response_time = sum(stats.request_times) / len(stats.request_times)
                stats.average_response_time = avg_response_time
                
                # Adaptive delay: slower servers get longer delays
                # Base delay + (average response time * factor)
                adaptive_delay = self.config.default_delay + (avg_response_time * 0.5)
                
                # Apply bounds
                adaptive_delay = max(self.config.min_delay, adaptive_delay)
                adaptive_delay = min(self.config.max_delay, adaptive_delay)
                
                stats.current_delay = adaptive_delay
        
        return stats.current_delay
    
    def apply_backoff(self, domain: str, is_failure: bool = False):
        """
        Apply backoff strategy for failed requests.
        
        Args:
            domain: The domain to apply backoff for
            is_failure: Whether the last request was a failure
        """
        stats = self.get_domain_stats(domain)
        
        if is_failure:
            stats.consecutive_failures += 1
            stats.failed_requests += 1
            
            # Exponential backoff for consecutive failures
            backoff_multiplier = self.config.backoff_factor ** min(stats.consecutive_failures, 5)
            new_delay = stats.current_delay * backoff_multiplier
            
            # Apply bounds
            stats.current_delay = min(new_delay, self.config.max_delay)
        else:
            # Reset consecutive failures on success
            if stats.consecutive_failures > 0:
                stats.consecutive_failures = 0
                # Gradually reduce delay back to normal
                stats.current_delay = max(
                    self.config.default_delay,
                    stats.current_delay * 0.8
                )
            stats.successful_requests += 1
        
        stats.total_requests += 1
    
    def should_retry(self, domain: str, attempt: int) -> bool:
        """
        Determine if a request should be retried.
        
        Args:
            domain: The domain for the request
            attempt: Current attempt number (0-based)
            
        Returns:
            True if the request should be retried
        """
        return attempt < self.config.max_retries
    
    def get_retry_delay(self, domain: str, attempt: int, retry_after: Optional[int] = None) -> float:
        """
        Get the delay before retrying a failed request.
        
        Args:
            domain: The domain for the request
            attempt: Current attempt number (0-based)
            retry_after: Retry-After header value in seconds
            
        Returns:
            Delay in seconds before retry
        """
        if retry_after is not None and self.config.respect_retry_after:
            return float(retry_after)
        
        # Exponential backoff for retries
        base_delay = self.calculate_delay(domain)
        retry_delay = base_delay * (self.config.backoff_factor ** attempt)
        
        return min(retry_delay, self.config.max_delay)
    
    def wait_for_request(self, url: str, response_time: Optional[float] = None) -> float:
        """
        Wait for the appropriate delay before making a request.
        
        Args:
            url: The URL to be requested
            response_time: Response time of the previous request (for adaptive delay)
            
        Returns:
            Actual delay time waited
        """
        domain = self.get_domain(url)
        stats = self.get_domain_stats(domain)
        
        # Calculate required delay
        required_delay = self.calculate_delay(domain, response_time)
        
        # Calculate time since last request
        current_time = time.time()
        time_since_last = current_time - stats.last_request_time
        
        # Wait if necessary
        if time_since_last < required_delay:
            wait_time = required_delay - time_since_last
            time.sleep(wait_time)
            stats.last_request_time = time.time()
            return wait_time
        else:
            stats.last_request_time = current_time
            return 0.0
    
    def acquire_request_slot(self, url: str) -> bool:
        """
        Acquire a request slot for concurrent request limiting.
        
        Args:
            url: The URL to be requested
            
        Returns:
            True if slot was acquired, False if max concurrent requests reached
        """
        domain = self.get_domain(url)
        semaphore = self.get_semaphore(domain)
        
        # Try to acquire semaphore (non-blocking)
        acquired = semaphore.acquire(blocking=False)
        
        if acquired:
            stats = self.get_domain_stats(domain)
            stats.active_requests += 1
        
        return acquired
    
    def release_request_slot(self, url: str):
        """
        Release a request slot after request completion.
        
        Args:
            url: The URL that was requested
        """
        domain = self.get_domain(url)
        semaphore = self.get_semaphore(domain)
        
        try:
            semaphore.release()
            stats = self.get_domain_stats(domain)
            stats.active_requests = max(0, stats.active_requests - 1)
        except ValueError:
            # Semaphore was already at maximum value
            pass
    
    def record_request_result(self, url: str, success: bool, response_time: Optional[float] = None):
        """
        Record the result of a request for statistics and adaptive behavior.
        
        Args:
            url: The URL that was requested
            success: Whether the request was successful
            response_time: Response time of the request
        """
        domain = self.get_domain(url)
        self.apply_backoff(domain, is_failure=not success)
        
        if response_time is not None:
            self.calculate_delay(domain, response_time)
    
    def get_stats_summary(self) -> Dict[str, Dict]:
        """
        Get a summary of rate limiting statistics for all domains.
        
        Returns:
            Dictionary with domain statistics
        """
        summary = {}
        
        with self._lock:
            for domain, stats in self._domain_stats.items():
                summary[domain] = {
                    'total_requests': stats.total_requests,
                    'successful_requests': stats.successful_requests,
                    'failed_requests': stats.failed_requests,
                    'success_rate': (
                        stats.successful_requests / stats.total_requests 
                        if stats.total_requests > 0 else 0.0
                    ),
                    'average_response_time': stats.average_response_time,
                    'current_delay': stats.current_delay,
                    'active_requests': stats.active_requests,
                    'consecutive_failures': stats.consecutive_failures
                }
        
        return summary
    
    def reset_domain_stats(self, domain: str):
        """
        Reset statistics for a specific domain.
        
        Args:
            domain: Domain to reset statistics for
        """
        with self._lock:
            if domain in self._domain_stats:
                self._domain_stats[domain] = DomainStats(
                    domain=domain,
                    current_delay=self.config.default_delay
                )
    
    def clear_all_stats(self):
        """Clear all domain statistics."""
        with self._lock:
            self._domain_stats.clear()
            self._semaphores.clear()


class RespectfulCrawler:
    """
    A wrapper class that combines rate limiting with other respectful crawling practices.
    
    This class provides a high-level interface for making respectful HTTP requests
    that automatically handles rate limiting, robots.txt compliance, and other
    ethical crawling practices.
    """
    
    def __init__(self, rate_limiter: RateLimiter = None, robots_parser=None):
        """
        Initialize the respectful crawler.
        
        Args:
            rate_limiter: Rate limiter instance
            robots_parser: Robots.txt parser instance
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.robots_parser = robots_parser
    
    def can_make_request(self, url: str, user_agent: str = None) -> Tuple[bool, str]:
        """
        Check if a request can be made to the given URL.
        
        Args:
            url: URL to check
            user_agent: User agent string
            
        Returns:
            Tuple of (can_make_request, reason)
        """
        # Check robots.txt compliance if parser is available
        if self.robots_parser:
            if not self.robots_parser.can_fetch(url, user_agent):
                return False, "Disallowed by robots.txt"
        
        # Check if we can acquire a request slot
        if not self.rate_limiter.acquire_request_slot(url):
            return False, "Maximum concurrent requests reached for domain"
        
        # Release the slot since this is just a check
        self.rate_limiter.release_request_slot(url)
        
        return True, "Request allowed"
    
    def prepare_request(self, url: str, user_agent: str = None) -> Tuple[bool, float]:
        """
        Prepare for making a request by applying rate limiting.
        
        Args:
            url: URL to request
            user_agent: User agent string
            
        Returns:
            Tuple of (success, delay_applied)
        """
        # Check robots.txt compliance if parser is available
        if self.robots_parser:
            if not self.robots_parser.can_fetch(url, user_agent):
                raise ScrapingError("Request not allowed: Disallowed by robots.txt", "rate_limit_error", url)
        
        # Acquire request slot
        if not self.rate_limiter.acquire_request_slot(url):
            raise ScrapingError("Request not allowed: Maximum concurrent requests reached for domain", "rate_limit_error", url)
        
        # Apply rate limiting delay
        delay = self.rate_limiter.wait_for_request(url)
        
        return True, delay
    
    def complete_request(self, url: str, success: bool, response_time: Optional[float] = None):
        """
        Complete a request by recording results and releasing resources.
        
        Args:
            url: URL that was requested
            success: Whether the request was successful
            response_time: Response time of the request
        """
        # Record request result for statistics
        self.rate_limiter.record_request_result(url, success, response_time)
        
        # Release request slot
        self.rate_limiter.release_request_slot(url)