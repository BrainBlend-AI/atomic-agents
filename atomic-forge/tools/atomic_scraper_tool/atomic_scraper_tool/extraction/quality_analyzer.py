"""
Data quality scoring system for the atomic scraper tool.

Provides comprehensive quality analysis including completeness, accuracy,
consistency scoring with configurable thresholds and filtering logic.
"""

import re
import statistics
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from atomic_scraper_tool.models.extraction_models import ExtractedContent, ContentQualityMetrics
from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition


@dataclass
class QualityThresholds:
    """Quality thresholds for filtering and scoring."""
    minimum_completeness: float = 50.0  # Minimum completeness percentage
    minimum_accuracy: float = 60.0      # Minimum accuracy percentage
    minimum_consistency: float = 40.0   # Minimum consistency percentage
    minimum_overall: float = 50.0       # Minimum overall quality score
    required_fields: List[str] = None   # Fields that must be present
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []


@dataclass
class QualityReport:
    """Comprehensive quality analysis report."""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    relevance_score: float
    field_scores: Dict[str, float]
    quality_issues: List[str]
    recommendations: List[str]
    passes_threshold: bool
    item_count: int
    
    def get_quality_category(self) -> str:
        """Get quality category based on overall score."""
        if self.overall_score >= 90.0:
            return 'excellent'
        elif self.overall_score >= 75.0:
            return 'good'
        elif self.overall_score >= 60.0:
            return 'fair'
        elif self.overall_score >= 40.0:
            return 'poor'
        else:
            return 'very_poor'


class QualityAnalyzer:
    """
    Analyzes data quality for extracted content with configurable scoring algorithms.
    
    Calculates completeness, accuracy, consistency, and relevance scores
    with support for custom quality thresholds and filtering logic.
    """
    
    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        """
        Initialize the quality analyzer.
        
        Args:
            thresholds: Quality thresholds for filtering and scoring
        """
        self.thresholds = thresholds or QualityThresholds()
        
        # Data validation patterns
        self.validation_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
            'phone': r'(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            'price': r'^\$?\d+\.?\d*$',
            'date': r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}-\d{1,2}-\d{4}',
            'number': r'^\d+\.?\d*$'
        }
        
        # Content quality indicators
        self.quality_indicators = {
            'min_length': 3,
            'max_length': 10000,
            'min_word_count': 1,
            'max_word_count': 2000,
            'suspicious_patterns': [
                r'^[^\w\s]*$',  # Only punctuation
                r'^(.)\1{10,}$',  # Repeated characters
                r'^\s*$',  # Only whitespace
                r'^[A-Z\s]{50,}$',  # All caps (likely spam)
            ]
        }
    
    def analyze_quality(
        self, 
        extracted_items: List[ExtractedContent],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> QualityReport:
        """
        Analyze quality of extracted content items.
        
        Args:
            extracted_items: List of extracted content items
            schema_recipe: Optional schema recipe for validation
            
        Returns:
            QualityReport with comprehensive quality analysis
        """
        if not extracted_items:
            return QualityReport(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                relevance_score=0.0,
                field_scores={},
                quality_issues=["No items to analyze"],
                recommendations=["Ensure extraction rules are correctly configured"],
                passes_threshold=False,
                item_count=0
            )
        
        # Calculate individual quality metrics
        completeness_score = self._calculate_completeness_score(extracted_items, schema_recipe)
        accuracy_score = self._calculate_accuracy_score(extracted_items, schema_recipe)
        consistency_score = self._calculate_consistency_score(extracted_items)
        relevance_score = self._calculate_relevance_score(extracted_items, schema_recipe)
        
        # Calculate field-level scores
        field_scores = self._calculate_field_scores(extracted_items, schema_recipe)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            completeness_score, accuracy_score, consistency_score, relevance_score, schema_recipe
        )
        
        # Identify quality issues and recommendations
        quality_issues = self._identify_quality_issues(
            extracted_items, completeness_score, accuracy_score, consistency_score
        )
        recommendations = self._generate_recommendations(
            quality_issues, field_scores, schema_recipe
        )
        
        # Check if passes threshold
        passes_threshold = self._passes_quality_threshold(
            overall_score, completeness_score, accuracy_score, consistency_score
        )
        
        return QualityReport(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            relevance_score=relevance_score,
            field_scores=field_scores,
            quality_issues=quality_issues,
            recommendations=recommendations,
            passes_threshold=passes_threshold,
            item_count=len(extracted_items)
        )
    
    def filter_by_quality(
        self, 
        extracted_items: List[ExtractedContent],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> List[ExtractedContent]:
        """
        Filter extracted items based on quality thresholds.
        
        Args:
            extracted_items: List of extracted content items
            schema_recipe: Optional schema recipe for validation
            
        Returns:
            Filtered list of high-quality items
        """
        filtered_items = []
        
        for item in extracted_items:
            # Calculate individual item quality
            item_quality = self._calculate_item_quality(item, schema_recipe)
            
            # Check if item meets quality thresholds
            if self._item_passes_threshold(item, item_quality):
                filtered_items.append(item)
        
        return filtered_items
    
    def _calculate_completeness_score(
        self, 
        extracted_items: List[ExtractedContent],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> float:
        """Calculate completeness score based on field presence."""
        if not extracted_items:
            return 0.0
        
        # Get expected fields from schema recipe or from first item
        if schema_recipe:
            expected_fields = set(schema_recipe.fields.keys())
        else:
            # Use union of all fields found across items
            expected_fields = set()
            for item in extracted_items:
                expected_fields.update(item.data.keys())
        
        if not expected_fields:
            return 0.0
        
        total_completeness = 0.0
        
        for item in extracted_items:
            present_fields = 0
            for field in expected_fields:
                if field in item.data and self._is_field_complete(item.data[field]):
                    present_fields += 1
            
            item_completeness = (present_fields / len(expected_fields)) * 100.0
            total_completeness += item_completeness
        
        return total_completeness / len(extracted_items)
    
    def _calculate_accuracy_score(
        self, 
        extracted_items: List[ExtractedContent],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> float:
        """Calculate accuracy score based on data validity."""
        if not extracted_items:
            return 0.0
        
        total_accuracy = 0.0
        
        for item in extracted_items:
            field_accuracies = []
            
            for field_name, value in item.data.items():
                field_accuracy = self._calculate_field_accuracy(
                    field_name, value, schema_recipe
                )
                field_accuracies.append(field_accuracy)
            
            if field_accuracies:
                item_accuracy = sum(field_accuracies) / len(field_accuracies)
                total_accuracy += item_accuracy
        
        return (total_accuracy / len(extracted_items)) * 100.0
    
    def _calculate_consistency_score(self, extracted_items: List[ExtractedContent]) -> float:
        """Calculate consistency score based on data patterns."""
        if len(extracted_items) < 2:
            return 100.0  # Single item is perfectly consistent
        
        # Group fields by name
        field_values = {}
        for item in extracted_items:
            for field_name, value in item.data.items():
                if field_name not in field_values:
                    field_values[field_name] = []
                field_values[field_name].append(value)
        
        field_consistencies = []
        
        for field_name, values in field_values.items():
            consistency = self._calculate_field_consistency(values)
            field_consistencies.append(consistency)
        
        if not field_consistencies:
            return 0.0
        
        return (sum(field_consistencies) / len(field_consistencies)) * 100.0
    
    def _calculate_relevance_score(
        self, 
        extracted_items: List[ExtractedContent],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> float:
        """Calculate relevance score based on content quality."""
        if not extracted_items:
            return 0.0
        
        total_relevance = 0.0
        
        for item in extracted_items:
            item_relevance = 0.0
            field_count = 0
            
            for field_name, value in item.data.items():
                if self._is_field_complete(value):
                    relevance = self._calculate_field_relevance(field_name, value)
                    item_relevance += relevance
                    field_count += 1
            
            if field_count > 0:
                item_relevance = item_relevance / field_count
            
            total_relevance += item_relevance
        
        return (total_relevance / len(extracted_items)) * 100.0
    
    def _calculate_field_scores(
        self, 
        extracted_items: List[ExtractedContent],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> Dict[str, float]:
        """Calculate quality scores for individual fields."""
        field_scores = {}
        
        # Get all field names
        all_fields = set()
        for item in extracted_items:
            all_fields.update(item.data.keys())
        
        for field_name in all_fields:
            field_values = []
            for item in extracted_items:
                if field_name in item.data:
                    field_values.append(item.data[field_name])
            
            if field_values:
                # Calculate field-specific metrics
                completeness = sum(1 for v in field_values if self._is_field_complete(v)) / len(field_values)
                accuracy = sum(self._calculate_field_accuracy(field_name, v, schema_recipe) 
                             for v in field_values) / len(field_values)
                consistency = self._calculate_field_consistency(field_values)
                
                # Weighted average
                field_score = (completeness * 0.4 + accuracy * 0.4 + consistency * 0.2) * 100.0
                field_scores[field_name] = field_score
        
        return field_scores
    
    def _calculate_overall_score(
        self, 
        completeness: float, 
        accuracy: float, 
        consistency: float,
        relevance: float,
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> float:
        """Calculate weighted overall quality score."""
        # Use schema recipe weights if available
        if schema_recipe and schema_recipe.quality_weights:
            weights = schema_recipe.quality_weights
        else:
            weights = {"completeness": 0.3, "accuracy": 0.3, "consistency": 0.2, "relevance": 0.2}
        
        overall_score = (
            completeness * weights.get("completeness", 0.3) +
            accuracy * weights.get("accuracy", 0.3) +
            consistency * weights.get("consistency", 0.2) +
            relevance * weights.get("relevance", 0.2)
        )
        
        return min(100.0, max(0.0, overall_score))
    
    def _is_field_complete(self, value: Any) -> bool:
        """Check if a field value is complete (not empty or null)."""
        if value is None:
            return False
        
        if isinstance(value, str):
            return len(value.strip()) > 0
        
        if isinstance(value, (list, dict)):
            return len(value) > 0
        
        return True
    
    def _calculate_field_accuracy(
        self, 
        field_name: str, 
        value: Any,
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> float:
        """Calculate accuracy score for a single field value."""
        if not self._is_field_complete(value):
            return 0.0
        
        accuracy = 1.0
        
        # Check against validation patterns
        if isinstance(value, str):
            # Check for suspicious patterns
            for pattern in self.quality_indicators['suspicious_patterns']:
                if re.match(pattern, value):
                    accuracy *= 0.1
                    break
            
            # Check length constraints
            length = len(value.strip())
            if length < self.quality_indicators['min_length']:
                accuracy *= 0.5
            elif length > self.quality_indicators['max_length']:
                accuracy *= 0.8
            
            # Check word count for text fields
            if field_name in ['description', 'content', 'summary']:
                word_count = len(value.split())
                if word_count < self.quality_indicators['min_word_count']:
                    accuracy *= 0.7
                elif word_count > self.quality_indicators['max_word_count']:
                    accuracy *= 0.9
            
            # Check field-specific patterns
            field_type = self._infer_field_type(field_name)
            if field_type in self.validation_patterns:
                pattern = self.validation_patterns[field_type]
                if not re.match(pattern, value, re.IGNORECASE):
                    accuracy *= 0.6
        
        # Check schema recipe validation if available
        if schema_recipe and field_name in schema_recipe.fields:
            field_def = schema_recipe.fields[field_name]
            if field_def.validation_pattern:
                if isinstance(value, str) and not re.match(field_def.validation_pattern, value):
                    accuracy *= 0.5
        
        return min(1.0, accuracy)
    
    def _calculate_field_consistency(self, values: List[Any]) -> float:
        """Calculate consistency score for a field across multiple items."""
        if len(values) < 2:
            return 1.0
        
        # Filter out empty values
        valid_values = [v for v in values if self._is_field_complete(v)]
        if len(valid_values) < 2:
            return 1.0
        
        consistency_score = 1.0
        
        # Check type consistency
        types = [type(v).__name__ for v in valid_values]
        type_consistency = len(set(types)) / len(types)
        consistency_score *= type_consistency
        
        # For string values, check format consistency
        if all(isinstance(v, str) for v in valid_values):
            # Check length consistency
            lengths = [len(v) for v in valid_values]
            if lengths:
                length_variance = statistics.variance(lengths) if len(lengths) > 1 else 0
                avg_length = statistics.mean(lengths)
                if avg_length > 0:
                    length_consistency = 1.0 - min(1.0, length_variance / (avg_length ** 2))
                    consistency_score *= length_consistency
            
            # Check pattern consistency (e.g., all URLs, all emails)
            patterns_matched = {}
            for pattern_name, pattern in self.validation_patterns.items():
                matches = sum(1 for v in valid_values if re.match(pattern, v, re.IGNORECASE))
                if matches > 0:
                    patterns_matched[pattern_name] = matches / len(valid_values)
            
            if patterns_matched:
                # If values match a pattern, they should all match it
                max_pattern_match = max(patterns_matched.values())
                consistency_score *= max_pattern_match
        
        return consistency_score
    
    def _calculate_field_relevance(self, field_name: str, value: Any) -> float:
        """Calculate relevance score for a field value."""
        if not self._is_field_complete(value):
            return 0.0
        
        relevance = 1.0
        
        # Field name relevance (semantic meaning)
        important_fields = ['title', 'name', 'price', 'description', 'url', 'date']
        if field_name.lower() in important_fields:
            relevance *= 1.2
        
        # Content relevance for text fields
        if isinstance(value, str) and len(value) > 10:
            # Check for meaningful content
            word_count = len(value.split())
            if word_count >= 3:
                relevance *= 1.1
            
            # Check for informative content (not just filler)
            filler_words = ['lorem', 'ipsum', 'placeholder', 'example', 'test', 'sample']
            if not any(filler in value.lower() for filler in filler_words):
                relevance *= 1.1
        
        return min(1.0, relevance)
    
    def _infer_field_type(self, field_name: str) -> str:
        """Infer field type from field name."""
        field_name_lower = field_name.lower()
        
        if 'email' in field_name_lower:
            return 'email'
        elif 'url' in field_name_lower or 'link' in field_name_lower:
            return 'url'
        elif 'phone' in field_name_lower or 'tel' in field_name_lower:
            return 'phone'
        elif 'price' in field_name_lower or 'cost' in field_name_lower:
            return 'price'
        elif 'date' in field_name_lower or 'time' in field_name_lower:
            return 'date'
        elif 'number' in field_name_lower or 'count' in field_name_lower:
            return 'number'
        else:
            return 'text'
    
    def _identify_quality_issues(
        self, 
        extracted_items: List[ExtractedContent],
        completeness: float,
        accuracy: float,
        consistency: float
    ) -> List[str]:
        """Identify specific quality issues in the extracted data."""
        issues = []
        
        # Completeness issues
        if completeness < 50.0:
            issues.append(f"Low completeness score ({completeness:.1f}%) - many fields are missing data")
        
        # Accuracy issues
        if accuracy < 60.0:
            issues.append(f"Low accuracy score ({accuracy:.1f}%) - data may contain errors or invalid formats")
        
        # Consistency issues
        if consistency < 40.0:
            issues.append(f"Low consistency score ({consistency:.1f}%) - data formats vary significantly between items")
        
        # Check for specific field issues
        field_issues = self._analyze_field_issues(extracted_items)
        issues.extend(field_issues)
        
        # Check for required fields
        if self.thresholds.required_fields:
            missing_required = []
            for item in extracted_items:
                for required_field in self.thresholds.required_fields:
                    if required_field not in item.data or not self._is_field_complete(item.data[required_field]):
                        if required_field not in missing_required:
                            missing_required.append(required_field)
            
            if missing_required:
                issues.append(f"Required fields missing: {', '.join(missing_required)}")
        
        return issues
    
    def _analyze_field_issues(self, extracted_items: List[ExtractedContent]) -> List[str]:
        """Analyze field-specific quality issues."""
        issues = []
        
        # Collect all field values
        field_values = {}
        for item in extracted_items:
            for field_name, value in item.data.items():
                if field_name not in field_values:
                    field_values[field_name] = []
                field_values[field_name].append(value)
        
        for field_name, values in field_values.items():
            # Check for high percentage of empty values
            empty_count = sum(1 for v in values if not self._is_field_complete(v))
            empty_percentage = (empty_count / len(values)) * 100
            
            if empty_percentage > 50:
                issues.append(f"Field '{field_name}' is empty in {empty_percentage:.1f}% of items")
            
            # Check for suspicious patterns
            valid_values = [v for v in values if self._is_field_complete(v) and isinstance(v, str)]
            if valid_values:
                suspicious_count = 0
                for value in valid_values:
                    for pattern in self.quality_indicators['suspicious_patterns']:
                        if re.match(pattern, value):
                            suspicious_count += 1
                            break
                
                if suspicious_count > len(valid_values) * 0.3:
                    issues.append(f"Field '{field_name}' contains suspicious or low-quality content")
        
        return issues
    
    def _generate_recommendations(
        self, 
        quality_issues: List[str],
        field_scores: Dict[str, float],
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []
        
        # General recommendations based on issues
        if any("completeness" in issue.lower() for issue in quality_issues):
            recommendations.append("Review extraction selectors to ensure they match the target content")
            recommendations.append("Consider adding fallback selectors for better field coverage")
        
        if any("accuracy" in issue.lower() for issue in quality_issues):
            recommendations.append("Add validation patterns to filter out invalid data")
            recommendations.append("Implement post-processing steps to clean extracted data")
        
        if any("consistency" in issue.lower() for issue in quality_issues):
            recommendations.append("Standardize extraction rules across similar content types")
            recommendations.append("Add data normalization steps to ensure consistent formatting")
        
        # Field-specific recommendations
        low_quality_fields = [field for field, score in field_scores.items() if score < 60.0]
        if low_quality_fields:
            recommendations.append(f"Focus on improving extraction for fields: {', '.join(low_quality_fields)}")
        
        # Schema-specific recommendations
        if schema_recipe:
            required_fields = schema_recipe.get_required_fields()
            if required_fields:
                recommendations.append(f"Ensure required fields are properly extracted: {', '.join(required_fields)}")
        
        return recommendations
    
    def _passes_quality_threshold(
        self, 
        overall_score: float,
        completeness: float,
        accuracy: float,
        consistency: float
    ) -> bool:
        """Check if quality scores meet the configured thresholds."""
        return (
            overall_score >= self.thresholds.minimum_overall and
            completeness >= self.thresholds.minimum_completeness and
            accuracy >= self.thresholds.minimum_accuracy and
            consistency >= self.thresholds.minimum_consistency
        )
    
    def _calculate_item_quality(
        self, 
        item: ExtractedContent,
        schema_recipe: Optional[SchemaRecipe] = None
    ) -> float:
        """Calculate quality score for a single item."""
        # Use the item's existing quality score if available
        if hasattr(item, 'quality_score') and item.quality_score is not None:
            return item.quality_score
        
        # Calculate based on field completeness and accuracy
        if not item.data:
            return 0.0
        
        field_scores = []
        for field_name, value in item.data.items():
            if self._is_field_complete(value):
                accuracy = self._calculate_field_accuracy(field_name, value, schema_recipe)
                field_scores.append(accuracy * 100.0)
        
        return sum(field_scores) / len(field_scores) if field_scores else 0.0
    
    def _item_passes_threshold(self, item: ExtractedContent, item_quality: float) -> bool:
        """Check if an individual item passes quality thresholds."""
        # Check overall quality
        if item_quality < self.thresholds.minimum_overall:
            return False
        
        # Check required fields
        if self.thresholds.required_fields:
            for required_field in self.thresholds.required_fields:
                if required_field not in item.data or not self._is_field_complete(item.data[required_field]):
                    return False
        
        return True
    
    def update_thresholds(self, thresholds: QualityThresholds) -> None:
        """Update quality thresholds."""
        self.thresholds = thresholds
    
    def get_quality_metrics(self, extracted_items: List[ExtractedContent]) -> ContentQualityMetrics:
        """
        Get quality metrics in the ContentQualityMetrics format.
        
        Args:
            extracted_items: List of extracted content items
            
        Returns:
            ContentQualityMetrics object
        """
        if not extracted_items:
            return ContentQualityMetrics(
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                relevance_score=0.0
            )
        
        completeness = self._calculate_completeness_score(extracted_items)
        accuracy = self._calculate_accuracy_score(extracted_items)
        consistency = self._calculate_consistency_score(extracted_items)
        relevance = self._calculate_relevance_score(extracted_items)
        
        return ContentQualityMetrics(
            completeness_score=completeness,
            accuracy_score=accuracy,
            consistency_score=consistency,
            relevance_score=relevance
        )