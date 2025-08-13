"""
Unit tests for base data models.

Tests validation functions and data integrity for ScrapedItem, ScrapingResult, and ScrapingStrategy models.
"""

import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from atomic_scraper_tool.models.base_models import (
    ScrapingStrategy,
    ScrapedItem,
    ScrapingResult,
    validate_css_selector,
    validate_url,
    calculate_quality_score
)


class TestScrapingStrategy:
    """Test cases for ScrapingStrategy model."""
    
    def test_valid_strategy_creation(self):
        """Test creating a valid scraping strategy."""
        strategy = ScrapingStrategy(
            scrape_type="list",
            target_selectors=[".item", "#content"],
            pagination_strategy="next_link",
            content_filters=["text", "links"],
            extraction_rules={"title": "h1", "description": ".desc"},
            max_pages=5,
            request_delay=2.0
        )
        
        assert strategy.scrape_type == "list"
        assert strategy.target_selectors == [".item", "#content"]
        assert strategy.pagination_strategy == "next_link"
        assert strategy.max_pages == 5
        assert strategy.request_delay == 2.0
    
    def test_invalid_scrape_type(self):
        """Test validation of invalid scrape_type."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="invalid_type",
                target_selectors=[".item"]
            )
        
        assert "scrape_type must be one of" in str(exc_info.value)
    
    def test_empty_target_selectors(self):
        """Test validation of empty target_selectors."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[]
            )
        
        assert "target_selectors cannot be empty" in str(exc_info.value)
    
    def test_invalid_css_selector(self):
        """Test validation of invalid CSS selectors."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=["<invalid>selector"]
            )
        
        assert "Invalid CSS selector syntax" in str(exc_info.value)
    
    def test_empty_selector_string(self):
        """Test validation of empty selector strings."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[""]
            )
        
        assert "target_selectors cannot contain empty strings" in str(exc_info.value)
    
    def test_invalid_pagination_strategy(self):
        """Test validation of invalid pagination strategy."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[".item"],
                pagination_strategy="invalid_strategy"
            )
        
        assert "pagination_strategy must be one of" in str(exc_info.value)
    
    def test_valid_pagination_strategies(self):
        """Test all valid pagination strategies."""
        valid_strategies = ['next_link', 'page_numbers', 'infinite_scroll', 'load_more']
        
        for strategy in valid_strategies:
            scraping_strategy = ScrapingStrategy(
                scrape_type="list",
                target_selectors=[".item"],
                pagination_strategy=strategy
            )
            assert scraping_strategy.pagination_strategy == strategy
    
    def test_invalid_extraction_rules(self):
        """Test validation of invalid extraction rules."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[".item"],
                extraction_rules={"": "h1"}  # Empty field name
            )
        
        assert "extraction_rules field names cannot be empty" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[".item"],
                extraction_rules={"title": ""}  # Empty selector
            )
        
        assert "extraction_rules selector for 'title' cannot be empty" in str(exc_info.value)
    
    def test_field_constraints(self):
        """Test field constraints validation."""
        # Test max_pages minimum value
        with pytest.raises(ValidationError):
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[".item"],
                max_pages=0
            )
        
        # Test request_delay minimum value
        with pytest.raises(ValidationError):
            ScrapingStrategy(
                scrape_type="list",
                target_selectors=[".item"],
                request_delay=0.05
            )


class TestScrapedItem:
    """Test cases for ScrapedItem model."""
    
    def test_valid_item_creation(self):
        """Test creating a valid scraped item."""
        item = ScrapedItem(
            source_url="https://example.com/page1",
            data={"title": "Test Title", "price": 29.99},
            quality_score=85.5
        )
        
        assert item.source_url == "https://example.com/page1"
        assert item.data == {"title": "Test Title", "price": 29.99}
        assert item.quality_score == 85.5
        assert isinstance(item.id, str)
        assert isinstance(item.scraped_at, datetime)
        assert item.schema_version == "1.0"
    
    def test_auto_generated_fields(self):
        """Test auto-generated fields."""
        item = ScrapedItem(
            source_url="https://example.com/page1",
            data={"title": "Test"},
            quality_score=75.0
        )
        
        # Test UUID format
        uuid.UUID(item.id)  # Should not raise exception
        
        # Test timestamp is recent
        time_diff = datetime.utcnow() - item.scraped_at
        assert time_diff.total_seconds() < 1.0
    
    def test_invalid_source_url(self):
        """Test validation of invalid source URLs."""
        # Empty URL
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="",
                data={"title": "Test"},
                quality_score=75.0
            )
        
        assert "source_url cannot be empty" in str(exc_info.value)
        
        # Invalid URL format
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="not-a-url",
                data={"title": "Test"},
                quality_score=75.0
            )
        
        assert "Invalid URL format" in str(exc_info.value)
        
        # Invalid scheme
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="ftp://example.com",
                data={"title": "Test"},
                quality_score=75.0
            )
        
        assert "URL scheme must be http or https" in str(exc_info.value)
    
    def test_empty_data(self):
        """Test validation of empty data."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="https://example.com",
                data={},
                quality_score=75.0
            )
        
        assert "data cannot be empty" in str(exc_info.value)
    
    def test_invalid_data_types(self):
        """Test validation of invalid data types."""
        # Non-string keys
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="https://example.com",
                data={123: "value"},
                quality_score=75.0
            )
        
        assert "Input should be a valid string" in str(exc_info.value)
        
        # Non-JSON serializable values
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="https://example.com",
                data={"title": lambda x: x},  # Function is not JSON serializable
                quality_score=75.0
            )
        
        assert "is not JSON serializable" in str(exc_info.value)
    
    def test_valid_data_types(self):
        """Test valid JSON-serializable data types."""
        valid_data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, "three"],
            "nested_dict": {"key": "value"},
            "mixed_list": [1, "two", {"three": 3}]
        }
        
        item = ScrapedItem(
            source_url="https://example.com",
            data=valid_data,
            quality_score=75.0
        )
        
        assert item.data == valid_data
    
    def test_quality_score_bounds(self):
        """Test quality score bounds validation."""
        # Below minimum
        with pytest.raises(ValidationError):
            ScrapedItem(
                source_url="https://example.com",
                data={"title": "Test"},
                quality_score=-1.0
            )
        
        # Above maximum
        with pytest.raises(ValidationError):
            ScrapedItem(
                source_url="https://example.com",
                data={"title": "Test"},
                quality_score=101.0
            )
        
        # Valid bounds
        item_min = ScrapedItem(
            source_url="https://example.com",
            data={"title": "Test"},
            quality_score=0.0
        )
        assert item_min.quality_score == 0.0
        
        item_max = ScrapedItem(
            source_url="https://example.com",
            data={"title": "Test"},
            quality_score=100.0
        )
        assert item_max.quality_score == 100.0
    
    def test_invalid_schema_version(self):
        """Test validation of invalid schema version."""
        with pytest.raises(ValidationError) as exc_info:
            ScrapedItem(
                source_url="https://example.com",
                data={"title": "Test"},
                quality_score=75.0,
                schema_version="invalid"
            )
        
        assert "schema_version must be in format 'X.Y'" in str(exc_info.value)


class TestScrapingResult:
    """Test cases for ScrapingResult model."""
    
    def create_sample_items(self, count: int = 3) -> list:
        """Create sample scraped items for testing."""
        items = []
        for i in range(count):
            items.append(ScrapedItem(
                source_url=f"https://example.com/item{i}",
                data={"title": f"Item {i}", "value": i * 10},
                quality_score=80.0 + i * 5
            ))
        return items
    
    def create_sample_strategy(self) -> ScrapingStrategy:
        """Create sample scraping strategy for testing."""
        return ScrapingStrategy(
            scrape_type="list",
            target_selectors=[".item"]
        )
    
    def test_valid_result_creation(self):
        """Test creating a valid scraping result."""
        items = self.create_sample_items(3)
        strategy = self.create_sample_strategy()
        
        result = ScrapingResult(
            items=items,
            total_items_found=5,
            total_items_scraped=3,
            average_quality_score=85.0,
            scraping_summary="Successfully scraped 3 out of 5 items",
            strategy_used=strategy,
            execution_time=2.5
        )
        
        assert len(result.items) == 3
        assert result.total_items_found == 5
        assert result.total_items_scraped == 3
        assert result.average_quality_score == 85.0
        assert result.success_rate == 60.0
    
    def test_scraped_count_validation(self):
        """Test validation that scraped count doesn't exceed found count."""
        items = self.create_sample_items(3)
        strategy = self.create_sample_strategy()
        
        with pytest.raises(ValidationError) as exc_info:
            ScrapingResult(
                items=items,
                total_items_found=2,  # Less than scraped count
                total_items_scraped=3,
                average_quality_score=85.0,
                scraping_summary="Test",
                strategy_used=strategy,
                execution_time=1.0
            )
        
        assert "total_items_scraped cannot exceed total_items_found" in str(exc_info.value)
    
    def test_average_quality_validation(self):
        """Test validation of average quality score against items."""
        items = self.create_sample_items(3)  # Quality scores: 80, 85, 90
        strategy = self.create_sample_strategy()
        expected_avg = (80.0 + 85.0 + 90.0) / 3  # 85.0
        
        # Correct average should work
        result = ScrapingResult(
            items=items,
            total_items_found=3,
            total_items_scraped=3,
            average_quality_score=expected_avg,
            scraping_summary="Test",
            strategy_used=strategy,
            execution_time=1.0
        )
        assert result.average_quality_score == expected_avg
        
        # Incorrect average should fail
        with pytest.raises(ValidationError) as exc_info:
            ScrapingResult(
                items=items,
                total_items_found=3,
                total_items_scraped=3,
                average_quality_score=50.0,  # Wrong average
                scraping_summary="Test",
                strategy_used=strategy,
                execution_time=1.0
            )
        
        assert "average_quality_score" in str(exc_info.value)
        assert "doesn't match calculated average" in str(exc_info.value)
    
    def test_consistency_validation(self):
        """Test overall consistency validation."""
        items = self.create_sample_items(3)
        strategy = self.create_sample_strategy()
        
        # Mismatch between items count and total_items_scraped
        with pytest.raises(ValidationError) as exc_info:
            ScrapingResult(
                items=items,  # 3 items
                total_items_found=5,
                total_items_scraped=2,  # Says 2 but has 3 items
                average_quality_score=85.0,
                scraping_summary="Test",
                strategy_used=strategy,
                execution_time=1.0
            )
        
        assert "Number of items" in str(exc_info.value)
        assert "doesn't match total_items_scraped" in str(exc_info.value)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        items = self.create_sample_items(3)
        strategy = self.create_sample_strategy()
        
        # Normal case
        result = ScrapingResult(
            items=items,
            total_items_found=10,
            total_items_scraped=3,
            average_quality_score=85.0,
            scraping_summary="Test",
            strategy_used=strategy,
            execution_time=1.0
        )
        assert result.success_rate == 30.0
        
        # Zero found items
        result_zero = ScrapingResult(
            items=[],
            total_items_found=0,
            total_items_scraped=0,
            average_quality_score=0.0,
            scraping_summary="No items found",
            strategy_used=strategy,
            execution_time=1.0
        )
        assert result_zero.success_rate == 0.0
    
    def test_field_constraints(self):
        """Test field constraints validation."""
        items = self.create_sample_items(1)
        strategy = self.create_sample_strategy()
        
        # Negative total_items_found
        with pytest.raises(ValidationError):
            ScrapingResult(
                items=items,
                total_items_found=-1,
                total_items_scraped=1,
                average_quality_score=85.0,
                scraping_summary="Test",
                strategy_used=strategy,
                execution_time=1.0
            )
        
        # Negative execution_time
        with pytest.raises(ValidationError):
            ScrapingResult(
                items=items,
                total_items_found=1,
                total_items_scraped=1,
                average_quality_score=85.0,
                scraping_summary="Test",
                strategy_used=strategy,
                execution_time=-1.0
            )


class TestValidationUtilities:
    """Test cases for validation utility functions."""
    
    def test_validate_css_selector(self):
        """Test CSS selector validation function."""
        # Valid selectors
        assert validate_css_selector(".class")
        assert validate_css_selector("#id")
        assert validate_css_selector("div.class")
        assert validate_css_selector("div > p")
        assert validate_css_selector("[data-attr='value']")
        assert validate_css_selector("input[type='text']")
        
        # Invalid selectors
        assert not validate_css_selector("")
        assert not validate_css_selector("   ")
        assert not validate_css_selector("<invalid>")
        assert not validate_css_selector("selector{}")
    
    def test_validate_url(self):
        """Test URL validation function."""
        # Valid URLs
        assert validate_url("https://example.com")
        assert validate_url("http://example.com")
        assert validate_url("https://example.com/path")
        assert validate_url("https://subdomain.example.com")
        
        # Invalid URLs
        assert not validate_url("")
        assert not validate_url("   ")
        assert not validate_url("not-a-url")
        assert not validate_url("ftp://example.com")
        assert not validate_url("example.com")  # Missing scheme
    
    def test_calculate_quality_score(self):
        """Test quality score calculation function."""
        # All fields present
        data = {"title": "Test", "price": "29.99", "description": "A test item"}
        expected_fields = ["title", "price", "description"]
        assert calculate_quality_score(data, expected_fields) == 100.0
        
        # Some fields missing
        data = {"title": "Test", "price": "29.99"}
        expected_fields = ["title", "price", "description"]
        assert abs(calculate_quality_score(data, expected_fields) - 200/3) < 0.01  # 66.67%
        
        # Empty/null values don't count
        data = {"title": "Test", "price": "", "description": None}
        expected_fields = ["title", "price", "description"]
        assert abs(calculate_quality_score(data, expected_fields) - 100/3) < 0.01  # 33.33%
        
        # No expected fields
        data = {"title": "Test"}
        expected_fields = []
        assert calculate_quality_score(data, expected_fields) == 100.0
        
        # No data
        data = {}
        expected_fields = ["title", "price"]
        assert calculate_quality_score(data, expected_fields) == 0.0


if __name__ == "__main__":
    pytest.main([__file__])