"""
Data processor with text cleaning and normalization capabilities.

Provides comprehensive data cleaning, type conversion, and validation functions
with configurable post-processing pipelines for different data types.
"""

import re
import html
import unicodedata
from typing import Dict, List, Optional, Any, Union, Callable
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Data processor with text cleaning and normalization methods.
    
    Provides configurable post-processing pipelines for different data types
    including text cleaning, data type conversion, and validation functions.
    """
    
    def __init__(self):
        """Initialize the data processor."""
        # Register built-in processing functions
        self.processors = {
            'clean': self._clean_text,
            'normalize': self._normalize_text,
            'validate': self._validate_text,
            'trim': self._trim_text,
            'lowercase': self._lowercase_text,
            'uppercase': self._uppercase_text,
            'strip_html': self._strip_html,
            'extract_numbers': self._extract_numbers,
            'extract_urls': self._extract_urls,
            'remove_duplicates': self._remove_duplicates,
            'normalize_whitespace': self._normalize_whitespace,
            'remove_empty_lines': self._remove_empty_lines,
            'decode_html': self._decode_html,
            'normalize_unicode': self._normalize_unicode,
            'extract_emails': self._extract_emails,
            'extract_phones': self._extract_phones,
            'format_price': self._format_price,
            'format_date': self._format_date,
            'capitalize_words': self._capitalize_words,
            'remove_extra_spaces': self._remove_extra_spaces,
            'filter_length': self._filter_by_length,
            'remove_special_chars': self._remove_special_chars,
            'extract_domain': self._extract_domain,
            'standardize_case': self._standardize_case
        }
        
        # Data type converters
        self.converters = {
            'string': self._to_string,
            'number': self._to_number,
            'float': self._to_float,
            'integer': self._to_integer,
            'boolean': self._to_boolean,
            'array': self._to_array,
            'url': self._to_url,
            'email': self._to_email,
            'phone': self._to_phone,
            'date': self._to_date
        }
        
        # Validation patterns
        self.validation_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
            'phone': r'(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            'price': r'^\$?\d+\.?\d*$',
            'date': r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}-\d{1,2}-\d{4}',
            'number': r'^\d+\.?\d*$',
            'integer': r'^\d+$'
        }
    
    def process_data(
        self, 
        data: Dict[str, Any], 
        processing_config: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Process data using field-specific processing pipelines.
        
        Args:
            data: Dictionary of field names to values
            processing_config: Dictionary mapping field names to processing step lists
            
        Returns:
            Processed data dictionary
        """
        processed_data = {}
        
        for field_name, value in data.items():
            if field_name in processing_config:
                processing_steps = processing_config[field_name]
                processed_value = self.process_field(value, processing_steps)
                processed_data[field_name] = processed_value
            else:
                processed_data[field_name] = value
        
        return processed_data
    
    def process_field(self, value: Any, processing_steps: List[str]) -> Any:
        """
        Process a single field value through a pipeline of processing steps.
        
        Args:
            value: Value to process
            processing_steps: List of processing step names
            
        Returns:
            Processed value
        """
        if value is None:
            return value
        
        processed_value = value
        
        for step in processing_steps:
            try:
                if step in self.processors:
                    processed_value = self.processors[step](processed_value)
                elif step.startswith('convert_'):
                    # Handle type conversion steps
                    target_type = step.replace('convert_', '')
                    if target_type in self.converters:
                        processed_value = self.converters[target_type](processed_value)
                    else:
                        logger.warning(f"Unknown conversion type: {target_type}")
                elif step.startswith('validate_'):
                    # Handle validation steps
                    pattern_name = step.replace('validate_', '')
                    if pattern_name in self.validation_patterns:
                        if not self._validate_pattern(processed_value, pattern_name):
                            logger.warning(f"Validation failed for {pattern_name}: {processed_value}")
                            processed_value = None
                    else:
                        logger.warning(f"Unknown validation pattern: {pattern_name}")
                else:
                    logger.warning(f"Unknown processing step: {step}")
            except Exception as e:
                logger.error(f"Error in processing step '{step}': {e}")
                # Continue with the current value if processing fails
        
        return processed_value
    
    def create_processing_pipeline(
        self, 
        field_type: str, 
        field_name: str,
        custom_steps: Optional[List[str]] = None
    ) -> List[str]:
        """
        Create a default processing pipeline for a field type and name.
        
        Args:
            field_type: Type of field ('string', 'number', 'url', etc.)
            field_name: Name of the field
            custom_steps: Optional custom processing steps to include
            
        Returns:
            List of processing step names
        """
        pipeline = []
        
        # Add common initial steps
        pipeline.extend(['trim', 'normalize_whitespace'])
        
        # Add field-type specific steps
        if field_type == 'string':
            if 'title' in field_name.lower() or 'name' in field_name.lower():
                pipeline.extend(['clean', 'capitalize_words'])
            elif 'description' in field_name.lower() or 'content' in field_name.lower():
                pipeline.extend(['clean', 'remove_empty_lines'])
            else:
                pipeline.append('clean')
        
        elif field_type == 'number':
            pipeline.extend(['extract_numbers', 'convert_number'])
        
        elif field_type == 'url':
            pipeline.extend(['validate_url', 'convert_url'])
        
        elif field_type == 'email':
            pipeline.extend(['lowercase', 'validate_email', 'convert_email'])
        
        elif field_type == 'phone':
            pipeline.extend(['extract_phones', 'convert_phone'])
        
        elif field_type == 'date':
            pipeline.extend(['format_date', 'convert_date'])
        
        # Add field-name specific steps
        if 'price' in field_name.lower():
            pipeline.extend(['format_price', 'validate_price'])
        
        if 'email' in field_name.lower():
            pipeline.extend(['lowercase', 'validate_email'])
        
        if 'url' in field_name.lower() or 'link' in field_name.lower():
            pipeline.append('validate_url')
        
        # Add custom steps if provided
        if custom_steps:
            pipeline.extend(custom_steps)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_pipeline = []
        for step in pipeline:
            if step not in seen:
                seen.add(step)
                unique_pipeline.append(step)
        
        return unique_pipeline
    
    def register_processor(self, name: str, processor_func: Callable[[Any], Any]) -> None:
        """
        Register a custom processing function.
        
        Args:
            name: Name of the processing step
            processor_func: Function that takes a value and returns processed value
        """
        self.processors[name] = processor_func
    
    def register_converter(self, name: str, converter_func: Callable[[Any], Any]) -> None:
        """
        Register a custom type converter function.
        
        Args:
            name: Name of the target type
            converter_func: Function that converts a value to the target type
        """
        self.converters[name] = converter_func
    
    # Built-in processing functions
    
    def _clean_text(self, text: Any) -> str:
        """Clean text by removing extra whitespace and unwanted characters."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove HTML tags first
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _normalize_text(self, text: Any) -> str:
        """Normalize text formatting."""
        if not isinstance(text, str):
            text = str(text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing punctuation
        text = re.sub(r'^[^\w]+|[^\w]+$', '', text)
        
        return text.strip()
    
    def _validate_text(self, text: Any) -> str:
        """Validate and clean text content."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove obviously invalid content
        if len(text.strip()) < 2:
            return ""
        
        # Remove text that's mostly punctuation
        alphanumeric_chars = len(re.sub(r'[^\w\s]', '', text))
        if alphanumeric_chars < len(text) * 0.3:
            return ""
        
        # Remove text that's mostly repeated characters
        if len(set(text.replace(' ', ''))) < 3:
            return ""
        
        return text
    
    def _trim_text(self, text: Any) -> str:
        """Trim whitespace from text."""
        if not isinstance(text, str):
            text = str(text)
        return text.strip()
    
    def _lowercase_text(self, text: Any) -> str:
        """Convert text to lowercase."""
        if not isinstance(text, str):
            text = str(text)
        return text.lower()
    
    def _uppercase_text(self, text: Any) -> str:
        """Convert text to uppercase."""
        if not isinstance(text, str):
            text = str(text)
        return text.upper()
    
    def _strip_html(self, text: Any) -> str:
        """Strip HTML tags from text."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        return text.strip()
    
    def _extract_numbers(self, text: Any) -> str:
        """Extract numbers from text."""
        if not isinstance(text, str):
            text = str(text)
        
        numbers = re.findall(r'\d+\.?\d*', text)
        return ' '.join(numbers)
    
    def _extract_urls(self, text: Any) -> List[str]:
        """Extract URLs from text."""
        if not isinstance(text, str):
            text = str(text)
        
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls
    
    def _remove_duplicates(self, items: Any) -> Any:
        """Remove duplicates from list while preserving order."""
        if isinstance(items, list):
            seen = set()
            unique_items = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    unique_items.append(item)
            return unique_items
        elif isinstance(items, str):
            # For strings, remove duplicate words
            words = items.split()
            seen = set()
            unique_words = []
            for word in words:
                if word.lower() not in seen:
                    seen.add(word.lower())
                    unique_words.append(word)
            return ' '.join(unique_words)
        else:
            return items
    
    def _normalize_whitespace(self, text: Any) -> str:
        """Normalize whitespace in text."""
        if not isinstance(text, str):
            text = str(text)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _remove_empty_lines(self, text: Any) -> str:
        """Remove empty lines from text."""
        if not isinstance(text, str):
            text = str(text)
        
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(non_empty_lines)
    
    def _decode_html(self, text: Any) -> str:
        """Decode HTML entities."""
        if not isinstance(text, str):
            text = str(text)
        
        return html.unescape(text)
    
    def _normalize_unicode(self, text: Any) -> str:
        """Normalize unicode characters."""
        if not isinstance(text, str):
            text = str(text)
        
        return unicodedata.normalize('NFKD', text)
    
    def _extract_emails(self, text: Any) -> List[str]:
        """Extract email addresses from text."""
        if not isinstance(text, str):
            text = str(text)
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails
    
    def _extract_phones(self, text: Any) -> List[str]:
        """Extract phone numbers from text."""
        if not isinstance(text, str):
            text = str(text)
        
        phone_patterns = [
            r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123) 456-7890
            r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
            r'\d{3}\.\d{3}\.\d{4}',  # 123.456.7890
            r'\+\d{1,3}\s?\d{3,4}\s?\d{3,4}',  # International
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return phones
    
    def _format_price(self, text: Any) -> str:
        """Format price text."""
        if not isinstance(text, str):
            text = str(text)
        
        # Extract price numbers
        price_match = re.search(r'\$?(\d+\.?\d*)', text)
        if price_match:
            price_num = price_match.group(1)
            # Ensure proper decimal formatting
            if '.' not in price_num:
                price_num += '.00'
            elif len(price_num.split('.')[1]) == 1:
                price_num += '0'
            return f"${price_num}"
        
        return text
    
    def _format_date(self, text: Any) -> str:
        """Format date text to standard format."""
        if not isinstance(text, str):
            text = str(text)
        
        # Try to parse common date formats
        date_patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', r'\1-\2-\3'),  # YYYY-MM-DD
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\3-\1-\2'),  # MM/DD/YYYY
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\3-\1-\2'),  # MM-DD-YYYY
        ]
        
        for pattern, replacement in date_patterns:
            match = re.search(pattern, text)
            if match:
                return re.sub(pattern, replacement, text)
        
        return text
    
    def _capitalize_words(self, text: Any) -> str:
        """Capitalize words in text."""
        if not isinstance(text, str):
            text = str(text)
        
        return text.title()
    
    def _remove_extra_spaces(self, text: Any) -> str:
        """Remove extra spaces from text."""
        if not isinstance(text, str):
            text = str(text)
        
        return re.sub(r'\s{2,}', ' ', text).strip()
    
    def _filter_by_length(self, text: Any, min_length: int = 1, max_length: int = 10000) -> str:
        """Filter text by length constraints."""
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) < min_length or len(text) > max_length:
            return ""
        
        return text
    
    def _remove_special_chars(self, text: Any) -> str:
        """Remove special characters from text."""
        if not isinstance(text, str):
            text = str(text)
        
        # Keep only alphanumeric characters, spaces, and basic punctuation
        return re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
    
    def _extract_domain(self, url: Any) -> str:
        """Extract domain from URL."""
        if not isinstance(url, str):
            url = str(url)
        
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return url
    
    def _standardize_case(self, text: Any) -> str:
        """Standardize text case (sentence case)."""
        if not isinstance(text, str):
            text = str(text)
        
        # Convert to lowercase and capitalize first letter
        text = text.lower()
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    # Type conversion functions
    
    def _to_string(self, value: Any) -> str:
        """Convert value to string."""
        if value is None:
            return ""
        return str(value)
    
    def _to_number(self, value: Any) -> Union[int, float, None]:
        """Convert value to number (int or float)."""
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            # Extract numbers from string
            numbers = re.findall(r'\d+\.?\d*', value)
            if numbers:
                num_str = numbers[0]
                try:
                    if '.' in num_str:
                        return float(num_str)
                    else:
                        return int(num_str)
                except ValueError:
                    pass
        
        return None
    
    def _to_float(self, value: Any) -> Optional[float]:
        """Convert value to float."""
        if isinstance(value, float):
            return value
        
        if isinstance(value, int):
            return float(value)
        
        if isinstance(value, str):
            numbers = re.findall(r'\d+\.?\d*', value)
            if numbers:
                try:
                    return float(numbers[0])
                except ValueError:
                    pass
        
        return None
    
    def _to_integer(self, value: Any) -> Optional[int]:
        """Convert value to integer."""
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            return int(value)
        
        if isinstance(value, str):
            numbers = re.findall(r'\d+', value)
            if numbers:
                try:
                    return int(numbers[0])
                except ValueError:
                    pass
        
        return None
    
    def _to_boolean(self, value: Any) -> Optional[bool]:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['true', 'yes', '1', 'on', 'enabled']:
                return True
            elif value_lower in ['false', 'no', '0', 'off', 'disabled']:
                return False
        
        return None
    
    def _to_array(self, value: Any) -> List[Any]:
        """Convert value to array."""
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            # Split by common delimiters
            if ',' in value:
                return [item.strip() for item in value.split(',')]
            elif ';' in value:
                return [item.strip() for item in value.split(';')]
            elif '|' in value:
                return [item.strip() for item in value.split('|')]
            else:
                return [value]
        
        return [value]
    
    def _to_url(self, value: Any) -> Optional[str]:
        """Convert and validate URL."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        # Add protocol if missing
        if value and not value.startswith(('http://', 'https://')):
            if value.startswith('www.'):
                value = 'https://' + value
            elif '.' in value:
                value = 'https://' + value
        
        # Validate URL format
        if self._validate_pattern(value, 'url'):
            return value
        
        return None
    
    def _to_email(self, value: Any) -> Optional[str]:
        """Convert and validate email."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip().lower()
        
        if self._validate_pattern(value, 'email'):
            return value
        
        return None
    
    def _to_phone(self, value: Any) -> Optional[str]:
        """Convert and validate phone number."""
        if not isinstance(value, str):
            value = str(value)
        
        # Extract phone numbers
        phones = self._extract_phones(value)
        if phones:
            return phones[0]
        
        return None
    
    def _to_date(self, value: Any) -> Optional[str]:
        """Convert to standardized date format."""
        if not isinstance(value, str):
            value = str(value)
        
        return self._format_date(value)
    
    def _validate_pattern(self, value: str, pattern_name: str) -> bool:
        """Validate value against a pattern."""
        if pattern_name not in self.validation_patterns:
            return True
        
        pattern = self.validation_patterns[pattern_name]
        return bool(re.match(pattern, value, re.IGNORECASE))
    
    def get_available_processors(self) -> List[str]:
        """Get list of available processing step names."""
        return list(self.processors.keys())
    
    def get_available_converters(self) -> List[str]:
        """Get list of available type converter names."""
        return list(self.converters.keys())
    
    def get_validation_patterns(self) -> Dict[str, str]:
        """Get dictionary of validation patterns."""
        return self.validation_patterns.copy()