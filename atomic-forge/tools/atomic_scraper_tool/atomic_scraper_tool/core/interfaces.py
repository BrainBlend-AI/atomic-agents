"""
Base interfaces and abstract classes for the atomic scraper tool.

These interfaces establish system boundaries and define contracts for core components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from atomic_scraper_tool.models.base_models import ScrapingStrategy, ScrapingResult
from atomic_scraper_tool.models.schema_models import SchemaRecipe
from atomic_scraper_tool.models.extraction_models import ExtractedContent


class BaseExtractor(ABC):
    """Abstract base class for content extractors."""
    
    @abstractmethod
    def extract_content(self, html: str, strategy: ScrapingStrategy) -> List[ExtractedContent]:
        """
        Extract content from HTML using the provided strategy.
        
        Args:
            html: Raw HTML content to extract from
            strategy: Scraping strategy with selectors and rules
            
        Returns:
            List of extracted content items with quality scores
        """
        pass
    
    @abstractmethod
    def calculate_quality_score(self, content: Dict[str, Any], schema: SchemaRecipe) -> float:
        """
        Calculate quality score for extracted content.
        
        Args:
            content: Extracted content data
            schema: Schema recipe with quality weights
            
        Returns:
            Quality score between 0.0 and 100.0
        """
        pass


class BaseAnalyzer(ABC):
    """Abstract base class for website analyzers."""
    
    @abstractmethod
    def analyze_website_structure(self, url: str, html: str) -> Dict[str, Any]:
        """
        Analyze website structure and content patterns.
        
        Args:
            url: Website URL being analyzed
            html: HTML content to analyze
            
        Returns:
            Analysis results including content types and patterns
        """
        pass
    
    @abstractmethod
    def detect_content_types(self, html: str) -> List[str]:
        """
        Detect common content types in the HTML.
        
        Args:
            html: HTML content to analyze
            
        Returns:
            List of detected content types (e.g., 'list', 'article', 'product')
        """
        pass


class BaseGenerator(ABC):
    """Abstract base class for strategy and schema generators."""
    
    @abstractmethod
    def generate_strategy(self, analysis: Dict[str, Any], criteria: str) -> ScrapingStrategy:
        """
        Generate scraping strategy based on website analysis and user criteria.
        
        Args:
            analysis: Website structure analysis results
            criteria: User's scraping criteria
            
        Returns:
            Generated scraping strategy
        """
        pass
    
    @abstractmethod
    def generate_schema_recipe(self, analysis: Dict[str, Any], criteria: str) -> SchemaRecipe:
        """
        Generate schema recipe based on website analysis and user criteria.
        
        Args:
            analysis: Website structure analysis results
            criteria: User's scraping criteria
            
        Returns:
            Generated schema recipe for data validation
        """
        pass


class BaseProcessor(ABC):
    """Abstract base class for data processors."""
    
    @abstractmethod
    def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean extracted data.
        
        Args:
            raw_data: Raw extracted data items
            
        Returns:
            Processed and cleaned data items
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any], schema: SchemaRecipe) -> bool:
        """
        Validate data against schema recipe.
        
        Args:
            data: Data item to validate
            schema: Schema recipe for validation
            
        Returns:
            True if data is valid, False otherwise
        """
        pass


class BaseErrorHandler(ABC):
    """Abstract base class for error handlers."""
    
    @abstractmethod
    def handle_network_error(self, error: Exception, url: str) -> bool:
        """
        Handle network-related errors.
        
        Args:
            error: The network error that occurred
            url: URL where the error occurred
            
        Returns:
            True if operation should be retried, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_parsing_error(self, error: Exception, content: str) -> Optional[Dict[str, Any]]:
        """
        Handle parsing errors and attempt recovery.
        
        Args:
            error: The parsing error that occurred
            content: Content that failed to parse
            
        Returns:
            Recovered data if possible, None otherwise
        """
        pass
    
    @abstractmethod
    def should_retry(self, error: Exception, attempt: int, max_attempts: int) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            error: The error that occurred
            attempt: Current attempt number
            max_attempts: Maximum number of attempts allowed
            
        Returns:
            True if operation should be retried, False otherwise
        """
        pass