"""
Extraction-related data models for the atomic scraper tool.

Contains models for content extraction and processing.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from urllib.parse import urlparse
import re


class ExtractionRule(BaseModel):
    """Rule for extracting specific content from HTML."""
    
    field_name: str = Field(..., description="Name of the field this rule extracts")
    selector: str = Field(..., description="CSS selector or XPath for extraction")
    extraction_type: str = Field(..., description="Type of extraction: 'text', 'attribute', 'html'")
    attribute_name: Optional[str] = Field(None, description="Attribute name for 'attribute' extraction type")
    post_processing: List[str] = Field(default_factory=list, description="Post-processing steps to apply")
    fallback_selectors: List[str] = Field(default_factory=list, description="Fallback selectors if primary fails")
    quality_indicators: List[str] = Field(default_factory=list, description="Indicators of high-quality content")
    
    @field_validator('field_name')
    @classmethod
    def validate_field_name(cls, v):
        """Validate field name is not empty and follows naming conventions."""
        if not v.strip():
            raise ValueError('field_name cannot be empty')
        
        # Field name should be a valid identifier
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('field_name must start with a letter and contain only letters, numbers, and underscores')
        return v
    
    @field_validator('selector')
    @classmethod
    def validate_selector(cls, v):
        """Validate selector is not empty and has basic syntax."""
        if not v.strip():
            raise ValueError('selector cannot be empty')
        
        # Basic CSS selector and XPath validation
        if not re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_/@]+$', v):
            raise ValueError(f"Invalid selector syntax: '{v}'")
        return v
    
    @field_validator('extraction_type')
    @classmethod
    def validate_extraction_type(cls, v):
        """Validate extraction type is supported."""
        valid_types = ['text', 'attribute', 'html', 'href', 'src', 'inner_text', 'outer_html']
        if v not in valid_types:
            raise ValueError(f'extraction_type must be one of: {valid_types}')
        return v
    
    @field_validator('post_processing')
    @classmethod
    def validate_post_processing(cls, v):
        """Validate post-processing steps are supported."""
        valid_steps = [
            'clean', 'normalize', 'validate', 'trim', 'lowercase', 'uppercase', 
            'strip_html', 'extract_numbers', 'extract_urls', 'remove_duplicates'
        ]
        for step in v:
            if step not in valid_steps:
                raise ValueError(f'Invalid post-processing step: {step}. Valid steps: {valid_steps}')
        return v
    
    @field_validator('fallback_selectors')
    @classmethod
    def validate_fallback_selectors(cls, v):
        """Validate fallback selectors have basic syntax."""
        for selector in v:
            if not selector.strip():
                raise ValueError('fallback_selectors cannot contain empty strings')
            if not re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_/@]+$', selector):
                raise ValueError(f"Invalid fallback selector syntax: '{selector}'")
        return v
    
    @field_validator('quality_indicators')
    @classmethod
    def validate_quality_indicators(cls, v):
        """Validate quality indicators are supported."""
        valid_indicators = [
            'has_text', 'has_links', 'has_images', 'min_length', 'max_length',
            'contains_keywords', 'matches_pattern', 'has_structure'
        ]
        for indicator in v:
            if indicator not in valid_indicators:
                raise ValueError(f'Invalid quality indicator: {indicator}. Valid indicators: {valid_indicators}')
        return v
    
    @model_validator(mode='after')
    def validate_attribute_extraction(self):
        """Ensure attribute_name is provided for attribute extraction."""
        if self.extraction_type == 'attribute' and not self.attribute_name:
            raise ValueError('attribute_name is required for attribute extraction type')
        
        if self.extraction_type != 'attribute' and self.attribute_name:
            raise ValueError('attribute_name should only be provided for attribute extraction type')
        
        return self


class ExtractedContent(BaseModel):
    """Content extracted from a single HTML element or page section."""
    
    data: Dict[str, Any] = Field(..., description="Extracted data fields")
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Quality score for this content")
    extraction_issues: List[str] = Field(default_factory=list, description="Issues encountered during extraction")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in extraction accuracy")
    source_url: str = Field(..., description="URL where content was extracted from")
    element_selector: Optional[str] = Field(None, description="Selector that matched this content")
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional extraction metadata")
    
    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate data is not empty and contains valid types."""
        if not v:
            raise ValueError('data cannot be empty')
        
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
    
    @field_validator('source_url')
    @classmethod
    def validate_source_url(cls, v):
        """Validate source_url is a valid URL."""
        if not v.strip():
            raise ValueError('source_url cannot be empty')
        
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: '{v}'")
        
        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"URL scheme must be http or https, got '{parsed.scheme}'")
        
        return v
    
    @field_validator('element_selector')
    @classmethod
    def validate_element_selector(cls, v):
        """Validate element selector if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError('element_selector cannot be empty string')
            if not re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_/@]+$', v):
                raise ValueError(f"Invalid element selector syntax: '{v}'")
        return v
    
    @field_validator('extraction_metadata')
    @classmethod
    def validate_extraction_metadata(cls, v):
        """Validate extraction metadata contains valid types."""
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
                raise ValueError(f"Metadata keys must be strings, got {type(key)} for key '{key}'")
            if not is_json_serializable(value):
                raise ValueError(f"Metadata value for key '{key}' is not JSON serializable")
        
        return v
    
    def add_issue(self, issue: str) -> None:
        """Add an extraction issue to the list."""
        if issue and issue not in self.extraction_issues:
            self.extraction_issues.append(issue)
    
    def has_required_fields(self, required_fields: List[str]) -> bool:
        """Check if all required fields are present and non-empty."""
        for field in required_fields:
            if field not in self.data or not self.data[field]:
                return False
        return True
    
    def get_field_completeness(self) -> float:
        """Calculate field completeness as percentage of non-empty fields."""
        if not self.data:
            return 0.0
        
        non_empty_fields = sum(1 for value in self.data.values() if value is not None and str(value).strip())
        return (non_empty_fields / len(self.data)) * 100.0
    
    def get_data_size(self) -> int:
        """Get total size of extracted data in characters."""
        total_size = 0
        for value in self.data.values():
            if value is not None:
                total_size += len(str(value))
        return total_size


class ContentQualityMetrics(BaseModel):
    """Metrics for assessing content quality."""
    
    completeness_score: float = Field(..., ge=0.0, le=100.0, description="Percentage of fields with data")
    accuracy_score: float = Field(..., ge=0.0, le=100.0, description="Estimated accuracy of extracted data")
    consistency_score: float = Field(..., ge=0.0, le=100.0, description="Consistency with expected patterns")
    relevance_score: float = Field(..., ge=0.0, le=100.0, description="Relevance to extraction criteria")
    
    @model_validator(mode='after')
    def validate_score_consistency(self):
        """Validate that scores are consistent with each other."""
        # If completeness is very low, accuracy shouldn't be very high
        if self.completeness_score < 20.0 and self.accuracy_score > 80.0:
            raise ValueError('Accuracy score cannot be high when completeness is very low')
        
        # If consistency is very low, overall quality should reflect that
        if self.consistency_score < 30.0 and self.accuracy_score > 90.0:
            raise ValueError('Accuracy score should be lower when consistency is poor')
        
        return self
    
    def calculate_overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted overall quality score."""
        if weights is None:
            weights = {'completeness': 0.25, 'accuracy': 0.25, 'consistency': 0.25, 'relevance': 0.25}
        
        # Validate weights sum to 1.0
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f'Weights must sum to 1.0, got {total_weight}')
        
        score = 0.0
        score += self.completeness_score * weights.get('completeness', 0.0)
        score += self.accuracy_score * weights.get('accuracy', 0.0)
        score += self.consistency_score * weights.get('consistency', 0.0)
        score += self.relevance_score * weights.get('relevance', 0.0)
        
        return min(100.0, max(0.0, score))
    
    def get_quality_category(self) -> str:
        """Get quality category based on overall score."""
        overall_score = self.calculate_overall_score()
        
        if overall_score >= 90.0:
            return 'excellent'
        elif overall_score >= 75.0:
            return 'good'
        elif overall_score >= 60.0:
            return 'fair'
        elif overall_score >= 40.0:
            return 'poor'
        else:
            return 'very_poor'