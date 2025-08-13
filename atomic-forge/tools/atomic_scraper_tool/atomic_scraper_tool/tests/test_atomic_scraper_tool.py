"""
Unit tests for the AtomicScraperTool class.

Tests tool initialization, configuration validation, and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from atomic_scraper_tool.tools.atomic_scraper_tool import (
    AtomicScraperTool, 
    AtomicScraperInputSchema, 
    AtomicScraperOutputSchema
)
from atomic_scraper_tool.config.scraper_config import AtomicScraperConfig
from atomic_scraper_tool.models.base_models import ScrapingStrategy
from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
from atomic_scraper_tool.core.exceptions import NetworkError


class TestAtomicScraperInputSchema:
    """Test cases for AtomicScraperInputSchema."""
    
    def test_valid_input_schema(self):
        """Test valid input schema creation."""
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={
                "scrape_type": "list",
                "target_selectors": [".item"]
            },
            schema_recipe={
                "name": "test_recipe",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "extraction_selector": "h1"
                    }
                }
            },
            max_results=20
        )
        
        assert input_data.target_url == "https://example.com"
        assert input_data.strategy["scrape_type"] == "list"
        assert input_data.max_results == 20
    
    def test_invalid_url_format(self):
        """Test validation of invalid URL format."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            AtomicScraperInputSchema(
                target_url="not-a-url",
                strategy={"scrape_type": "list", "target_selectors": [".item"]},
                schema_recipe={"fields": {}},
                max_results=10
            )
    
    def test_invalid_url_scheme(self):
        """Test validation of invalid URL scheme."""
        with pytest.raises(ValueError, match="URL scheme must be http or https"):
            AtomicScraperInputSchema(
                target_url="ftp://example.com",
                strategy={"scrape_type": "list", "target_selectors": [".item"]},
                schema_recipe={"fields": {}},
                max_results=10
            )
    
    def test_empty_url(self):
        """Test validation of empty URL."""
        with pytest.raises(ValueError, match="target_url cannot be empty"):
            AtomicScraperInputSchema(
                target_url="",
                strategy={"scrape_type": "list", "target_selectors": [".item"]},
                schema_recipe={"fields": {}},
                max_results=10
            )


class TestAtomicScraperTool:
    """Test cases for AtomicScraperTool."""
    
    def test_tool_initialization_with_config(self):
        """Test tool initialization with provided config."""
        config = AtomicScraperConfig(
            base_url="https://test.com",
            request_delay=2.0,
            timeout=60,
            min_quality_score=70.0
        )
        
        tool = AtomicScraperTool(config=config)
        
        assert tool.config == config
        assert tool.request_timeout == 60
        assert tool.session.headers['User-Agent'] == config.user_agent
        assert tool.content_extractor is not None
        assert tool.data_processor is not None
        assert tool.quality_analyzer is not None
        assert tool.error_handler is not None
    
    def test_tool_initialization_without_config(self):
        """Test tool initialization with default config."""
        tool = AtomicScraperTool()
        
        assert tool.config is not None
        assert tool.config.base_url == "https://example.com"
        assert tool.request_timeout == tool.config.timeout
        assert tool.content_extractor is not None
        assert tool.data_processor is not None
        assert tool.quality_analyzer is not None
        assert tool.error_handler is not None
    
    def test_validate_inputs_valid(self):
        """Test input validation with valid data."""
        tool = AtomicScraperTool()
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={
                "scrape_type": "list",
                "target_selectors": [".item", ".product"]
            },
            schema_recipe={
                "fields": {
                    "title": {"field_type": "string", "extraction_selector": "h1"}
                }
            },
            max_results=10
        )
        
        # Should not raise any exception
        tool._validate_inputs(input_data)
    
    def test_validate_inputs_empty_strategy(self):
        """Test input validation with empty strategy."""
        tool = AtomicScraperTool()
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={},
            schema_recipe={"fields": {}},
            max_results=10
        )
        
        with pytest.raises(ValueError, match="Strategy cannot be empty"):
            tool._validate_inputs(input_data)
    
    def test_validate_inputs_missing_strategy_fields(self):
        """Test input validation with missing required strategy fields."""
        tool = AtomicScraperTool()
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={"scrape_type": "list"},  # Missing target_selectors
            schema_recipe={"fields": {}},
            max_results=10
        )
        
        with pytest.raises(ValueError, match="Strategy missing required field: target_selectors"):
            tool._validate_inputs(input_data)
    
    def test_validate_inputs_empty_schema_recipe(self):
        """Test input validation with empty schema recipe."""
        tool = AtomicScraperTool()
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={"scrape_type": "list", "target_selectors": [".item"]},
            schema_recipe={},
            max_results=10
        )
        
        with pytest.raises(ValueError, match="Schema recipe cannot be empty"):
            tool._validate_inputs(input_data)
    
    def test_validate_inputs_missing_fields_in_schema(self):
        """Test input validation with missing fields in schema recipe."""
        tool = AtomicScraperTool()
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={"scrape_type": "list", "target_selectors": [".item"]},
            schema_recipe={"name": "test"},  # Missing fields
            max_results=10
        )
        
        with pytest.raises(ValueError, match="Schema recipe must contain 'fields' definition"):
            tool._validate_inputs(input_data)
    
    def test_create_scraping_strategy_valid(self):
        """Test creating scraping strategy from valid dictionary."""
        tool = AtomicScraperTool()
        
        strategy_dict = {
            "scrape_type": "list",
            "target_selectors": [".item", ".product"],
            "pagination_strategy": "next_link",
            "content_filters": ["not_empty"],
            "extraction_rules": {"title": "h1"},
            "max_pages": 5,
            "request_delay": 1.5
        }
        
        strategy = tool._create_scraping_strategy(strategy_dict)
        
        assert isinstance(strategy, ScrapingStrategy)
        assert strategy.scrape_type == "list"
        assert strategy.target_selectors == [".item", ".product"]
        assert strategy.pagination_strategy == "next_link"
        assert strategy.max_pages == 5
        assert strategy.request_delay == 1.5
    
    def test_create_scraping_strategy_invalid(self):
        """Test creating scraping strategy from invalid dictionary."""
        tool = AtomicScraperTool()
        
        strategy_dict = {
            "scrape_type": "invalid_type",  # Invalid scrape type
            "target_selectors": []  # Empty selectors
        }
        
        with pytest.raises(ValueError, match="Invalid strategy configuration"):
            tool._create_scraping_strategy(strategy_dict)
    
    def test_create_schema_recipe_valid(self):
        """Test creating schema recipe from valid dictionary."""
        tool = AtomicScraperTool()
        
        recipe_dict = {
            "name": "test_recipe",
            "description": "Test schema recipe",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Item title",
                    "extraction_selector": "h1",
                    "required": True,
                    "quality_weight": 2.0
                },
                "price": {
                    "field_type": "string",
                    "description": "Item price",
                    "extraction_selector": ".price",
                    "required": False,
                    "quality_weight": 1.5
                }
            },
            "validation_rules": ["require_all_fields"],
            "quality_weights": {
                "completeness": 0.4,
                "accuracy": 0.4,
                "consistency": 0.2
            }
        }
        
        schema_recipe = tool._create_schema_recipe(recipe_dict)
        
        assert isinstance(schema_recipe, SchemaRecipe)
        assert schema_recipe.name == "test_recipe"
        assert len(schema_recipe.fields) == 2
        assert "title" in schema_recipe.fields
        assert "price" in schema_recipe.fields
    
    def test_create_extraction_rules(self):
        """Test creating extraction rules from schema recipe."""
        tool = AtomicScraperTool()
        
        # Create a schema recipe with field definitions
        fields = {
            "title": FieldDefinition(
                field_type="string",
                description="Item title",
                extraction_selector="h1",
                required=True,
                quality_weight=2.0
            ),
            "description": FieldDefinition(
                field_type="string",
                description="Item description",
                extraction_selector=".desc",
                required=False,
                quality_weight=1.0
            )
        }
        
        schema_recipe = SchemaRecipe(
            name="test_recipe",
            description="Test recipe",
            fields=fields,
            validation_rules=[],
            quality_weights={
                "completeness": 0.4,
                "accuracy": 0.4,
                "consistency": 0.2
            }
        )
        
        extraction_rules = tool._create_extraction_rules(schema_recipe)
        
        assert len(extraction_rules) == 2
        assert "title" in extraction_rules
        assert "description" in extraction_rules
        
        title_rule = extraction_rules["title"]
        assert title_rule.field_name == "title"
        assert title_rule.selector == "h1"
        assert title_rule.extraction_type == "text"  # Field type 'string' maps to extraction type 'text'
    
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.requests.Session.get')
    def test_fetch_page_content_success(self, mock_get):
        """Test successful page content fetching."""
        tool = AtomicScraperTool()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        content = tool._fetch_page_content("https://example.com")
        
        assert content == "<html><body>Test content</body></html>"
        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=tool.request_timeout,
            allow_redirects=True
        )
    
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.requests.Session.get')
    def test_fetch_page_content_network_error(self, mock_get):
        """Test page content fetching with network error."""
        tool = AtomicScraperTool()
        
        # Mock network error
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(NetworkError):
            tool._fetch_page_content("https://example.com")
    
    @patch('time.sleep')
    def test_apply_rate_limiting(self, mock_sleep):
        """Test rate limiting application."""
        config = AtomicScraperConfig(
            base_url="https://example.com",
            request_delay=2.5
        )
        tool = AtomicScraperTool(config=config)
        
        tool._apply_rate_limiting()
        
        mock_sleep.assert_called_once_with(2.5)
    
    def test_generate_summary(self):
        """Test summary generation from scraping result."""
        from atomic_scraper_tool.models.base_models import ScrapingResult, ScrapingStrategy, ScrapedItem
        
        tool = AtomicScraperTool()
        
        strategy = ScrapingStrategy(
            scrape_type="list",
            target_selectors=[".item"]
        )
        
        # Create mock scraped items to match total_items_scraped
        mock_items = []
        for i in range(12):
            mock_item = ScrapedItem(
                source_url="https://example.com",
                data={"title": f"Item {i+1}"},
                quality_score=85.5
            )
            mock_items.append(mock_item)
        
        scraping_result = ScrapingResult(
            items=mock_items,
            total_items_found=15,
            total_items_scraped=12,
            average_quality_score=85.5,
            scraping_summary="Test summary",
            strategy_used=strategy,
            errors=["Error 1", "Error 2"],
            execution_time=3.45
        )
        
        summary = tool._generate_summary(scraping_result)
        
        assert "12 items" in summary
        assert "85.5%" in summary
        assert "3.45 seconds" in summary
        assert "2 errors" in summary
    
    def test_extract_quality_metrics(self):
        """Test quality metrics extraction from scraping result."""
        from atomic_scraper_tool.models.base_models import ScrapingResult, ScrapingStrategy, ScrapedItem
        
        tool = AtomicScraperTool()
        
        strategy = ScrapingStrategy(
            scrape_type="list",
            target_selectors=[".item"]
        )
        
        # Create mock scraped items to match total_items_scraped
        mock_items = []
        for i in range(18):
            mock_item = ScrapedItem(
                source_url="https://example.com",
                data={"title": f"Item {i+1}"},
                quality_score=92.3
            )
            mock_items.append(mock_item)
        
        scraping_result = ScrapingResult(
            items=mock_items,
            total_items_found=20,
            total_items_scraped=18,
            average_quality_score=92.3,
            scraping_summary="Test summary",
            strategy_used=strategy,
            errors=[],
            execution_time=2.15
        )
        
        metrics = tool._extract_quality_metrics(scraping_result)
        
        assert metrics['average_quality_score'] == 92.3
        assert metrics['success_rate'] == 90.0  # 18/20 * 100
        assert metrics['total_items_found'] == 20.0
        assert metrics['total_items_scraped'] == 18.0
        assert metrics['execution_time'] == 2.15
    
    def test_get_tool_info(self):
        """Test getting tool information."""
        config = AtomicScraperConfig(
            base_url="https://test.com",
            request_delay=1.5,
            timeout=45,
            max_pages=8,
            max_results=150,
            min_quality_score=75.0
        )
        tool = AtomicScraperTool(config=config)
        
        info = tool.get_tool_info()
        
        assert info['name'] == 'Atomic Scraper Tool'
        assert info['version'] == '1.0.0'
        assert 'description' in info
        assert info['config']['base_url'] == 'https://test.com'
        assert info['config']['request_delay'] == 1.5
        assert info['config']['timeout'] == 45
        assert info['config']['max_pages'] == 8
        assert info['config']['max_results'] == 150
        assert info['config']['min_quality_score'] == 75.0
        assert 'supported_strategies' in info
        assert 'supported_extraction_types' in info
    
    def test_update_config(self):
        """Test configuration updates."""
        tool = AtomicScraperTool()
        original_delay = tool.config.request_delay
        original_timeout = tool.config.timeout
        
        tool.update_config(
            request_delay=3.0,
            timeout=90,
            min_quality_score=80.0
        )
        
        assert tool.config.request_delay == 3.0
        assert tool.config.timeout == 90
        assert tool.config.min_quality_score == 80.0
        assert tool.request_timeout == 90
    
    def test_update_config_user_agent(self):
        """Test user agent configuration update."""
        tool = AtomicScraperTool()
        
        new_user_agent = "TestBot/1.0"
        tool.update_config(user_agent=new_user_agent)
        
        assert tool.config.user_agent == new_user_agent
        assert tool.session.headers['User-Agent'] == new_user_agent
    
    def test_get_error_stats(self):
        """Test getting error statistics."""
        tool = AtomicScraperTool()
        
        stats = tool.get_error_stats()
        
        assert 'error_handler_stats' in stats
        assert 'extractor_stats' in stats
        assert isinstance(stats['error_handler_stats'], dict)
        assert isinstance(stats['extractor_stats'], dict)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        tool = AtomicScraperTool()
        
        # Should not raise any exception
        tool.reset_stats()
    
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._fetch_page_content')
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._extract_items_from_page')
    def test_run_list_scraping_success(self, mock_extract_items, mock_fetch_content):
        """Test successful list scraping execution."""
        from atomic_scraper_tool.models.base_models import ScrapedItem
        
        tool = AtomicScraperTool()
        
        # Mock HTML content
        mock_fetch_content.return_value = "<html><body><div class='item'>Item 1</div></body></html>"
        
        # Mock extracted items
        mock_item = ScrapedItem(
            source_url="https://example.com",
            data={"title": "Item 1", "description": "Test item"},
            quality_score=85.0
        )
        mock_extract_items.return_value = [mock_item]
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={
                "scrape_type": "list",
                "target_selectors": [".item"],
                "max_pages": 1,
                "request_delay": 0.1
            },
            schema_recipe={
                "name": "test_recipe",
                "description": "Test schema recipe for list scraping",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Item title",
                        "extraction_selector": "h1",
                        "required": True
                    }
                }
            },
            max_results=10
        )
        
        result = tool.run(input_data)
        
        assert isinstance(result, AtomicScraperOutputSchema)
        assert result.results['total_scraped'] == 1
        assert len(result.results['items']) == 1
        assert result.results['items'][0]['data']['title'] == "Item 1"
        assert "Successfully scraped 1 items" in result.summary
        assert result.quality_metrics['average_quality_score'] == 85.0
    
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._fetch_page_content')
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._extract_items_from_page')
    def test_run_detail_scraping_success(self, mock_extract_items, mock_fetch_content):
        """Test successful detail page scraping execution."""
        from atomic_scraper_tool.models.base_models import ScrapedItem
        
        tool = AtomicScraperTool()
        
        # Mock HTML content
        mock_fetch_content.return_value = "<html><body><h1>Detail Page</h1></body></html>"
        
        # Mock extracted item
        mock_item = ScrapedItem(
            source_url="https://example.com/detail",
            data={"title": "Detail Page", "content": "Detailed content"},
            quality_score=92.5
        )
        mock_extract_items.return_value = [mock_item]
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com/detail",
            strategy={
                "scrape_type": "detail",
                "target_selectors": ["body"],
                "max_pages": 1,
                "request_delay": 0.1
            },
            schema_recipe={
                "name": "detail_recipe",
                "description": "Test schema recipe for detail scraping",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Page title",
                        "extraction_selector": "h1",
                        "required": True
                    }
                }
            },
            max_results=1
        )
        
        result = tool.run(input_data)
        
        assert isinstance(result, AtomicScraperOutputSchema)
        assert result.results['total_scraped'] == 1
        assert len(result.results['items']) == 1
        assert result.results['items'][0]['data']['title'] == "Detail Page"
        assert "92.5%" in result.summary
        assert result.quality_metrics['average_quality_score'] == 92.5
    
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._fetch_page_content')
    def test_run_scraping_with_network_error(self, mock_fetch_content):
        """Test scraping execution with network error."""
        tool = AtomicScraperTool()
        
        # Mock network error
        mock_fetch_content.side_effect = NetworkError("Connection failed", url="https://example.com")
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={
                "scrape_type": "list",
                "target_selectors": [".item"],
                "max_pages": 1,
                "request_delay": 0.1
            },
            schema_recipe={
                "name": "test_recipe",
                "description": "Test schema recipe",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Item title",
                        "extraction_selector": "h1"
                    }
                }
            },
            max_results=10
        )
        
        result = tool.run(input_data)
        
        assert isinstance(result, AtomicScraperOutputSchema)
        assert result.results['total_scraped'] == 0
        assert len(result.results['items']) == 0
        assert len(result.results['errors']) > 0
        assert "0 items" in result.summary and "errors" in result.summary
        assert result.quality_metrics['average_quality_score'] == 0.0
    
    def test_run_invalid_strategy_type(self):
        """Test scraping execution with invalid strategy type."""
        tool = AtomicScraperTool()
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={
                "scrape_type": "invalid_type",
                "target_selectors": [".item"]
            },
            schema_recipe={
                "name": "test_recipe",
                "description": "Test schema recipe",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Item title",
                        "extraction_selector": "h1"
                    }
                }
            },
            max_results=10
        )
        
        result = tool.run(input_data)
        
        assert isinstance(result, AtomicScraperOutputSchema)
        assert result.results['total_scraped'] == 0
        assert len(result.results['errors']) > 0
        assert "Scraping failed" in result.summary
    
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._fetch_page_content')
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._extract_items_from_page')
    @patch('atomic_scraper_tool.tools.atomic_scraper_tool.AtomicScraperTool._find_next_page_url')
    def test_run_list_scraping_with_pagination(self, mock_find_next, mock_extract_items, mock_fetch_content):
        """Test list scraping with pagination support."""
        from atomic_scraper_tool.models.base_models import ScrapedItem
        
        tool = AtomicScraperTool()
        
        # Mock HTML content for multiple pages
        mock_fetch_content.side_effect = [
            "<html><body><div class='item'>Item 1</div></body></html>",
            "<html><body><div class='item'>Item 2</div></body></html>"
        ]
        
        # Mock extracted items for each page
        mock_item1 = ScrapedItem(
            source_url="https://example.com",
            data={"title": "Item 1"},
            quality_score=85.0
        )
        mock_item2 = ScrapedItem(
            source_url="https://example.com/page/2",
            data={"title": "Item 2"},
            quality_score=90.0
        )
        mock_extract_items.side_effect = [[mock_item1], [mock_item2]]
        
        # Mock pagination - first call returns next page, second returns None
        mock_find_next.side_effect = ["https://example.com/page/2", None]
        
        input_data = AtomicScraperInputSchema(
            target_url="https://example.com",
            strategy={
                "scrape_type": "list",
                "target_selectors": [".item"],
                "pagination_strategy": "next_link",
                "max_pages": 3,
                "request_delay": 0.1
            },
            schema_recipe={
                "name": "test_recipe",
                "description": "Test schema recipe",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Item title",
                        "extraction_selector": "h1"
                    }
                }
            },
            max_results=10
        )
        
        result = tool.run(input_data)
        
        assert isinstance(result, AtomicScraperOutputSchema)
        assert result.results['total_scraped'] == 2
        assert len(result.results['items']) == 2
        assert result.results['items'][0]['data']['title'] == "Item 1"
        assert result.results['items'][1]['data']['title'] == "Item 2"
        assert "Successfully scraped 2 items" in result.summary
        
        # Verify pagination was called
        assert mock_find_next.call_count == 2
    
    def test_extract_items_from_page_single_item(self):
        """Test extracting single item from page."""
        from atomic_scraper_tool.models.base_models import ScrapingStrategy
        from atomic_scraper_tool.models.extraction_models import ExtractionRule
        
        tool = AtomicScraperTool()
        
        html_content = "<html><body><h1>Test Title</h1><p>Test description</p></body></html>"
        source_url = "https://example.com"
        
        strategy = ScrapingStrategy(
            scrape_type="detail",
            target_selectors=["body"]
        )
        
        extraction_rules = {
            "title": ExtractionRule(
                field_name="title",
                selector="h1",
                extraction_type="text"
            ),
            "description": ExtractionRule(
                field_name="description",
                selector="p",
                extraction_type="text"
            )
        }
        
        items = tool._extract_items_from_page(html_content, source_url, strategy, extraction_rules)
        
        assert len(items) == 1
        assert items[0].source_url == source_url
        assert "title" in items[0].data
        assert "description" in items[0].data
        assert items[0].quality_score > 0
    
    def test_find_next_page_url_next_link(self):
        """Test finding next page URL with next_link strategy."""
        tool = AtomicScraperTool()
        
        html_content = '''
        <html>
        <body>
            <div class="pagination">
                <a href="/page/1">1</a>
                <a href="/page/2" class="current">2</a>
                <a href="/page/3" rel="next">Next</a>
            </div>
        </body>
        </html>
        '''
        
        current_url = "https://example.com/page/2"
        next_url = tool._find_next_page_url(html_content, current_url, "next_link")
        
        assert next_url == "https://example.com/page/3"
    
    def test_find_next_page_url_no_next_page(self):
        """Test finding next page URL when no next page exists."""
        tool = AtomicScraperTool()
        
        html_content = '''
        <html>
        <body>
            <div class="pagination">
                <a href="/page/1">1</a>
                <a href="/page/2" class="current">2</a>
            </div>
        </body>
        </html>
        '''
        
        current_url = "https://example.com/page/2"
        next_url = tool._find_next_page_url(html_content, current_url, "next_link")
        
        assert next_url is None
    
    def test_extract_current_page_number(self):
        """Test extracting current page number from URL."""
        tool = AtomicScraperTool()
        
        # Test various URL patterns
        assert tool._extract_current_page_number("https://example.com?page=5") == 5
        assert tool._extract_current_page_number("https://example.com?p=3") == 3
        assert tool._extract_current_page_number("https://example.com/page/7") == 7
        assert tool._extract_current_page_number("https://example.com/p2") == 2
        assert tool._extract_current_page_number("https://example.com-page-4") == 4
        assert tool._extract_current_page_number("https://example.com") == 1  # Default
    
    def test_extract_sitemap_urls_xml(self):
        """Test extracting URLs from XML sitemap."""
        tool = AtomicScraperTool()
        
        xml_sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2023-01-01</lastmod>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
                <lastmod>2023-01-02</lastmod>
            </url>
        </urlset>'''
        
        urls = tool._extract_sitemap_urls(xml_sitemap)
        
        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls
    
    def test_extract_sitemap_urls_html(self):
        """Test extracting URLs from HTML sitemap."""
        tool = AtomicScraperTool()
        
        html_sitemap = '''
        <html>
        <body>
            <ul>
                <li><a href="https://example.com/page1">Page 1</a></li>
                <li><a href="/page2">Page 2</a></li>
                <li><a href="https://example.com/page3">Page 3</a></li>
            </ul>
        </body>
        </html>
        '''
        
        urls = tool._extract_sitemap_urls(html_sitemap)
        
        assert len(urls) == 3
        assert "https://example.com/page1" in urls
        assert "/page2" in urls
        assert "https://example.com/page3" in urls


if __name__ == "__main__":
    pytest.main([__file__])