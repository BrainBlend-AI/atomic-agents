"""
Content extractor with CSS selector and XPath support.

Provides comprehensive content extraction capabilities using BeautifulSoup
for HTML parsing and supports various extraction patterns.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag, NavigableString
from lxml import etree, html
from atomic_scraper_tool.models.extraction_models import (
    ExtractionRule, 
    ExtractedContent, 
    ContentQualityMetrics
)
from atomic_scraper_tool.models.base_models import ScrapedItem


logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Content extractor that uses BeautifulSoup and lxml for HTML parsing.
    
    Supports CSS selectors, XPath expressions, and complex extraction patterns
    with built-in quality scoring and data validation.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the content extractor.
        
        Args:
            base_url: Base URL for resolving relative URLs
        """
        self.base_url = base_url
        self.soup = None
        self.lxml_tree = None
        self._extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'quality_scores': []
        }
    
    def load_html(self, html_content: str, base_url: Optional[str] = None) -> None:
        """
        Load HTML content for extraction.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative URLs
        """
        if base_url:
            self.base_url = base_url
        
        # Parse with BeautifulSoup for CSS selectors
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        # Parse with lxml for XPath support
        try:
            from lxml import html as lxml_html
            self.lxml_tree = lxml_html.fromstring(html_content)
        except Exception as e:
            logger.warning(f"Failed to parse HTML with lxml: {e}")
            self.lxml_tree = None
    
    def extract_content(
        self, 
        extraction_rules: Dict[str, ExtractionRule],
        source_url: str
    ) -> ExtractedContent:
        """
        Extract content using the provided extraction rules.
        
        Args:
            extraction_rules: Dictionary of field names to extraction rules
            source_url: URL where content was extracted from
            
        Returns:
            ExtractedContent object with extracted data and quality metrics
        """
        if not self.soup:
            raise ValueError("No HTML content loaded. Call load_html() first.")
        
        extracted_data = {}
        extraction_issues = []
        extraction_metadata = {}
        
        # Extract each field according to its rule
        for field_name, rule in extraction_rules.items():
            try:
                value = self._extract_field(rule)
                if value is not None:
                    extracted_data[field_name] = value
                    extraction_metadata[f"{field_name}_selector"] = rule.selector
                else:
                    extraction_issues.append(f"No content found for field '{field_name}' with selector '{rule.selector}'")
            except Exception as e:
                extraction_issues.append(f"Error extracting field '{field_name}': {str(e)}")
                logger.error(f"Extraction error for field '{field_name}': {e}")
        
        # Calculate quality metrics
        quality_score = self._calculate_quality_score(extracted_data, extraction_rules)
        confidence_level = self._calculate_confidence_level(extracted_data, extraction_issues)
        
        # Update extraction stats
        self._update_extraction_stats(quality_score, len(extracted_data) > 0)
        
        return ExtractedContent(
            data=extracted_data,
            quality_score=quality_score,
            extraction_issues=extraction_issues,
            confidence_level=confidence_level,
            source_url=source_url,
            element_selector=None,  # Could be enhanced to track which elements were used
            extraction_metadata=extraction_metadata
        )
    
    def extract_multiple_items(
        self, 
        container_selector: str,
        extraction_rules: Dict[str, ExtractionRule],
        source_url: str,
        max_items: Optional[int] = None
    ) -> List[ExtractedContent]:
        """
        Extract multiple items from containers using the same extraction rules.
        
        Args:
            container_selector: CSS selector for item containers
            extraction_rules: Dictionary of field names to extraction rules
            source_url: URL where content was extracted from
            max_items: Maximum number of items to extract
            
        Returns:
            List of ExtractedContent objects
        """
        if not self.soup:
            raise ValueError("No HTML content loaded. Call load_html() first.")
        
        containers = self.soup.select(container_selector)
        if not containers:
            logger.warning(f"No containers found with selector: {container_selector}")
            return []
        
        if max_items:
            containers = containers[:max_items]
        
        extracted_items = []
        
        for i, container in enumerate(containers):
            try:
                # Create a temporary extractor for this container
                container_html = str(container)
                temp_extractor = ContentExtractor(self.base_url)
                temp_extractor.load_html(container_html, self.base_url)
                
                # Extract content from this container
                extracted_content = temp_extractor.extract_content(extraction_rules, source_url)
                extracted_content.element_selector = f"{container_selector}:nth-of-type({i+1})"
                
                extracted_items.append(extracted_content)
                
            except Exception as e:
                logger.error(f"Error extracting item {i+1}: {e}")
                continue
        
        return extracted_items
    
    def _extract_field(self, rule: ExtractionRule) -> Optional[Any]:
        """
        Extract a single field using the extraction rule.
        
        Args:
            rule: ExtractionRule defining how to extract the field
            
        Returns:
            Extracted value or None if not found
        """
        # Try primary selector first
        value = self._extract_with_selector(rule.selector, rule.extraction_type, rule.attribute_name)
        
        # Try fallback selectors if primary fails
        if value is None and rule.fallback_selectors:
            for fallback_selector in rule.fallback_selectors:
                value = self._extract_with_selector(fallback_selector, rule.extraction_type, rule.attribute_name)
                if value is not None:
                    break
        
        # Apply post-processing if value was found
        if value is not None and rule.post_processing:
            value = self._apply_post_processing(value, rule.post_processing)
        
        return value
    
    def _extract_with_selector(
        self, 
        selector: str, 
        extraction_type: str,
        attribute_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Extract content using a specific selector and extraction type.
        
        Args:
            selector: CSS selector or XPath expression
            extraction_type: Type of extraction ('text', 'attribute', 'html', etc.)
            attribute_name: Attribute name for attribute extraction
            
        Returns:
            Extracted value or None if not found
        """
        # Determine if this is an XPath expression
        if selector.startswith('//') or selector.startswith('./'):
            return self._extract_with_xpath(selector, extraction_type, attribute_name)
        else:
            return self._extract_with_css(selector, extraction_type, attribute_name)
    
    def _extract_with_css(
        self, 
        selector: str, 
        extraction_type: str,
        attribute_name: Optional[str] = None
    ) -> Optional[Any]:
        """Extract content using CSS selector."""
        try:
            elements = self.soup.select(selector)
            if not elements:
                return None
            
            # Use the first matching element
            element = elements[0]
            
            return self._extract_from_element(element, extraction_type, attribute_name)
            
        except Exception as e:
            logger.error(f"CSS selector extraction error: {e}")
            return None
    
    def _extract_with_xpath(
        self, 
        xpath: str, 
        extraction_type: str,
        attribute_name: Optional[str] = None
    ) -> Optional[Any]:
        """Extract content using XPath expression."""
        if not self.lxml_tree:
            logger.warning("XPath extraction requested but lxml tree not available")
            return None
        
        try:
            results = self.lxml_tree.xpath(xpath)
            if not results:
                return None
            
            # Handle different result types
            result = results[0]
            
            if isinstance(result, str):
                return result
            elif hasattr(result, 'text'):
                if extraction_type == 'text':
                    return result.text or ''
                elif extraction_type == 'attribute' and attribute_name:
                    return result.get(attribute_name)
                elif extraction_type == 'html':
                    return etree.tostring(result, encoding='unicode')
            
            return str(result)
            
        except Exception as e:
            logger.error(f"XPath extraction error: {e}")
            return None
    
    def _extract_from_element(
        self, 
        element: Tag, 
        extraction_type: str,
        attribute_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Extract content from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup Tag element
            extraction_type: Type of extraction
            attribute_name: Attribute name for attribute extraction
            
        Returns:
            Extracted value
        """
        if extraction_type == 'text' or extraction_type == 'inner_text':
            return element.get_text().strip()
        
        elif extraction_type == 'html' or extraction_type == 'outer_html':
            return str(element)
        
        elif extraction_type == 'attribute':
            if not attribute_name:
                raise ValueError("attribute_name required for attribute extraction")
            return element.get(attribute_name)
        
        elif extraction_type == 'href':
            href = element.get('href')
            if href and self.base_url:
                return urljoin(self.base_url, href)
            return href
        
        elif extraction_type == 'src':
            src = element.get('src')
            if src and self.base_url:
                return urljoin(self.base_url, src)
            return src
        
        else:
            # Default to text extraction
            return element.get_text().strip()
    
    def _apply_post_processing(self, value: Any, processing_steps: List[str]) -> Any:
        """
        Apply post-processing steps to extracted value.
        
        Args:
            value: Value to process
            processing_steps: List of processing step names
            
        Returns:
            Processed value
        """
        if not isinstance(value, str):
            value = str(value)
        
        for step in processing_steps:
            try:
                if step == 'clean':
                    value = self._clean_text(value)
                elif step == 'normalize':
                    value = self._normalize_text(value)
                elif step == 'validate':
                    value = self._validate_text(value)
                elif step == 'trim':
                    value = value.strip()
                elif step == 'lowercase':
                    value = value.lower()
                elif step == 'uppercase':
                    value = value.upper()
                elif step == 'strip_html':
                    value = self._strip_html(value)
                elif step == 'extract_numbers':
                    value = self._extract_numbers(value)
                elif step == 'extract_urls':
                    value = self._extract_urls(value)
                elif step == 'remove_duplicates':
                    if isinstance(value, list):
                        value = list(dict.fromkeys(value))  # Preserve order
                else:
                    logger.warning(f"Unknown post-processing step: {step}")
            except Exception as e:
                logger.error(f"Post-processing error in step '{step}': {e}")
        
        return value
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove non-printable characters
        text = re.sub(r'[^\x20-\x7E]', '', text)
        return text.strip()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text formatting."""
        # Convert to lowercase and remove extra spaces
        text = re.sub(r'\s+', ' ', text.lower())
        # Remove leading/trailing punctuation
        text = re.sub(r'^[^\w]+|[^\w]+$', '', text)
        return text.strip()
    
    def _validate_text(self, text: str) -> str:
        """Validate and clean text content."""
        # Remove obviously invalid content
        if len(text) < 2:
            return ""
        
        # Remove text that's mostly punctuation
        if len(re.sub(r'[^\w\s]', '', text)) < len(text) * 0.3:
            return ""
        
        return text
    
    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from text."""
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    
    def _extract_numbers(self, text: str) -> str:
        """Extract numbers from text."""
        numbers = re.findall(r'\d+\.?\d*', text)
        return ' '.join(numbers)
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls
    
    def _calculate_quality_score(
        self, 
        extracted_data: Dict[str, Any], 
        extraction_rules: Dict[str, ExtractionRule]
    ) -> float:
        """
        Calculate quality score for extracted content.
        
        Args:
            extracted_data: Dictionary of extracted field values
            extraction_rules: Dictionary of extraction rules
            
        Returns:
            Quality score between 0.0 and 100.0
        """
        if not extraction_rules:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for field_name, rule in extraction_rules.items():
            field_weight = rule.quality_weight if hasattr(rule, 'quality_weight') else 1.0
            total_weight += field_weight
            
            if field_name in extracted_data and extracted_data[field_name]:
                field_score = self._calculate_field_quality(extracted_data[field_name], rule)
                weighted_score += field_score * field_weight
        
        if total_weight == 0:
            return 0.0
        
        return min(100.0, (weighted_score / total_weight) * 100.0)
    
    def _calculate_field_quality(self, value: Any, rule: ExtractionRule) -> float:
        """
        Calculate quality score for a single field.
        
        Args:
            value: Extracted field value
            rule: Extraction rule for the field
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return 0.0
        
        score = 1.0
        
        # Check quality indicators if present
        if hasattr(rule, 'quality_indicators') and rule.quality_indicators:
            for indicator in rule.quality_indicators:
                if indicator == 'has_text' and isinstance(value, str) and len(value.strip()) > 0:
                    score *= 1.1
                elif indicator == 'min_length' and isinstance(value, str) and len(value) >= 10:
                    score *= 1.1
                elif indicator == 'max_length' and isinstance(value, str) and len(value) <= 500:
                    score *= 1.1
                elif indicator == 'has_links' and isinstance(value, str) and 'http' in value:
                    score *= 1.1
        
        # Penalize very short or very long content
        if isinstance(value, str):
            length = len(value.strip())
            if length < 3:
                score *= 0.5
            elif length > 1000:
                score *= 0.8
        
        return min(1.0, score)
    
    def _calculate_confidence_level(
        self, 
        extracted_data: Dict[str, Any], 
        extraction_issues: List[str]
    ) -> float:
        """
        Calculate confidence level for the extraction.
        
        Args:
            extracted_data: Dictionary of extracted field values
            extraction_issues: List of extraction issues
            
        Returns:
            Confidence level between 0.0 and 1.0
        """
        if not extracted_data:
            return 0.0
        
        # Base confidence on successful extractions vs issues
        total_fields = len(extracted_data) + len(extraction_issues)
        if total_fields == 0:
            return 0.0
        
        success_rate = len(extracted_data) / total_fields
        
        # Adjust based on data quality
        non_empty_fields = sum(1 for value in extracted_data.values() 
                              if value is not None and str(value).strip())
        
        if len(extracted_data) > 0:
            completeness = non_empty_fields / len(extracted_data)
        else:
            completeness = 0.0
        
        # Combine success rate and completeness
        confidence = (success_rate * 0.6) + (completeness * 0.4)
        
        return min(1.0, confidence)
    
    def _update_extraction_stats(self, quality_score: float, success: bool) -> None:
        """Update internal extraction statistics."""
        self._extraction_stats['total_extractions'] += 1
        if success:
            self._extraction_stats['successful_extractions'] += 1
        else:
            self._extraction_stats['failed_extractions'] += 1
        
        self._extraction_stats['quality_scores'].append(quality_score)
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        stats = self._extraction_stats.copy()
        
        if stats['quality_scores']:
            stats['average_quality'] = sum(stats['quality_scores']) / len(stats['quality_scores'])
            stats['min_quality'] = min(stats['quality_scores'])
            stats['max_quality'] = max(stats['quality_scores'])
        else:
            stats['average_quality'] = 0.0
            stats['min_quality'] = 0.0
            stats['max_quality'] = 0.0
        
        if stats['total_extractions'] > 0:
            stats['success_rate'] = stats['successful_extractions'] / stats['total_extractions']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset extraction statistics."""
        self._extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'quality_scores': []
        }
    
    def extract_with_css_selector(
        self, 
        selector: str, 
        extraction_type: str = 'text',
        attribute_name: Optional[str] = None,
        multiple: bool = False
    ) -> Union[Any, List[Any]]:
        """
        Simple extraction method using CSS selector.
        
        Args:
            selector: CSS selector
            extraction_type: Type of extraction ('text', 'attribute', 'html')
            attribute_name: Attribute name for attribute extraction
            multiple: Whether to return multiple results
            
        Returns:
            Extracted value(s) or None if not found
        """
        if not self.soup:
            raise ValueError("No HTML content loaded. Call load_html() first.")
        
        elements = self.soup.select(selector)
        if not elements:
            return [] if multiple else None
        
        if multiple:
            results = []
            for element in elements:
                value = self._extract_from_element(element, extraction_type, attribute_name)
                if value is not None:
                    results.append(value)
            return results
        else:
            return self._extract_from_element(elements[0], extraction_type, attribute_name)
    
    def extract_with_xpath(
        self, 
        xpath: str, 
        extraction_type: str = 'text',
        attribute_name: Optional[str] = None,
        multiple: bool = False
    ) -> Union[Any, List[Any]]:
        """
        Simple extraction method using XPath.
        
        Args:
            xpath: XPath expression
            extraction_type: Type of extraction ('text', 'attribute', 'html')
            attribute_name: Attribute name for attribute extraction
            multiple: Whether to return multiple results
            
        Returns:
            Extracted value(s) or None if not found
        """
        if not self.lxml_tree:
            raise ValueError("XPath not supported. lxml tree not available.")
        
        try:
            results = self.lxml_tree.xpath(xpath)
            if not results:
                return [] if multiple else None
            
            if multiple:
                extracted_values = []
                for result in results:
                    if isinstance(result, str):
                        extracted_values.append(result)
                    elif hasattr(result, 'text'):
                        if extraction_type == 'text':
                            extracted_values.append(result.text or '')
                        elif extraction_type == 'attribute' and attribute_name:
                            extracted_values.append(result.get(attribute_name))
                        elif extraction_type == 'html':
                            extracted_values.append(etree.tostring(result, encoding='unicode'))
                    else:
                        extracted_values.append(str(result))
                return extracted_values
            else:
                result = results[0]
                if isinstance(result, str):
                    return result
                elif hasattr(result, 'text'):
                    if extraction_type == 'text':
                        return result.text or ''
                    elif extraction_type == 'attribute' and attribute_name:
                        return result.get(attribute_name)
                    elif extraction_type == 'html':
                        return etree.tostring(result, encoding='unicode')
                return str(result)
                
        except Exception as e:
            logger.error(f"XPath extraction error: {e}")
            return [] if multiple else None