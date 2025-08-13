"""
Custom exception classes for the atomic scraper tool.

Provides specific error types for different failure scenarios.
"""

from typing import Optional, Dict, Any


class ScrapingError(Exception):
    """Base exception for all scraping-related errors."""
    
    def __init__(self, message: str, error_type: str, url: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize scraping error.
        
        Args:
            message: Error message
            error_type: Type of error (e.g., 'network', 'parsing', 'validation')
            url: URL where error occurred (optional)
            context: Additional error context (optional)
        """
        self.message = message
        self.error_type = error_type
        self.url = url
        self.context = context or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"[{self.error_type.upper()}] {self.message}"
        if self.url:
            error_str += f" (URL: {self.url})"
        return error_str


class NetworkError(ScrapingError):
    """Exception for network-related errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize network error.
        
        Args:
            message: Error message
            url: URL where error occurred
            status_code: HTTP status code (if applicable)
            context: Additional error context
        """
        super().__init__(message, "network", url, context)
        self.status_code = status_code


class ParsingError(ScrapingError):
    """Exception for HTML parsing and content extraction errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 selector: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize parsing error.
        
        Args:
            message: Error message
            url: URL where error occurred
            selector: CSS selector or XPath that failed
            context: Additional error context
        """
        super().__init__(message, "parsing", url, context)
        self.selector = selector


class ValidationError(ScrapingError):
    """Exception for data validation errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 field_value: Optional[Any] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_name: Name of field that failed validation
            field_value: Value that failed validation
            context: Additional error context
        """
        super().__init__(message, "validation", context=context)
        self.field_name = field_name
        self.field_value = field_value


class ConfigurationError(ScrapingError):
    """Exception for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
            context: Additional error context
        """
        super().__init__(message, "configuration", context=context)
        self.config_key = config_key


class RateLimitError(ScrapingError):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 retry_after: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            url: URL where rate limit was hit
            retry_after: Seconds to wait before retrying
            context: Additional error context
        """
        super().__init__(message, "rate_limit", url, context)
        self.retry_after = retry_after


class QualityError(ScrapingError):
    """Exception for data quality threshold errors."""
    
    def __init__(self, message: str, quality_score: float, 
                 threshold: float, context: Optional[Dict[str, Any]] = None):
        """
        Initialize quality error.
        
        Args:
            message: Error message
            quality_score: Actual quality score achieved
            threshold: Minimum quality threshold required
            context: Additional error context
        """
        super().__init__(message, "quality", context=context)
        self.quality_score = quality_score
        self.threshold = threshold