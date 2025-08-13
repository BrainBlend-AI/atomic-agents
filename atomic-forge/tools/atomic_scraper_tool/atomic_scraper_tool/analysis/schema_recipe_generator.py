"""
Dynamic schema recipe generator for the atomic scraper tool.

Creates JSON schemas from website analysis and identifies data patterns and types.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
from atomic_scraper_tool.analysis.website_analyzer import WebsiteStructureAnalysis, ContentPattern


@dataclass
class FieldPattern:
    """Represents a detected field pattern in the content."""
    field_name: str
    field_type: str  # 'string', 'number', 'array', 'object', 'boolean'
    selectors: List[str]
    sample_values: List[str]
    confidence: float
    importance_score: float
    data_pattern: Optional[str] = None  # Regex pattern for validation


@dataclass
class SchemaGenerationContext:
    """Context for schema generation."""
    user_criteria: str
    target_content_type: str
    sample_html: str
    quality_requirements: Dict[str, float]
    field_preferences: List[str] = None  # Preferred field names
    
    def __post_init__(self):
        if self.field_preferences is None:
            self.field_preferences = []


class SchemaRecipeGenerator:
    """Generates dynamic schema recipes based on website analysis."""
    
    def __init__(self):
        """Initialize the schema recipe generator."""
        self.field_type_patterns = {
            'number': [
                r'^\$?\d+\.?\d*$',  # Price/currency
                r'^\d+$',  # Integer
                r'^\d+\.\d+$',  # Decimal
                r'^\d+%$',  # Percentage
            ],
            'boolean': [
                r'^(true|false)$',
                r'^(yes|no)$',
                r'^(on|off)$',
                r'^(enabled|disabled)$',
            ],
            'date': [
                r'\d{4}-\d{2}-\d{2}',  # ISO date
                r'\d{1,2}/\d{1,2}/\d{4}',  # US date
                r'\d{1,2}-\d{1,2}-\d{4}',  # European date
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month names
            ],
            'url': [
                r'^https?://',
                r'^www\.',
                r'\.(com|org|net|edu|gov)',
            ],
            'email': [
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            ],
            'phone': [
                r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123) 456-7890
                r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
                r'\+\d{1,3}\s?\d{3,4}\s?\d{3,4}',  # International
            ]
        }
        
        self.field_name_patterns = {
            'title': ['title', 'name', 'heading', 'header', 'subject'],
            'description': ['description', 'summary', 'content', 'text', 'body', 'excerpt'],
            'price': ['price', 'cost', 'amount', 'fee', 'rate', 'value'],
            'date': ['date', 'time', 'when', 'published', 'created', 'updated'],
            'location': ['location', 'address', 'place', 'venue', 'where'],
            'contact': ['contact', 'phone', 'email', 'tel', 'mail'],
            'image': ['image', 'photo', 'picture', 'img', 'thumbnail'],
            'link': ['link', 'url', 'href', 'website'],
            'category': ['category', 'type', 'kind', 'genre', 'class'],
            'author': ['author', 'by', 'creator', 'writer', 'publisher'],
            'rating': ['rating', 'score', 'stars', 'review', 'grade'],
            'status': ['status', 'state', 'condition', 'availability']
        }
        
        self.quality_weights = {
            'title': 0.9,
            'description': 0.8,
            'price': 0.85,
            'date': 0.7,
            'location': 0.75,
            'contact': 0.8,
            'image': 0.6,
            'link': 0.5,
            'category': 0.65,
            'author': 0.6,
            'rating': 0.7,
            'status': 0.65
        }
    
    def generate_schema_recipe(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: SchemaGenerationContext
    ) -> SchemaRecipe:
        """
        Generate a dynamic schema recipe based on website analysis.
        
        Args:
            analysis: Website structure analysis
            context: Schema generation context
            
        Returns:
            SchemaRecipe object with field definitions
        """
        # Detect field patterns from the HTML content
        field_patterns = self._detect_field_patterns(context.sample_html, analysis)
        
        # Filter and prioritize fields based on context
        relevant_patterns = self._filter_relevant_patterns(field_patterns, context)
        
        # Generate field definitions
        field_definitions = self._generate_field_definitions(relevant_patterns, context)
        
        # Calculate quality weights
        quality_weights = self._calculate_quality_weights(field_definitions, context)
        
        # Generate validation rules
        validation_rules = self._generate_validation_rules(field_definitions, context)
        
        # Create schema name and description
        schema_name = self._generate_schema_name(context)
        schema_description = self._generate_schema_description(context, field_definitions)
        
        return SchemaRecipe(
            name=schema_name,
            description=schema_description,
            fields=field_definitions,
            validation_rules=validation_rules,
            quality_weights=quality_weights,
            version="1.0"
        )
    
    def _detect_field_patterns(
        self, 
        html_content: str, 
        analysis: WebsiteStructureAnalysis
    ) -> List[FieldPattern]:
        """Detect field patterns in the HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        patterns = []
        
        # Find repeated content structures
        content_containers = self._find_content_containers(soup, analysis)
        
        for container in content_containers:
            container_patterns = self._analyze_container_fields(container)
            patterns.extend(container_patterns)
        
        # Deduplicate and merge similar patterns
        merged_patterns = self._merge_similar_patterns(patterns)
        
        return merged_patterns
    
    def _find_content_containers(
        self, 
        soup: BeautifulSoup, 
        analysis: WebsiteStructureAnalysis
    ) -> List[Tag]:
        """Find containers that likely contain structured content."""
        containers = []
        
        # Use detected list containers from analysis
        for selector in analysis.list_containers:
            elements = soup.select(selector)
            containers.extend(elements)
        
        # Look for repeated item patterns
        for selector in analysis.item_selectors:
            elements = soup.select(selector)
            if len(elements) >= 2:  # At least 2 similar items
                containers.extend(elements[:3])  # Sample first 3
        
        # If no containers found, use content patterns
        if not containers:
            for pattern in analysis.content_patterns:
                if pattern.pattern_type in ['list', 'product', 'article']:
                    elements = soup.select(pattern.selector)
                    containers.extend(elements[:2])
        
        return containers[:10]  # Limit to 10 containers for analysis
    
    def _analyze_container_fields(self, container: Tag) -> List[FieldPattern]:
        """Analyze fields within a content container."""
        patterns = []
        
        # Find all text-containing elements
        text_elements = container.find_all(text=True)
        text_elements = [elem.parent for elem in text_elements 
                        if elem.parent and elem.strip() and len(elem.strip()) > 2]
        
        # Group elements by tag and class patterns
        element_groups = self._group_similar_elements(text_elements)
        
        for group in element_groups:
            if len(group) >= 1:  # At least one element
                pattern = self._create_field_pattern_from_group(group)
                if pattern:
                    patterns.append(pattern)
        
        # Look for specific attribute patterns (href, src, etc.)
        attribute_patterns = self._detect_attribute_patterns(container)
        patterns.extend(attribute_patterns)
        
        return patterns
    
    def _group_similar_elements(self, elements: List[Tag]) -> List[List[Tag]]:
        """Group similar elements together."""
        groups = {}
        
        for element in elements:
            # Create a signature based on tag, class, and position
            classes = tuple(sorted(element.get('class', [])))
            tag = element.name
            
            # Consider parent context for better grouping
            parent_classes = tuple(sorted(element.parent.get('class', []))) if element.parent else ()
            
            key = (tag, classes, parent_classes)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(element)
        
        # Return groups with at least one element
        return [group for group in groups.values() if len(group) >= 1]
    
    def _create_field_pattern_from_group(self, elements: List[Tag]) -> Optional[FieldPattern]:
        """Create a field pattern from a group of similar elements."""
        if not elements:
            return None
        
        first_element = elements[0]
        
        # Extract sample values
        sample_values = []
        for elem in elements[:5]:  # Sample up to 5 values
            text = elem.get_text().strip()
            if text:
                sample_values.append(text)
        
        if not sample_values:
            return None
        
        # Determine field name based on element characteristics
        field_name = self._infer_field_name(first_element, sample_values)
        
        # Determine field type based on sample values
        field_type = self._infer_field_type(sample_values)
        
        # Generate selectors
        selectors = self._generate_selectors_for_group(elements)
        
        # Calculate confidence based on consistency
        confidence = self._calculate_pattern_confidence(elements, sample_values)
        
        # Calculate importance score
        importance_score = self._calculate_importance_score(field_name, first_element, sample_values)
        
        # Detect data pattern for validation
        data_pattern = self._detect_data_pattern(sample_values, field_type)
        
        return FieldPattern(
            field_name=field_name,
            field_type=field_type,
            selectors=selectors,
            sample_values=sample_values,
            confidence=confidence,
            importance_score=importance_score,
            data_pattern=data_pattern
        )
    
    def _detect_attribute_patterns(self, container: Tag) -> List[FieldPattern]:
        """Detect patterns in element attributes (href, src, etc.)."""
        patterns = []
        
        # Look for links
        links = container.find_all('a', href=True)
        if links:
            hrefs = [link.get('href') for link in links if link.get('href')]
            if hrefs:
                patterns.append(FieldPattern(
                    field_name='link',
                    field_type='string',
                    selectors=['a[href]'],
                    sample_values=hrefs[:3],
                    confidence=0.9,
                    importance_score=0.5,
                    data_pattern=None
                ))
        
        # Look for images
        images = container.find_all('img', src=True)
        if images:
            srcs = [img.get('src') for img in images if img.get('src')]
            if srcs:
                patterns.append(FieldPattern(
                    field_name='image',
                    field_type='string',
                    selectors=['img[src]'],
                    sample_values=srcs[:3],
                    confidence=0.9,
                    importance_score=0.6,
                    data_pattern=None
                ))
        
        return patterns
    
    def _infer_field_name(self, element: Tag, sample_values: List[str]) -> str:
        """Infer field name based on element characteristics and content."""
        # Check element classes and IDs
        classes = element.get('class', [])
        element_id = element.get('id', '')
        
        # Check for semantic field names in classes/IDs
        for field_type, keywords in self.field_name_patterns.items():
            for keyword in keywords:
                # Check in classes
                if any(keyword in cls.lower() for cls in classes):
                    return field_type
                # Check in ID
                if keyword in element_id.lower():
                    return field_type
        
        # Check parent element for context
        if element.parent:
            parent_classes = element.parent.get('class', [])
            parent_id = element.parent.get('id', '')
            
            for field_type, keywords in self.field_name_patterns.items():
                for keyword in keywords:
                    if any(keyword in cls.lower() for cls in parent_classes):
                        return field_type
                    if keyword in parent_id.lower():
                        return field_type
        
        # Analyze sample values for patterns
        for field_type, patterns in self.field_type_patterns.items():
            if field_type in ['number', 'date', 'url', 'email', 'phone']:
                for pattern in patterns:
                    if any(re.search(pattern, value, re.IGNORECASE) for value in sample_values):
                        return field_type
        
        # Check tag name for semantic meaning
        tag_name = element.name.lower()
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return 'title'
        elif tag_name == 'p':
            return 'description'
        elif tag_name == 'time':
            return 'date'
        
        # Default based on content characteristics
        if sample_values:
            avg_length = sum(len(val) for val in sample_values) / len(sample_values)
            if avg_length < 50:
                return 'title'
            else:
                return 'description'
        
        return 'content'
    
    def _infer_field_type(self, sample_values: List[str]) -> str:
        """Infer field type based on sample values."""
        if not sample_values:
            return 'string'
        
        # Check for specific patterns
        for field_type, patterns in self.field_type_patterns.items():
            match_count = 0
            for value in sample_values:
                if any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns):
                    match_count += 1
            
            # If majority of values match a pattern, use that type
            if match_count >= len(sample_values) * 0.6:
                if field_type in ['date', 'url', 'email', 'phone']:
                    return 'string'  # These are still strings, just with patterns
                return field_type
        
        # Check for arrays (comma-separated values)
        if any(',' in value for value in sample_values):
            return 'array'
        
        # Default to string
        return 'string'
    
    def _generate_selectors_for_group(self, elements: List[Tag]) -> List[str]:
        """Generate CSS selectors for a group of elements."""
        selectors = []
        
        if not elements:
            return selectors
        
        first_element = elements[0]
        
        # Try ID selector
        if first_element.get('id'):
            selectors.append(f"#{first_element.get('id')}")
        
        # Try class selector
        classes = first_element.get('class', [])
        if classes:
            class_selector = '.' + '.'.join(classes)
            selectors.append(f"{first_element.name}{class_selector}")
        
        # Try tag selector
        selectors.append(first_element.name)
        
        # Try attribute selectors
        for attr in ['data-field', 'data-type', 'role']:
            if first_element.get(attr):
                selectors.append(f"{first_element.name}[{attr}='{first_element.get(attr)}']")
        
        return selectors[:3]  # Limit to top 3 selectors
    
    def _calculate_pattern_confidence(self, elements: List[Tag], sample_values: List[str]) -> float:
        """Calculate confidence score for a field pattern."""
        base_confidence = 0.5
        
        # Boost confidence for multiple similar elements
        if len(elements) > 1:
            base_confidence += min(0.3, len(elements) * 0.1)
        
        # Boost confidence for consistent value patterns
        if sample_values:
            # Check if values have similar lengths
            lengths = [len(val) for val in sample_values]
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
                if length_variance < avg_length * 0.5:  # Low variance
                    base_confidence += 0.2
        
        # Boost confidence for semantic elements
        first_element = elements[0] if elements else None
        if first_element:
            if first_element.name in ['h1', 'h2', 'h3', 'time', 'address']:
                base_confidence += 0.2
            
            # Boost for semantic classes
            classes = first_element.get('class', [])
            semantic_classes = ['title', 'name', 'price', 'date', 'location', 'description']
            if any(sem_class in ' '.join(classes).lower() for sem_class in semantic_classes):
                base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    def _calculate_importance_score(
        self, 
        field_name: str, 
        element: Tag, 
        sample_values: List[str]
    ) -> float:
        """Calculate importance score for a field."""
        # Base importance from field type
        base_importance = self.quality_weights.get(field_name, 0.5)
        
        # Boost for heading elements
        if element.name in ['h1', 'h2', 'h3']:
            base_importance += 0.2
        
        # Boost for elements with semantic classes
        classes = element.get('class', [])
        if any('main' in cls.lower() or 'primary' in cls.lower() for cls in classes):
            base_importance += 0.1
        
        # Boost for required-looking fields
        if any(keyword in field_name for keyword in ['title', 'name', 'price']):
            base_importance += 0.1
        
        # Reduce importance for very short or very long content
        if sample_values:
            avg_length = sum(len(val) for val in sample_values) / len(sample_values)
            if avg_length < 5 or avg_length > 500:
                base_importance -= 0.1
        
        return max(0.1, min(1.0, base_importance))
    
    def _detect_data_pattern(self, sample_values: List[str], field_type: str) -> Optional[str]:
        """Detect regex pattern for data validation."""
        if not sample_values or field_type != 'string':
            return None
        
        # Check for common patterns
        for pattern_type, patterns in self.field_type_patterns.items():
            for pattern in patterns:
                if all(re.search(pattern, value, re.IGNORECASE) for value in sample_values):
                    return pattern
        
        return None
    
    def _merge_similar_patterns(self, patterns: List[FieldPattern]) -> List[FieldPattern]:
        """Merge similar field patterns to avoid duplicates."""
        if not patterns:
            return patterns
        
        merged = {}
        
        for pattern in patterns:
            # Create a key based on field name and type
            key = (pattern.field_name, pattern.field_type)
            
            if key not in merged:
                merged[key] = pattern
            else:
                # Merge with existing pattern
                existing = merged[key]
                
                # Combine selectors
                combined_selectors = list(set(existing.selectors + pattern.selectors))
                
                # Combine sample values
                combined_samples = list(set(existing.sample_values + pattern.sample_values))
                
                # Use higher confidence
                combined_confidence = max(existing.confidence, pattern.confidence)
                
                # Use higher importance
                combined_importance = max(existing.importance_score, pattern.importance_score)
                
                merged[key] = FieldPattern(
                    field_name=existing.field_name,
                    field_type=existing.field_type,
                    selectors=combined_selectors[:5],  # Limit selectors
                    sample_values=combined_samples[:5],  # Limit samples
                    confidence=combined_confidence,
                    importance_score=combined_importance,
                    data_pattern=existing.data_pattern or pattern.data_pattern
                )
        
        return list(merged.values())
    
    def _filter_relevant_patterns(
        self, 
        patterns: List[FieldPattern], 
        context: SchemaGenerationContext
    ) -> List[FieldPattern]:
        """Filter patterns based on context and relevance."""
        if not patterns:
            return patterns
        
        # Sort by importance and confidence
        patterns.sort(key=lambda p: (p.importance_score * p.confidence), reverse=True)
        
        # Filter by user preferences
        if context.field_preferences:
            preferred_patterns = [p for p in patterns if p.field_name in context.field_preferences]
            other_patterns = [p for p in patterns if p.field_name not in context.field_preferences]
            patterns = preferred_patterns + other_patterns
        
        # Filter by context criteria
        criteria_lower = context.user_criteria.lower()
        
        # Boost patterns that match user criteria
        for pattern in patterns:
            if pattern.field_name in criteria_lower:
                pattern.importance_score *= 1.2
        
        # Limit to top patterns
        max_fields = 10
        return patterns[:max_fields]
    
    def _generate_field_definitions(
        self, 
        patterns: List[FieldPattern], 
        context: SchemaGenerationContext
    ) -> Dict[str, FieldDefinition]:
        """Generate field definitions from patterns."""
        field_definitions = {}
        
        for pattern in patterns:
            # Determine if field is required
            required = pattern.importance_score > 0.7
            
            # Choose best selector
            best_selector = pattern.selectors[0] if pattern.selectors else pattern.field_name
            
            # Generate description
            description = self._generate_field_description(pattern)
            
            # Generate post-processing steps
            post_processing = self._generate_post_processing_steps(pattern)
            
            field_def = FieldDefinition(
                field_type=pattern.field_type,
                description=description,
                extraction_selector=best_selector,
                validation_pattern=pattern.data_pattern,
                required=required,
                quality_weight=pattern.importance_score,
                post_processing=post_processing
            )
            
            field_definitions[pattern.field_name] = field_def
        
        return field_definitions
    
    def _generate_field_description(self, pattern: FieldPattern) -> str:
        """Generate a description for a field."""
        base_descriptions = {
            'title': 'The title or name of the item',
            'description': 'A description or summary of the item',
            'price': 'The price or cost of the item',
            'date': 'Date or time information',
            'location': 'Location or address information',
            'contact': 'Contact information (phone, email, etc.)',
            'image': 'Image URL or source',
            'link': 'Link or URL to more information',
            'category': 'Category or classification',
            'author': 'Author or creator information',
            'rating': 'Rating or score',
            'status': 'Status or availability information'
        }
        
        base_desc = base_descriptions.get(pattern.field_name, f'{pattern.field_name.title()} information')
        
        # Add type information
        if pattern.field_type != 'string':
            base_desc += f' ({pattern.field_type})'
        
        return base_desc
    
    def _generate_post_processing_steps(self, pattern: FieldPattern) -> List[str]:
        """Generate post-processing steps for a field."""
        steps = ['trim']  # Always trim whitespace
        
        # Add field-specific processing
        if pattern.field_name in ['title', 'description']:
            steps.append('clean')
        
        if pattern.field_name == 'price':
            steps.extend(['clean', 'extract_numbers'])
        
        if pattern.field_name in ['email', 'link']:
            steps.append('validate')
        
        if pattern.field_type == 'array':
            steps.append('normalize')
        
        return steps
    
    def _calculate_quality_weights(
        self, 
        field_definitions: Dict[str, FieldDefinition], 
        context: SchemaGenerationContext
    ) -> Dict[str, float]:
        """Calculate quality weights for the schema."""
        # Use context quality requirements if provided
        if context.quality_requirements:
            return context.quality_requirements
        
        # Default quality weights
        return {
            "completeness": 0.4,
            "accuracy": 0.4,
            "consistency": 0.2
        }
    
    def _generate_validation_rules(
        self, 
        field_definitions: Dict[str, FieldDefinition], 
        context: SchemaGenerationContext
    ) -> List[str]:
        """Generate validation rules for the schema."""
        rules = []
        
        # Add basic validation rules
        rules.append('normalize_whitespace')
        
        # Add rules based on required fields
        required_fields = [name for name, field_def in field_definitions.items() if field_def.required]
        if required_fields:
            rules.append('require_all_fields')
        else:
            rules.append('allow_partial_data')
        
        # Add content-specific rules
        if any(field_def.validation_pattern for field_def in field_definitions.values()):
            rules.append('validate_urls')
        
        return rules
    
    def _generate_schema_name(self, context: SchemaGenerationContext) -> str:
        """Generate a name for the schema."""
        # Extract key terms from user criteria
        criteria_words = re.findall(r'\b\w+\b', context.user_criteria.lower())
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'scrape', 'get', 'find'}
        key_words = [word for word in criteria_words if word not in stop_words and len(word) > 2]
        
        if key_words:
            name = '_'.join(key_words[:3])  # Use up to 3 key words
        else:
            name = context.target_content_type
        
        return f"{name}_schema"
    
    def _generate_schema_description(
        self, 
        context: SchemaGenerationContext, 
        field_definitions: Dict[str, FieldDefinition]
    ) -> str:
        """Generate a description for the schema."""
        field_count = len(field_definitions)
        field_names = list(field_definitions.keys())
        
        description = f"Schema for extracting {context.target_content_type} data"
        
        if context.user_criteria:
            description += f" based on criteria: '{context.user_criteria}'"
        
        description += f". Contains {field_count} fields: {', '.join(field_names[:5])}"
        
        if len(field_names) > 5:
            description += f" and {len(field_names) - 5} more"
        
        return description
    
    def optimize_schema_recipe(
        self, 
        recipe: SchemaRecipe, 
        analysis: WebsiteStructureAnalysis
    ) -> SchemaRecipe:
        """Optimize an existing schema recipe based on analysis."""
        # Create optimized field definitions
        optimized_fields = {}
        
        for field_name, field_def in recipe.fields.items():
            # Try to find better selectors based on analysis
            better_selector = self._find_better_selector(field_name, field_def, analysis)
            
            optimized_field = FieldDefinition(
                field_type=field_def.field_type,
                description=field_def.description,
                extraction_selector=better_selector or field_def.extraction_selector,
                validation_pattern=field_def.validation_pattern,
                required=field_def.required,
                quality_weight=field_def.quality_weight,
                post_processing=field_def.post_processing
            )
            
            optimized_fields[field_name] = optimized_field
        
        # Create optimized recipe
        return SchemaRecipe(
            name=recipe.name,
            description=recipe.description,
            fields=optimized_fields,
            validation_rules=recipe.validation_rules,
            quality_weights=recipe.quality_weights,
            version=recipe.version
        )
    
    def _find_better_selector(
        self, 
        field_name: str, 
        field_def: FieldDefinition, 
        analysis: WebsiteStructureAnalysis
    ) -> Optional[str]:
        """Find a better selector for a field based on analysis."""
        # This is a placeholder for more sophisticated selector optimization
        # Could analyze the actual HTML to find more specific selectors
        return None
    
    def validate_schema_recipe(self, recipe: SchemaRecipe) -> List[str]:
        """Validate a schema recipe and return any issues."""
        issues = []
        
        # Check for required fields
        if not recipe.fields:
            issues.append("Schema recipe has no fields defined")
        
        # Check field definitions
        for field_name, field_def in recipe.fields.items():
            if not field_def.extraction_selector:
                issues.append(f"Field '{field_name}' has no extraction selector")
            
            if field_def.quality_weight < 0 or field_def.quality_weight > 1:
                issues.append(f"Field '{field_name}' has invalid quality weight: {field_def.quality_weight}")
        
        # Check quality weights sum
        total_weight = sum(recipe.quality_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Quality weights don't sum to 1.0: {total_weight}")
        
        return issues