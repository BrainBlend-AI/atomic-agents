"""
Atomic Scraper Tool - Next-Generation Intelligent Web Scraping

AI-powered scraping tool that executes dynamically generated scraping strategies
with natural language interface and advanced quality control.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from atomic_agents.lib.base.base_tool import BaseTool
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field, field_validator

from atomic_scraper_tool.config.scraper_config import AtomicScraperConfig
from atomic_scraper_tool.models.base_models import ScrapingStrategy, ScrapingResult, ScrapedItem
from atomic_scraper_tool.models.schema_models import SchemaRecipe
from atomic_scraper_tool.models.extraction_models import ExtractionRule
from atomic_scraper_tool.extraction.content_extractor import ContentExtractor
from atomic_scraper_tool.extraction.data_processor import DataProcessor
from atomic_scraper_tool.extraction.quality_analyzer import QualityAnalyzer, QualityThresholds
from atomic_scraper_tool.core.error_handler import ErrorHandler, ErrorContext, RetryConfig
from atomic_scraper_tool.core.exceptions import ScrapingError, NetworkError, ParsingError, QualityError


logger = logging.getLogger(__name__)


class AtomicScraperInputSchema(BaseIOSchema):
    """Input schema for the atomic scraper tool."""
    
    target_url: str = Field(..., description="Website URL to scrape")
    strategy: Dict[str, Any] = Field(..., description="Scraping strategy configuration")
    schema_recipe: Dict[str, Any] = Field(..., description="Schema recipe for data validation")
    max_results: int = Field(10, ge=1, le=1000, description="Maximum results to return")
    
    @field_validator('target_url')
    @classmethod
    def validate_target_url(cls, v):
        """Validate target URL format."""
        if not v.strip():
            raise ValueError("target_url cannot be empty")
        
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: '{v}'")
        
        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"URL scheme must be http or https, got '{parsed.scheme}'")
        
        return v


class AtomicScraperOutputSchema(BaseIOSchema):
    """Output schema for the atomic scraper tool."""
    
    results: Dict[str, Any] = Field(..., description="Scraping results with extracted data")
    summary: str = Field(..., description="Human-readable summary of results")
    quality_metrics: Dict[str, float] = Field(..., description="Quality metrics for the scraping operation")


class AtomicScraperTool(BaseTool):
    """
    Next-Generation Intelligent Web Scraping Tool built on the atomic agents framework.
    
    This AI-powered tool executes dynamically generated scraping strategies with
    natural language interface and advanced quality control, returning structured
    data according to dynamic schema recipes.
    """
    
    name = "Atomic Scraper Tool"
    description = "Next-generation intelligent web scraping tool with AI-powered strategy generation"
    input_schema = AtomicScraperInputSchema
    output_schema = AtomicScraperOutputSchema
    
    def __init__(self, config: Optional[AtomicScraperConfig] = None):
        """
        Initialize the atomic scraper tool.
        
        Args:
            config: Tool configuration
        """
        # Initialize with default config if none provided
        if config is None:
            config = AtomicScraperConfig(base_url="https://example.com")
        
        # Store the scraper config separately from the base tool config
        self.config = config
        
        super().__init__()
        
        # Initialize components
        self.content_extractor = ContentExtractor()
        self.data_processor = DataProcessor()
        
        # Initialize quality analyzer with thresholds from config
        quality_thresholds = QualityThresholds(
            minimum_completeness=config.min_quality_score * 0.8,
            minimum_accuracy=config.min_quality_score * 0.9,
            minimum_consistency=config.min_quality_score * 0.6,
            minimum_overall=config.min_quality_score
        )
        self.quality_analyzer = QualityAnalyzer(quality_thresholds)
        
        # Initialize error handler with retry configuration
        retry_config = RetryConfig(
            max_attempts=config.max_retries,
            base_delay=config.retry_delay,
            max_delay=30.0
        )
        self.error_handler = ErrorHandler(retry_config)
        
        # Initialize HTTP session with configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent
        })
        
        # Set request timeout
        self.request_timeout = config.timeout
        
        logger.info(f"AtomicScraperTool initialized with config: {config}")
    
    def run(self, input_data: AtomicScraperInputSchema) -> AtomicScraperOutputSchema:
        """
        Execute scraping operation based on strategy and schema.
        
        Args:
            input_data: Scraping parameters and configuration
            
        Returns:
            Scraping results with extracted data
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            self._validate_inputs(input_data)
            
            # Create strategy and schema objects
            strategy = self._create_scraping_strategy(input_data.strategy)
            schema_recipe = self._create_schema_recipe(input_data.schema_recipe)
            
            # Create extraction rules from schema recipe
            extraction_rules = self._create_extraction_rules(schema_recipe)
            
            logger.info(f"Starting scraping operation for {input_data.target_url}")
            logger.info(f"Strategy: {strategy.scrape_type}, Max results: {input_data.max_results}")
            
            # Execute scraping based on strategy type
            if strategy.scrape_type == 'list':
                scraping_result = self._scrape_list_content(
                    input_data.target_url, strategy, extraction_rules, input_data.max_results
                )
            elif strategy.scrape_type == 'detail':
                scraping_result = self._scrape_detail_content(
                    input_data.target_url, strategy, extraction_rules
                )
            elif strategy.scrape_type == 'search':
                scraping_result = self._scrape_search_results(
                    input_data.target_url, strategy, extraction_rules, input_data.max_results
                )
            elif strategy.scrape_type == 'sitemap':
                scraping_result = self._scrape_from_sitemap(
                    input_data.target_url, strategy, extraction_rules, input_data.max_results
                )
            else:
                raise ValueError(f"Unsupported scrape_type: {strategy.scrape_type}")
            
            # Calculate execution time
            execution_time = time.time() - start_time
            scraping_result.execution_time = execution_time
            
            # Generate summary and quality metrics
            summary = self._generate_summary(scraping_result)
            quality_metrics = self._extract_quality_metrics(scraping_result)
            
            logger.info(f"Scraping completed in {execution_time:.2f} seconds")
            logger.info(f"Results: {scraping_result.total_items_scraped} items scraped")
            
            return AtomicScraperOutputSchema(
                results={
                    'items': [item.model_dump() for item in scraping_result.items],
                    'total_found': scraping_result.total_items_found,
                    'total_scraped': scraping_result.total_items_scraped,
                    'strategy_used': scraping_result.strategy_used.model_dump(),
                    'errors': scraping_result.errors
                },
                summary=summary,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Scraping failed: {str(e)}"
            logger.error(error_msg)
            
            # Return error result
            return AtomicScraperOutputSchema(
                results={
                    'items': [],
                    'total_found': 0,
                    'total_scraped': 0,
                    'strategy_used': input_data.strategy,
                    'errors': [error_msg]
                },
                summary=f"Scraping failed after {execution_time:.2f} seconds: {str(e)}",
                quality_metrics={
                    'average_quality_score': 0.0,
                    'success_rate': 0.0,
                    'total_items_found': 0.0,
                    'total_items_scraped': 0.0,
                    'execution_time': execution_time
                }
            )
    
    def _validate_inputs(self, input_data: AtomicScraperInputSchema) -> None:
        """
        Validate input data and configuration.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            ValueError: If input data is invalid
        """
        # Validate strategy
        if not input_data.strategy:
            raise ValueError("Strategy cannot be empty")
        
        required_strategy_fields = ['scrape_type', 'target_selectors']
        for field in required_strategy_fields:
            if field not in input_data.strategy:
                raise ValueError(f"Strategy missing required field: {field}")
        
        # Validate schema recipe
        if not input_data.schema_recipe:
            raise ValueError("Schema recipe cannot be empty")
        
        if 'fields' not in input_data.schema_recipe:
            raise ValueError("Schema recipe must contain 'fields' definition")
        
        # Validate URL accessibility
        try:
            parsed_url = urlparse(input_data.target_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL format: {input_data.target_url}")
        except Exception as e:
            raise ValueError(f"URL validation failed: {e}")
    
    def _create_scraping_strategy(self, strategy_dict: Dict[str, Any]) -> ScrapingStrategy:
        """
        Create ScrapingStrategy object from dictionary.
        
        Args:
            strategy_dict: Strategy configuration dictionary
            
        Returns:
            ScrapingStrategy object
        """
        try:
            return ScrapingStrategy(**strategy_dict)
        except Exception as e:
            raise ValueError(f"Invalid strategy configuration: {e}")
    
    def _create_schema_recipe(self, recipe_dict: Dict[str, Any]) -> SchemaRecipe:
        """
        Create SchemaRecipe object from dictionary.
        
        Args:
            recipe_dict: Schema recipe dictionary
            
        Returns:
            SchemaRecipe object
        """
        try:
            return SchemaRecipe(**recipe_dict)
        except Exception as e:
            raise ValueError(f"Invalid schema recipe: {e}")
    
    def _create_extraction_rules(self, schema_recipe: SchemaRecipe) -> Dict[str, ExtractionRule]:
        """
        Create extraction rules from schema recipe.
        
        Args:
            schema_recipe: Schema recipe containing field definitions
            
        Returns:
            Dictionary of field names to extraction rules
        """
        extraction_rules = {}
        
        # Map field types to extraction types
        field_type_mapping = {
            'string': 'text',
            'number': 'text',
            'float': 'text',
            'integer': 'text',
            'boolean': 'text',
            'array': 'text',
            'url': 'href',
            'email': 'text',
            'phone': 'text',
            'date': 'text'
        }
        
        for field_name, field_def in schema_recipe.fields.items():
            # Map field type to extraction type
            extraction_type = field_type_mapping.get(field_def.field_type, 'text')
            
            extraction_rule = ExtractionRule(
                field_name=field_name,
                selector=field_def.extraction_selector,
                extraction_type=extraction_type,
                post_processing=getattr(field_def, 'post_processing', [])
            )
            extraction_rules[field_name] = extraction_rule
        
        return extraction_rules
    
    def _fetch_page_content(self, url: str) -> str:
        """
        Fetch HTML content from URL with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            NetworkError: If request fails
        """
        context = ErrorContext(
            operation="fetch_page",
            url=url,
            max_attempts=self.config.max_retries
        )
        
        def fetch_operation():
            try:
                response = self.session.get(
                    url, 
                    timeout=self.request_timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                raise NetworkError(f"Failed to fetch {url}: {e}", url=url)
        
        return self.error_handler.with_retry(fetch_operation, context)
    
    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting delay between requests."""
        if hasattr(self.config, 'request_delay') and self.config.request_delay > 0:
            time.sleep(self.config.request_delay)
    
    def _generate_summary(self, scraping_result: ScrapingResult) -> str:
        """
        Generate human-readable summary of scraping results.
        
        Args:
            scraping_result: Scraping result to summarize
            
        Returns:
            Summary string
        """
        total_items = scraping_result.total_items_scraped
        avg_quality = scraping_result.average_quality_score
        execution_time = scraping_result.execution_time
        
        summary = f"Successfully scraped {total_items} items "
        summary += f"with average quality score of {avg_quality:.1f}% "
        summary += f"in {execution_time:.2f} seconds."
        
        if scraping_result.errors:
            summary += f" Encountered {len(scraping_result.errors)} errors during scraping."
        
        return summary
    
    def _extract_quality_metrics(self, scraping_result: ScrapingResult) -> Dict[str, float]:
        """
        Extract quality metrics from scraping result.
        
        Args:
            scraping_result: Scraping result containing quality information
            
        Returns:
            Dictionary of quality metrics
        """
        return {
            'average_quality_score': scraping_result.average_quality_score,
            'success_rate': scraping_result.success_rate,
            'total_items_found': float(scraping_result.total_items_found),
            'total_items_scraped': float(scraping_result.total_items_scraped),
            'execution_time': scraping_result.execution_time
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get information about the tool and its configuration.
        
        Returns:
            Dictionary containing tool information
        """
        return {
            'name': self.name,
            'version': '1.0.0',
            'description': self.description,
            'config': {
                'base_url': self.config.base_url,
                'request_delay': self.config.request_delay,
                'timeout': self.config.timeout,
                'max_pages': self.config.max_pages,
                'max_results': self.config.max_results,
                'min_quality_score': self.config.min_quality_score,
                'respect_robots_txt': self.config.respect_robots_txt,
                'enable_rate_limiting': self.config.enable_rate_limiting
            },
            'supported_strategies': ['list', 'detail', 'search', 'sitemap'],
            'supported_extraction_types': ['text', 'attribute', 'html', 'href', 'src']
        }
    
    def update_config(self, **config_updates) -> None:
        """
        Update tool configuration.
        
        Args:
            **config_updates: Configuration parameters to update
        """
        # Update config attributes
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated config {key} to {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")
        
        # Update session headers if user_agent changed
        if 'user_agent' in config_updates:
            self.session.headers.update({
                'User-Agent': config_updates['user_agent']
            })
        
        # Update timeout if changed
        if 'timeout' in config_updates:
            self.request_timeout = config_updates['timeout']
        
        # Update quality analyzer thresholds if quality score changed
        if 'min_quality_score' in config_updates:
            new_threshold = config_updates['min_quality_score']
            quality_thresholds = QualityThresholds(
                minimum_completeness=new_threshold * 0.8,
                minimum_accuracy=new_threshold * 0.9,
                minimum_consistency=new_threshold * 0.6,
                minimum_overall=new_threshold
            )
            self.quality_analyzer.update_thresholds(quality_thresholds)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error handling statistics.
        
        Returns:
            Dictionary containing error statistics
        """
        return {
            'error_handler_stats': self.error_handler.get_error_stats(),
            'extractor_stats': self.content_extractor.get_extraction_stats()
        }
    
    def reset_stats(self) -> None:
        """Reset all internal statistics."""
        self.error_handler.reset_stats()
        self.content_extractor.reset_stats()
    
    def _scrape_list_content(
        self, 
        url: str, 
        strategy: ScrapingStrategy, 
        extraction_rules: Dict[str, ExtractionRule],
        max_results: int
    ) -> ScrapingResult:
        """
        Scrape list-type content with pagination support.
        
        Args:
            url: Starting URL to scrape
            strategy: Scraping strategy configuration
            extraction_rules: Field extraction rules
            max_results: Maximum items to return
            
        Returns:
            ScrapingResult with extracted items
        """
        all_items = []
        errors = []
        pages_scraped = 0
        current_url = url
        
        while current_url and pages_scraped < strategy.max_pages and len(all_items) < max_results:
            try:
                # Apply rate limiting
                if pages_scraped > 0:
                    self._apply_rate_limiting()
                
                # Fetch page content
                html_content = self._fetch_page_content(current_url)
                
                # Extract items from this page
                page_items = self._extract_items_from_page(
                    html_content, current_url, strategy, extraction_rules
                )
                
                # Filter items that meet quality threshold
                quality_items = []
                for item in page_items:
                    if item.quality_score >= self.config.min_quality_score:
                        quality_items.append(item)
                    else:
                        errors.append(f"Item from {current_url} below quality threshold: {item.quality_score:.1f}%")
                
                all_items.extend(quality_items)
                pages_scraped += 1
                
                logger.info(f"Page {pages_scraped}: Found {len(page_items)} items, {len(quality_items)} passed quality check")
                
                # Check if we have enough results
                if len(all_items) >= max_results:
                    all_items = all_items[:max_results]
                    break
                
                # Find next page URL if pagination is enabled
                if strategy.pagination_strategy:
                    current_url = self._find_next_page_url(html_content, current_url, strategy.pagination_strategy)
                else:
                    break
                    
            except Exception as e:
                error_msg = f"Error scraping page {current_url}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                break
        
        # Calculate metrics
        total_found = len(all_items) + len([e for e in errors if "below quality threshold" in e])
        avg_quality = sum(item.quality_score for item in all_items) / len(all_items) if all_items else 0.0
        
        return ScrapingResult(
            items=all_items,
            total_items_found=total_found,
            total_items_scraped=len(all_items),
            average_quality_score=avg_quality,
            scraping_summary=f"Scraped {len(all_items)} items from {pages_scraped} pages",
            strategy_used=strategy,
            errors=errors,
            execution_time=0.0  # Will be set by caller
        )
    
    def _scrape_detail_content(
        self, 
        url: str, 
        strategy: ScrapingStrategy, 
        extraction_rules: Dict[str, ExtractionRule]
    ) -> ScrapingResult:
        """
        Scrape detail page content.
        
        Args:
            url: URL to scrape
            strategy: Scraping strategy configuration
            extraction_rules: Field extraction rules
            
        Returns:
            ScrapingResult with extracted item
        """
        errors = []
        
        try:
            # Fetch page content
            html_content = self._fetch_page_content(url)
            
            # Extract single item from page
            items = self._extract_items_from_page(html_content, url, strategy, extraction_rules)
            
            if not items:
                errors.append(f"No content found on detail page: {url}")
                return ScrapingResult(
                    items=[],
                    total_items_found=0,
                    total_items_scraped=0,
                    average_quality_score=0.0,
                    scraping_summary="No content found on detail page",
                    strategy_used=strategy,
                    errors=errors,
                    execution_time=0.0
                )
            
            # Take the first (and typically only) item
            item = items[0]
            
            # Check quality threshold
            if item.quality_score < self.config.min_quality_score:
                errors.append(f"Detail page content below quality threshold: {item.quality_score:.1f}%")
                return ScrapingResult(
                    items=[],
                    total_items_found=1,
                    total_items_scraped=0,
                    average_quality_score=item.quality_score,
                    scraping_summary="Detail page content below quality threshold",
                    strategy_used=strategy,
                    errors=errors,
                    execution_time=0.0
                )
            
            return ScrapingResult(
                items=[item],
                total_items_found=1,
                total_items_scraped=1,
                average_quality_score=item.quality_score,
                scraping_summary=f"Successfully scraped detail page with quality score {item.quality_score:.1f}%",
                strategy_used=strategy,
                errors=errors,
                execution_time=0.0
            )
            
        except Exception as e:
            error_msg = f"Error scraping detail page {url}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return ScrapingResult(
                items=[],
                total_items_found=0,
                total_items_scraped=0,
                average_quality_score=0.0,
                scraping_summary="Failed to scrape detail page",
                strategy_used=strategy,
                errors=errors,
                execution_time=0.0
            )
    
    def _scrape_search_results(
        self, 
        url: str, 
        strategy: ScrapingStrategy, 
        extraction_rules: Dict[str, ExtractionRule],
        max_results: int
    ) -> ScrapingResult:
        """
        Scrape search results with pagination support.
        
        Args:
            url: Search URL to scrape
            strategy: Scraping strategy configuration
            extraction_rules: Field extraction rules
            max_results: Maximum items to return
            
        Returns:
            ScrapingResult with extracted search results
        """
        # Search results are similar to list content but may have different pagination
        return self._scrape_list_content(url, strategy, extraction_rules, max_results)
    
    def _scrape_from_sitemap(
        self, 
        url: str, 
        strategy: ScrapingStrategy, 
        extraction_rules: Dict[str, ExtractionRule],
        max_results: int
    ) -> ScrapingResult:
        """
        Scrape content from sitemap URLs.
        
        Args:
            url: Sitemap URL
            strategy: Scraping strategy configuration
            extraction_rules: Field extraction rules
            max_results: Maximum items to return
            
        Returns:
            ScrapingResult with extracted items from sitemap URLs
        """
        all_items = []
        errors = []
        
        try:
            # Fetch sitemap content
            sitemap_content = self._fetch_page_content(url)
            
            # Extract URLs from sitemap
            sitemap_urls = self._extract_sitemap_urls(sitemap_content)
            
            if not sitemap_urls:
                errors.append(f"No URLs found in sitemap: {url}")
                return ScrapingResult(
                    items=[],
                    total_items_found=0,
                    total_items_scraped=0,
                    average_quality_score=0.0,
                    scraping_summary="No URLs found in sitemap",
                    strategy_used=strategy,
                    errors=errors,
                    execution_time=0.0
                )
            
            # Limit URLs to process
            urls_to_process = sitemap_urls[:min(len(sitemap_urls), max_results, strategy.max_pages)]
            
            # Scrape each URL from sitemap
            for i, sitemap_url in enumerate(urls_to_process):
                try:
                    # Apply rate limiting
                    if i > 0:
                        self._apply_rate_limiting()
                    
                    # Fetch and extract from this URL
                    html_content = self._fetch_page_content(sitemap_url)
                    page_items = self._extract_items_from_page(
                        html_content, sitemap_url, strategy, extraction_rules
                    )
                    
                    # Filter by quality
                    for item in page_items:
                        if item.quality_score >= self.config.min_quality_score:
                            all_items.append(item)
                            if len(all_items) >= max_results:
                                break
                        else:
                            errors.append(f"Item from {sitemap_url} below quality threshold")
                    
                    if len(all_items) >= max_results:
                        break
                        
                except Exception as e:
                    error_msg = f"Error scraping sitemap URL {sitemap_url}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            # Calculate metrics
            avg_quality = sum(item.quality_score for item in all_items) / len(all_items) if all_items else 0.0
            
            return ScrapingResult(
                items=all_items,
                total_items_found=len(sitemap_urls),
                total_items_scraped=len(all_items),
                average_quality_score=avg_quality,
                scraping_summary=f"Scraped {len(all_items)} items from {len(urls_to_process)} sitemap URLs",
                strategy_used=strategy,
                errors=errors,
                execution_time=0.0
            )
            
        except Exception as e:
            error_msg = f"Error processing sitemap {url}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return ScrapingResult(
                items=[],
                total_items_found=0,
                total_items_scraped=0,
                average_quality_score=0.0,
                scraping_summary="Failed to process sitemap",
                strategy_used=strategy,
                errors=errors,
                execution_time=0.0
            )
    
    def _extract_items_from_page(
        self, 
        html_content: str, 
        source_url: str, 
        strategy: ScrapingStrategy,
        extraction_rules: Dict[str, ExtractionRule]
    ) -> List[ScrapedItem]:
        """
        Extract items from a single page using the strategy and extraction rules.
        
        Args:
            html_content: HTML content of the page
            source_url: URL where content was fetched from
            strategy: Scraping strategy configuration
            extraction_rules: Field extraction rules
            
        Returns:
            List of ScrapedItem objects
        """
        items = []
        
        # Initialize content extractor with HTML
        self.content_extractor.load_html(html_content, source_url)
        
        # Check if we need to extract multiple items or single item
        if len(strategy.target_selectors) == 1 and strategy.scrape_type in ['list', 'search']:
            # Multiple items from containers
            container_selector = strategy.target_selectors[0]
            extracted_contents = self.content_extractor.extract_multiple_items(
                container_selector, extraction_rules, source_url
            )
            
            # Convert ExtractedContent to ScrapedItem
            for extracted_content in extracted_contents:
                scraped_item = ScrapedItem(
                    source_url=source_url,
                    data=extracted_content.data,
                    quality_score=extracted_content.quality_score,
                    extraction_issues=extracted_content.extraction_issues,
                    schema_version="1.0"
                )
                items.append(scraped_item)
        
        else:
            # Single item extraction (detail page or single item)
            extracted_content = self.content_extractor.extract_content(extraction_rules, source_url)
            
            if extracted_content.data:
                scraped_item = ScrapedItem(
                    source_url=source_url,
                    data=extracted_content.data,
                    quality_score=extracted_content.quality_score,
                    extraction_issues=extracted_content.extraction_issues,
                    schema_version="1.0"
                )
                items.append(scraped_item)
        
        return items
    
    def _find_next_page_url(
        self, 
        html_content: str, 
        current_url: str, 
        pagination_strategy: str
    ) -> Optional[str]:
        """
        Find the next page URL based on pagination strategy.
        
        Args:
            html_content: HTML content of current page
            current_url: Current page URL
            pagination_strategy: Type of pagination to look for
            
        Returns:
            Next page URL or None if no next page found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            if pagination_strategy == 'next_link':
                # Look for common "next" link patterns
                next_selectors = [
                    'a[rel="next"]',
                    'a.next',
                    'a.pagination-next',
                    'a:contains("Next")',
                    'a:contains(">")',
                    '.pager-next a'
                ]
                
                for selector in next_selectors:
                    try:
                        if ':contains(' in selector:
                            # Handle text-based selectors differently
                            if 'Next' in selector:
                                next_links = soup.find_all('a', string=lambda text: text and 'Next' in text)
                            elif '>' in selector:
                                next_links = soup.find_all('a', string=lambda text: text and '>' in text)
                            else:
                                continue
                            
                            if next_links:
                                next_link = next_links[0]
                                href = next_link.get('href')
                                if href:
                                    return urljoin(current_url, href)
                        else:
                            next_link = soup.select_one(selector)
                            if next_link:
                                href = next_link.get('href')
                                if href:
                                    return urljoin(current_url, href)
                    except Exception:
                        continue
            
            elif pagination_strategy == 'page_numbers':
                # Look for numbered pagination links
                page_links = soup.select('.pagination a, .pager a, .page-numbers a')
                current_page_num = self._extract_current_page_number(current_url)
                
                for link in page_links:
                    href = link.get('href')
                    if href:
                        link_page_num = self._extract_page_number_from_url(urljoin(current_url, href))
                        if link_page_num == current_page_num + 1:
                            return urljoin(current_url, href)
            
            elif pagination_strategy == 'load_more':
                # Look for "Load More" buttons (usually AJAX, but check for href)
                load_more_selectors = [
                    'a.load-more',
                    'button.load-more[data-url]',
                    'a:contains("Load More")',
                    'a:contains("Show More")'
                ]
                
                for selector in load_more_selectors:
                    try:
                        if ':contains(' in selector:
                            if 'Load More' in selector:
                                elements = soup.find_all('a', string=lambda text: text and 'Load More' in text)
                            elif 'Show More' in selector:
                                elements = soup.find_all('a', string=lambda text: text and 'Show More' in text)
                            else:
                                continue
                            
                            if elements:
                                element = elements[0]
                                href = element.get('href') or element.get('data-url')
                                if href:
                                    return urljoin(current_url, href)
                        else:
                            element = soup.select_one(selector)
                            if element:
                                href = element.get('href') or element.get('data-url')
                                if href:
                                    return urljoin(current_url, href)
                    except Exception:
                        continue
            
            # If no specific strategy worked, try generic next page detection
            return self._find_generic_next_page(soup, current_url)
            
        except Exception as e:
            logger.error(f"Error finding next page URL: {e}")
            return None
    
    def _find_generic_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Generic next page detection as fallback.
        
        Args:
            soup: BeautifulSoup object of current page
            current_url: Current page URL
            
        Returns:
            Next page URL or None
        """
        # Try common pagination patterns
        generic_selectors = [
            'a[aria-label="Next"]',
            'a[title="Next"]',
            'a.next-page',
            'a.btn-next',
            '.pagination .next a',
            '.paging .next a'
        ]
        
        for selector in generic_selectors:
            try:
                next_link = soup.select_one(selector)
                if next_link:
                    href = next_link.get('href')
                    if href:
                        next_page_url = urljoin(current_url, href)
                        # Make sure we're not returning the same URL
                        if next_page_url != current_url:
                            return next_page_url
            except Exception:
                continue
        
        return None
    
    def _extract_current_page_number(self, url: str) -> int:
        """Extract current page number from URL."""
        import re
        
        # Look for common page parameter patterns
        patterns = [
            r'[?&]page=(\d+)',
            r'[?&]p=(\d+)',
            r'[?&]pagenum=(\d+)',
            r'/page/(\d+)',
            r'/p(\d+)',
            r'-page-(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return int(match.group(1))
        
        return 1  # Default to page 1
    
    def _extract_page_number_from_url(self, url: str) -> int:
        """Extract page number from any URL."""
        return self._extract_current_page_number(url)
    
    def _extract_sitemap_urls(self, sitemap_content: str) -> List[str]:
        """
        Extract URLs from sitemap XML content.
        
        Args:
            sitemap_content: XML content of sitemap
            
        Returns:
            List of URLs found in sitemap
        """
        urls = []
        
        try:
            # Try parsing as XML sitemap first
            soup = BeautifulSoup(sitemap_content, 'xml')
            
            # Look for URL elements in XML sitemap
            url_elements = soup.find_all('url')
            for url_elem in url_elements:
                loc_elem = url_elem.find('loc')
                if loc_elem and loc_elem.text:
                    urls.append(loc_elem.text.strip())
            
            # If no XML URLs found, try HTML sitemap
            if not urls:
                html_soup = BeautifulSoup(sitemap_content, 'html.parser')
                links = html_soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if href.startswith('http') or href.startswith('/'):
                        urls.append(href)
        
        except Exception as e:
            logger.error(f"Error extracting sitemap URLs: {e}")
        
        return urls