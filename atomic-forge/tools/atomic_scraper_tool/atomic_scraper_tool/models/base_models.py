"""
Base data models for the atomic scraper tool.

Contains core Pydantic models for scraping operations and results.
"""

import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from urllib.parse import urlparse


class ScrapingStrategy(BaseModel):
    """Strategy configuration for scraping operations."""
    
    scrape_type: str = Field(..., description="Type of scraping: 'list', 'detail', 'search', 'sitemap'")
    target_selectors: List[str] = Field(..., description="CSS selectors for target content")
    pagination_strategy: Optional[str] = Field(None, description="Pagination handling strategy")
    content_filters: List[str] = Field(default_factory=list, description="Content filtering rules")
    extraction_rules: Dict[str, str] = Field(default_factory=dict, description="Field extraction rules")
    max_pages: int = Field(10, ge=1, description="Maximum pages to scrape")
    request_delay: float = Field(1.0, ge=0.1, description="Delay between requests")
    
    @field_validator('scrape_type')
    @classmethod
    def validate_scrape_type(cls, v):
        """Validate scrape_type is one of allowed values."""
        allowed_types = {'list', 'detail', 'search', 'sitemap'}
        if v not in allowed_types:
            raise ValueError(f"scrape_type must be one of {allowed_types}, got '{v}'")
        return v
    
    @field_validator('target_selectors')
    @classmethod
    def validate_target_selectors(cls, v):
        """Validate CSS selectors are not empty and have basic syntax."""
        if not v:
            raise ValueError("target_selectors cannot be empty")
        
        for selector in v:
            if not selector.strip():
                raise ValueError("target_selectors cannot contain empty strings")
            # Basic CSS selector validation - allow common CSS selector characters
            if not re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_]+$', selector):
                raise ValueError(f"Invalid CSS selector syntax: '{selector}'")
        return v
    
    @field_validator('pagination_strategy')
    @classmethod
    def validate_pagination_strategy(cls, v):
        """Validate pagination strategy if provided."""
        if v is not None:
            allowed_strategies = {'next_link', 'page_numbers', 'infinite_scroll', 'load_more'}
            if v not in allowed_strategies:
                raise ValueError(f"pagination_strategy must be one of {allowed_strategies}, got '{v}'")
        return v
    
    @field_validator('extraction_rules')
    @classmethod
    def validate_extraction_rules(cls, v):
        """Validate extraction rules have valid CSS selectors."""
        for field_name, selector in v.items():
            if not field_name.strip():
                raise ValueError("extraction_rules field names cannot be empty")
            if not selector.strip():
                raise ValueError(f"extraction_rules selector for '{field_name}' cannot be empty")
            # Basic CSS selector validation
            if not re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_]+$', selector):
                raise ValueError(f"Invalid CSS selector in extraction_rules for '{field_name}': '{selector}'")
        return v


class ScrapedItem(BaseModel):
    """Individual scraped item with quality tracking."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique item identifier")
    source_url: str = Field(..., description="URL where item was scraped from")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when scraped")
    data: Dict[str, Any] = Field(..., description="Extracted data fields")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Quality score (0-100)")
    extraction_issues: List[str] = Field(default_factory=list, description="Issues encountered during extraction")
    schema_version: str = Field("1.0", description="Schema version used for extraction")
    
    @field_validator('source_url')
    @classmethod
    def validate_source_url(cls, v):
        """Validate source_url is a valid URL."""
        if not v.strip():
            raise ValueError("source_url cannot be empty")
        
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: '{v}'")
        
        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"URL scheme must be http or https, got '{parsed.scheme}'")
        
        return v
    
    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate data is not empty and contains valid types."""
        if not v:
            raise ValueError("data cannot be empty")
        
        # Check for valid JSON-serializable types
        def is_json_serializable(obj):
            """Check if object is JSON serializable."""
            if obj is None:
                return True
            if isinstance(obj, (str, int, float, bool)):
                return True
            if isinstance(obj, (list, tuple)):
                return all(is_json_serializable(item) for item in obj)
            if isinstance(obj, dict):
                return all(isinstance(k, str) and is_json_serializable(v) for k, v in obj.items())
            return False
        
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError(f"Data keys must be strings, got {type(key)} for key '{key}'")
            if not is_json_serializable(value):
                raise ValueError(f"Data value for key '{key}' is not JSON serializable")
        
        return v
    
    @field_validator('schema_version')
    @classmethod
    def validate_schema_version(cls, v):
        """Validate schema version format."""
        if not re.match(r'^\d+\.\d+$', v):
            raise ValueError(f"schema_version must be in format 'X.Y', got '{v}'")
        return v


class ScrapingResult(BaseModel):
    """Complete result of a scraping operation."""
    
    items: List[ScrapedItem] = Field(..., description="List of scraped items")
    total_items_found: int = Field(..., ge=0, description="Total items found on pages")
    total_items_scraped: int = Field(..., ge=0, description="Total items successfully scraped")
    average_quality_score: float = Field(..., ge=0.0, le=100.0, description="Average quality score")
    scraping_summary: str = Field(..., description="Human-readable summary of results")
    strategy_used: ScrapingStrategy = Field(..., description="Strategy used for scraping")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during scraping")
    execution_time: float = Field(..., ge=0.0, description="Total execution time in seconds")
    
    @field_validator('total_items_scraped')
    @classmethod
    def validate_scraped_count(cls, v, info):
        """Validate scraped count doesn't exceed found count."""
        if info.data and 'total_items_found' in info.data and v > info.data['total_items_found']:
            raise ValueError("total_items_scraped cannot exceed total_items_found")
        return v
    
    @field_validator('average_quality_score')
    @classmethod
    def validate_average_quality(cls, v, info):
        """Validate average quality score matches items if present."""
        if info.data and 'items' in info.data and info.data['items']:
            calculated_avg = sum(item.quality_score for item in info.data['items']) / len(info.data['items'])
            # Allow small floating point differences
            if abs(v - calculated_avg) > 0.01:
                raise ValueError(f"average_quality_score ({v}) doesn't match calculated average ({calculated_avg:.2f})")
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self):
        """Validate overall consistency of the result."""
        if len(self.items) != self.total_items_scraped:
            raise ValueError(f"Number of items ({len(self.items)}) doesn't match total_items_scraped ({self.total_items_scraped})")
        
        return self
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_items_found == 0:
            return 0.0
        return (self.total_items_scraped / self.total_items_found) * 100.0


# Validation utility functions
def validate_css_selector(selector: str) -> bool:
    """Validate CSS selector syntax."""
    if not selector.strip():
        return False
    
    # Basic CSS selector validation - allow common CSS selector characters
    return bool(re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_]+$', selector))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url.strip():
        return False
    
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc and parsed.scheme in ['http', 'https'])


def calculate_quality_score(data: Dict[str, Any], expected_fields: List[str]) -> float:
    """Calculate quality score based on data completeness and validity."""
    if not expected_fields:
        return 100.0
    
    present_fields = 0
    for field in expected_fields:
        if field in data and data[field] is not None and str(data[field]).strip():
            present_fields += 1
    
    return (present_fields / len(expected_fields)) * 100.0