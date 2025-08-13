"""
Test scenarios for comprehensive scraping testing.

This module provides predefined test scenarios that combine mock websites
with specific testing objectives to validate scraping functionality.
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from atomic_scraper_tool.testing.mock_website import MockWebsite, MockWebsiteGenerator, WebsiteType


class ScenarioType(str, Enum):
    """Types of test scenarios."""
    BASIC_SCRAPING = "basic_scraping"
    ERROR_HANDLING = "error_handling"
    PAGINATION = "pagination"
    DYNAMIC_CONTENT = "dynamic_content"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    DATA_QUALITY = "data_quality"


@dataclass
class ScrapingTestScenario:
    """
    A test scenario that combines a mock website with testing objectives.
    """
    name: str
    description: str
    scenario_type: ScenarioType
    mock_website: MockWebsite
    expected_results: Dict[str, Any]
    validation_rules: List[Callable[[Any], bool]]
    test_urls: List[str]
    metadata: Dict[str, Any]


class ScenarioGenerator:
    """
    Generator for comprehensive test scenarios.
    
    This class creates various test scenarios that cover different aspects
    of web scraping functionality.
    """
    
    def __init__(self):
        """Initialize the scenario generator."""
        self.scenarios = {}
        self._setup_scenario_templates()
    
    def _setup_scenario_templates(self):
        """Set up templates for different scenario types."""
        self.scenario_templates = {
            ScenarioType.BASIC_SCRAPING: self._create_basic_scraping_scenarios,
            ScenarioType.ERROR_HANDLING: self._create_error_handling_scenarios,
            ScenarioType.PAGINATION: self._create_pagination_scenarios,
            ScenarioType.DYNAMIC_CONTENT: self._create_dynamic_content_scenarios,
            ScenarioType.PERFORMANCE: self._create_performance_scenarios,
            ScenarioType.COMPLIANCE: self._create_compliance_scenarios,
            ScenarioType.DATA_QUALITY: self._create_data_quality_scenarios
        }
    
    def generate_scenario(self, scenario_type: ScenarioType, **kwargs) -> ScrapingTestScenario:
        """
        Generate a test scenario of the specified type.
        
        Args:
            scenario_type: Type of scenario to generate
            **kwargs: Additional parameters for scenario generation
            
        Returns:
            Generated test scenario
        """
        generator = self.scenario_templates[scenario_type]
        return generator(**kwargs)
    
    def generate_all_scenarios(self) -> List[ScrapingTestScenario]:
        """
        Generate all available test scenarios.
        
        Returns:
            List of all test scenarios
        """
        scenarios = []
        
        for scenario_type in ScenarioType:
            try:
                scenario = self.generate_scenario(scenario_type)
                scenarios.append(scenario)
            except Exception as e:
                print(f"Failed to generate scenario {scenario_type}: {e}")
        
        return scenarios
    
    def _create_basic_scraping_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create basic scraping test scenarios."""
        website_type = kwargs.get('website_type', WebsiteType.ECOMMERCE)
        
        if website_type == WebsiteType.ECOMMERCE:
            mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=20)
            expected_results = {
                'product_count': 20,
                'required_fields': ['title', 'price', 'rating'],
                'page_count': 1,
                'navigation_present': True
            }
            validation_rules = [
                lambda results: len(results.get('products', [])) > 0,
                lambda results: all(field in str(results) for field in ['price', 'title']),
                lambda results: 'product-card' in str(results)
            ]
            test_urls = ["/", "/page/1", "/product/1", "/product/5"]
            
        elif website_type == WebsiteType.NEWS:
            mock_site = MockWebsiteGenerator.create_news_site(num_articles=15)
            expected_results = {
                'article_count': 15,
                'required_fields': ['title', 'author', 'date'],
                'page_count': 1,
                'navigation_present': True
            }
            validation_rules = [
                lambda results: 'story-card' in str(results),
                lambda results: 'Breaking News' in str(results),
                lambda results: 'article' in str(results).lower()
            ]
            test_urls = ["/", "/page/1", "/article/1"]
            
        else:
            mock_site = MockWebsiteGenerator.create_blog_site(num_posts=10)
            expected_results = {
                'post_count': 10,
                'required_fields': ['title', 'content', 'date'],
                'page_count': 1
            }
            validation_rules = [
                lambda results: len(str(results)) > 100
            ]
            test_urls = ["/", "/page/1"]
        
        return ScrapingTestScenario(
            name=f"Basic {website_type.value} Scraping",
            description=f"Test basic scraping functionality on a {website_type.value} website",
            scenario_type=ScenarioType.BASIC_SCRAPING,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'website_type': website_type.value}
        )
    
    def _create_error_handling_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create error handling test scenarios."""
        mock_site = MockWebsiteGenerator.create_problematic_site()
        
        expected_results = {
            'error_types': ['network_timeout', 'server_error', 'partial_content', 'encoding_error'],
            'recovery_expected': True,
            'partial_data_acceptable': True
        }
        
        validation_rules = [
            lambda results: 'error' in str(results).lower() or len(str(results)) > 0,
            lambda results: not str(results).startswith('<!DOCTYPE html>') or 'error' in str(results).lower()
        ]
        
        test_urls = ["/", "/page/1", "/page/2", "/product/1", "/product/2"]
        
        return ScrapingTestScenario(
            name="Error Handling",
            description="Test scraper's ability to handle various errors and malformed content",
            scenario_type=ScenarioType.ERROR_HANDLING,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'error_simulation': True}
        )
    
    def _create_pagination_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create pagination test scenarios."""
        num_pages = kwargs.get('num_pages', 5)
        items_per_page = kwargs.get('items_per_page', 10)
        
        mock_site = MockWebsiteGenerator.create_ecommerce_site(
            num_products=num_pages * items_per_page
        )
        
        expected_results = {
            'total_pages': num_pages,
            'items_per_page': items_per_page,
            'pagination_links_present': True,
            'sequential_access': True
        }
        
        validation_rules = [
            lambda results: 'pagination' in str(results).lower(),
            lambda results: 'next' in str(results).lower() or 'previous' in str(results).lower(),
            lambda results: any(f'/page/{i}' in str(results) for i in range(1, num_pages + 1))
        ]
        
        test_urls = [f"/page/{i}" for i in range(1, num_pages + 1)]
        
        return ScrapingTestScenario(
            name="Pagination Handling",
            description="Test scraper's ability to handle paginated content",
            scenario_type=ScenarioType.PAGINATION,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'num_pages': num_pages, 'items_per_page': items_per_page}
        )
    
    def _create_dynamic_content_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create dynamic content test scenarios."""
        mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=30)
        
        expected_results = {
            'dynamic_elements': ['product-card', 'add-to-cart', 'rating'],
            'interactive_content': True,
            'javascript_dependent': False  # Our mock doesn't use JS
        }
        
        validation_rules = [
            lambda results: 'data-product-id' in str(results),
            lambda results: 'button' in str(results).lower(),
            lambda results: 'class=' in str(results)
        ]
        
        test_urls = ["/", "/product/1", "/product/10"]
        
        return ScrapingTestScenario(
            name="Dynamic Content",
            description="Test scraper's ability to handle dynamic and interactive content",
            scenario_type=ScenarioType.DYNAMIC_CONTENT,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'dynamic_simulation': True}
        )
    
    def _create_performance_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create performance test scenarios."""
        num_products = kwargs.get('num_products', 100)
        mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=num_products)
        
        expected_results = {
            'total_items': num_products,
            'max_response_time': 5.0,  # seconds
            'memory_efficient': True,
            'concurrent_requests': True
        }
        
        validation_rules = [
            lambda results: len(str(results)) > 1000,  # Substantial content
            lambda results: 'product' in str(results).lower()
        ]
        
        # Generate many test URLs for performance testing
        test_urls = ["/"] + [f"/page/{i}" for i in range(1, 6)] + [f"/product/{i}" for i in range(1, 21)]
        
        return ScrapingTestScenario(
            name="Performance Testing",
            description="Test scraper's performance with large amounts of content",
            scenario_type=ScenarioType.PERFORMANCE,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'num_products': num_products, 'performance_test': True}
        )
    
    def _create_compliance_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create compliance test scenarios."""
        mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=20)
        
        expected_results = {
            'robots_txt_respected': True,
            'rate_limiting_applied': True,
            'user_agent_sent': True,
            'privacy_compliant': True
        }
        
        validation_rules = [
            lambda results: isinstance(results, (str, dict)),  # Valid response format
            lambda results: len(str(results)) > 0  # Non-empty response
        ]
        
        test_urls = ["/", "/page/1", "/product/1"]
        
        return ScrapingTestScenario(
            name="Compliance Testing",
            description="Test scraper's compliance with ethical scraping practices",
            scenario_type=ScenarioType.COMPLIANCE,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'compliance_test': True}
        )
    
    def _create_data_quality_scenarios(self, **kwargs) -> ScrapingTestScenario:
        """Create data quality test scenarios."""
        mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=25)
        
        expected_results = {
            'data_completeness': 0.9,  # 90% of expected fields present
            'data_accuracy': 0.95,     # 95% of data should be accurate
            'duplicate_detection': True,
            'validation_passed': True
        }
        
        validation_rules = [
            lambda results: 'price' in str(results).lower(),
            lambda results: 'product' in str(results).lower(),
            lambda results: '$' in str(results) or 'price' in str(results).lower(),
            lambda results: len(str(results)) > 500  # Substantial content
        ]
        
        test_urls = ["/", "/page/1", "/product/1", "/product/5", "/product/10"]
        
        return ScrapingTestScenario(
            name="Data Quality Testing",
            description="Test the quality and accuracy of scraped data",
            scenario_type=ScenarioType.DATA_QUALITY,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata={'quality_test': True}
        )
    
    def create_custom_scenario(
        self,
        name: str,
        description: str,
        website_type: WebsiteType,
        scenario_type: ScenarioType,
        **kwargs
    ) -> ScrapingTestScenario:
        """
        Create a custom test scenario.
        
        Args:
            name: Name of the scenario
            description: Description of what the scenario tests
            website_type: Type of website to generate
            scenario_type: Type of scenario
            **kwargs: Additional parameters
            
        Returns:
            Custom test scenario
        """
        # Create appropriate mock website
        if website_type == WebsiteType.ECOMMERCE:
            mock_site = MockWebsiteGenerator.create_ecommerce_site(
                num_products=kwargs.get('num_items', 20),
                include_errors=kwargs.get('include_errors', False)
            )
        elif website_type == WebsiteType.NEWS:
            mock_site = MockWebsiteGenerator.create_news_site(
                num_articles=kwargs.get('num_items', 15),
                include_errors=kwargs.get('include_errors', False)
            )
        elif website_type == WebsiteType.BLOG:
            mock_site = MockWebsiteGenerator.create_blog_site(
                num_posts=kwargs.get('num_items', 10),
                include_errors=kwargs.get('include_errors', False)
            )
        else:
            mock_site = MockWebsiteGenerator.create_directory_site(
                num_entries=kwargs.get('num_items', 50),
                include_errors=kwargs.get('include_errors', False)
            )
        
        expected_results = kwargs.get('expected_results', {})
        validation_rules = kwargs.get('validation_rules', [])
        test_urls = kwargs.get('test_urls', ["/"])
        
        return ScrapingTestScenario(
            name=name,
            description=description,
            scenario_type=scenario_type,
            mock_website=mock_site,
            expected_results=expected_results,
            validation_rules=validation_rules,
            test_urls=test_urls,
            metadata=kwargs.get('metadata', {})
        )
    
    def get_scenario_by_name(self, name: str) -> Optional[ScrapingTestScenario]:
        """
        Get a scenario by name.
        
        Args:
            name: Name of the scenario
            
        Returns:
            Test scenario if found, None otherwise
        """
        return self.scenarios.get(name)
    
    def list_available_scenarios(self) -> List[str]:
        """
        List all available scenario types.
        
        Returns:
            List of scenario type names
        """
        return [scenario_type.value for scenario_type in ScenarioType]