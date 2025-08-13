"""
Schema-related data models for the atomic scraper tool.

Contains models for dynamic schema generation and field definitions.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class FieldDefinition(BaseModel):
    """Definition for a data field in a schema recipe."""
    
    field_type: str = Field(..., description="Data type: 'string', 'number', 'array', 'object', 'boolean'")
    description: str = Field(..., description="Human-readable field description")
    extraction_selector: str = Field(..., description="CSS selector or XPath for extraction")
    validation_pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    required: bool = Field(False, description="Whether field is required")
    quality_weight: float = Field(1.0, ge=0.0, description="Weight for quality scoring")
    post_processing: List[str] = Field(default_factory=list, description="Post-processing steps")
    
    @field_validator('field_type')
    @classmethod
    def validate_field_type(cls, v):
        """Validate field type is supported."""
        valid_types = ['string', 'number', 'array', 'object', 'boolean']
        if v not in valid_types:
            raise ValueError(f'field_type must be one of: {valid_types}')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description is not empty."""
        if not v.strip():
            raise ValueError('description cannot be empty')
        return v
    
    @field_validator('extraction_selector')
    @classmethod
    def validate_extraction_selector(cls, v):
        """Validate extraction selector syntax."""
        if not v.strip():
            raise ValueError('extraction_selector cannot be empty')
        
        # Basic CSS selector validation - allow common CSS selector characters and XPath
        if not re.match(r'^[a-zA-Z0-9\s\.\#\[\]\:\-\>\+\~\*\(\)\"\'=,_/@]+$', v):
            raise ValueError(f"Invalid selector syntax: '{v}'")
        return v
    
    @field_validator('validation_pattern')
    @classmethod
    def validate_validation_pattern(cls, v):
        """Validate regex pattern if provided."""
        if v is not None:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f'Invalid regex pattern: {e}')
        return v
    
    @field_validator('post_processing')
    @classmethod
    def validate_post_processing(cls, v):
        """Validate post-processing steps are supported."""
        valid_steps = ['clean', 'normalize', 'validate', 'trim', 'lowercase', 'uppercase', 'strip_html', 'extract_numbers']
        for step in v:
            if step not in valid_steps:
                raise ValueError(f'Invalid post-processing step: {step}. Valid steps: {valid_steps}')
        return v


class SchemaRecipe(BaseModel):
    """Recipe for generating dynamic schemas based on website content."""
    
    name: str = Field(..., description="Unique name for the schema recipe")
    description: str = Field(..., description="Human-readable description of the schema")
    fields: Dict[str, FieldDefinition] = Field(..., description="Field definitions")
    validation_rules: List[str] = Field(default_factory=list, description="Global validation rules")
    quality_weights: Dict[str, float] = Field(
        default_factory=lambda: {"completeness": 0.4, "accuracy": 0.4, "consistency": 0.2},
        description="Weights for quality scoring components"
    )
    version: str = Field("1.0", description="Schema version")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty and follows naming conventions."""
        if not v.strip():
            raise ValueError('name cannot be empty')
        
        # Allow alphanumeric, underscores, hyphens, and spaces
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description is not empty."""
        if not v.strip():
            raise ValueError('description cannot be empty')
        return v
    
    @field_validator('fields')
    @classmethod
    def validate_fields_not_empty(cls, v):
        """Ensure at least one field is defined."""
        if not v:
            raise ValueError('Schema recipe must have at least one field defined')
        
        # Validate field names
        for field_name in v.keys():
            if not field_name.strip():
                raise ValueError('Field names cannot be empty')
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', field_name):
                raise ValueError(f'Field name "{field_name}" must start with a letter and contain only letters, numbers, and underscores')
        
        return v
    
    @field_validator('quality_weights')
    @classmethod
    def validate_quality_weights_sum(cls, v):
        """Ensure quality weights sum to 1.0."""
        if not v:
            raise ValueError('quality_weights cannot be empty')
        
        # Check for required weight categories
        required_categories = {'completeness', 'accuracy', 'consistency'}
        missing_categories = required_categories - set(v.keys())
        if missing_categories:
            raise ValueError(f'Missing required quality weight categories: {missing_categories}')
        
        # Check all weights are non-negative
        for category, weight in v.items():
            if weight < 0:
                raise ValueError(f'Quality weight for "{category}" cannot be negative: {weight}')
        
        # Check weights sum to 1.0
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f'Quality weights must sum to 1.0, got {total}')
        return v
    
    @field_validator('validation_rules')
    @classmethod
    def validate_validation_rules(cls, v):
        """Validate global validation rules."""
        valid_rules = [
            'require_all_fields', 'allow_partial_data', 'strict_types', 
            'normalize_whitespace', 'remove_duplicates', 'validate_urls'
        ]
        
        for rule in v:
            if rule not in valid_rules:
                raise ValueError(f'Invalid validation rule: {rule}. Valid rules: {valid_rules}')
        return v
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        """Validate version format."""
        if not re.match(r'^\d+\.\d+$', v):
            raise ValueError(f"version must be in format 'X.Y', got '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_consistency(self):
        """Validate overall schema consistency."""
        # Check that required fields have appropriate quality weights
        required_fields = self.get_required_fields()
        if required_fields:
            avg_required_weight = sum(self.fields[name].quality_weight for name in required_fields) / len(required_fields)
            if avg_required_weight < 0.5:
                raise ValueError('Required fields should have higher quality weights (average < 0.5)')
        
        return self
    
    def get_required_fields(self) -> List[str]:
        """Get list of required field names."""
        return [name for name, field_def in self.fields.items() if field_def.required]
    
    def get_field_selectors(self) -> Dict[str, str]:
        """Get mapping of field names to their extraction selectors."""
        return {name: field_def.extraction_selector for name, field_def in self.fields.items()}
    
    def calculate_field_quality_weight(self, field_name: str) -> float:
        """Calculate the quality weight for a specific field."""
        if field_name not in self.fields:
            return 0.0
        return self.fields[field_name].quality_weight
    
    def get_total_quality_weight(self) -> float:
        """Get total quality weight of all fields."""
        return sum(field_def.quality_weight for field_def in self.fields.values())
    
    def validate_extracted_data(self, data: Dict[str, any]) -> List[str]:
        """Validate extracted data against schema rules."""
        errors = []
        
        # Check required fields
        for required_field in self.get_required_fields():
            if required_field not in data or data[required_field] is None:
                errors.append(f'Required field "{required_field}" is missing')
        
        # Validate field patterns
        for field_name, field_def in self.fields.items():
            if field_name in data and data[field_name] is not None and field_def.validation_pattern:
                value_str = str(data[field_name])
                if not re.match(field_def.validation_pattern, value_str):
                    errors.append(f'Field "{field_name}" does not match validation pattern')
        
        return errors