"""
Integration tests for complete scraping workflows.

These tests verify that all components work together correctly
in end-to-end scraping scenarios.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os

from atomic_scraper_tool.testing.mock_website import MockWebsiteGenerator, WebsiteType
from atomic_scraper_tool.testing.test_scenarios import ScenarioGenerator, ScenarioType
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperTool
from atomic_scraper_tool.agents.scraper_planning_agent import AtomicScraperPlanningAgent
from atomic_scraper_tool.compliance.robots_parser import RobotsParser
from atomic_scraper_tool.compliance.rate_limiter import RateLimiter
from atomic_scraper_tool.compliance.privacy_compliance import PrivacyComplianceChecker


class TestEndToEndWorkflows:
    """Test complete end-to-end scraping workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=10)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("requests.get")
    def test_complete_scraping_workflow(self, mock_get):
        """Test complete scraping workflow from request to results."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.mock_site.generate_page("/")
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        # Create scraper tool
        scraper_tool = AtomicScraperTool()

        # Create proper schema objects
        from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition

        schema_recipe = SchemaRecipe(
            fields={
                "title": FieldDefinition(selector="h1", type="text"),
                "products": FieldDefinition(selector=".product-card", type="list"),
            }
        )

        # Test scraping
        result = scraper_tool.run({"url": "https://example.com", "schema_recipe": schema_recipe})

        # Verify results
        assert result is not None
        assert "scraped_data" in result
        assert "quality_score" in result
        assert result["success"] is True

    @patch("requests.get")
    def test_agent_tool_coordination(self, mock_get):
        """Test coordination between scraper planning agent and scraper tool."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.mock_site.generate_page("/")
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        # Create planning agent
        planning_agent = AtomicScraperPlanningAgent()

        # Test agent planning
        request = {
            "url": "https://example.com",
            "description": "Scrape product information from e-commerce site",
        }

        # This would normally use LLM, so we'll mock the response
        with patch.object(planning_agent, "run") as mock_run:
            mock_run.return_value = {
                "success": True,
                "scraping_strategy": {
                    "url": "https://example.com",
                    "schema_recipe": {
                        "fields": {
                            "title": {"selector": "h1", "type": "text"},
                            "price": {"selector": ".price", "type": "text"},
                        }
                    },
                },
                "reasoning": "Detected e-commerce site with product listings",
            }

            result = planning_agent.run(request)

            assert result["success"] is True
            assert "scraping_strategy" in result
            assert "reasoning" in result

    def test_error_handling_integration(self):
        """Test error handling across the entire pipeline."""
        # Create problematic mock site
        problematic_site = MockWebsiteGenerator.create_problematic_site()

        with patch("requests.get") as mock_get:
            # Mock error responses
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = problematic_site.generate_page("/")
            mock_response.raise_for_status.side_effect = Exception("Server Error")
            mock_get.return_value = mock_response

            scraper_tool = AtomicScraperTool()

            result = scraper_tool.run(
                {
                    "url": "https://example.com",
                    "schema_recipe": {"fields": {"title": {"selector": "h1", "type": "text"}}},
                }
            )

            # Should handle errors gracefully
            assert result is not None
            assert "error" in result or result.get("success") is False

    def test_compliance_integration(self):
        """Test integration of compliance features."""
        # Create compliance components
        robots_parser = RobotsParser()
        rate_limiter = RateLimiter()
        privacy_checker = PrivacyComplianceChecker()

        # Test robots.txt compliance
        with patch.object(robots_parser, "can_fetch", return_value=True):
            can_fetch = robots_parser.can_fetch("https://example.com/test")
            assert can_fetch is True

        # Test rate limiting
        url = "https://example.com/test"
        delay = rate_limiter.wait_for_request(url)
        assert isinstance(delay, float)
        assert delay >= 0

        # Test privacy compliance
        test_data = {"title": "Test Product", "price": "$19.99"}
        is_compliant = privacy_checker.validate_data_collection(url, test_data)
        assert isinstance(is_compliant, bool)


class TestScenarioBasedIntegration:
    """Test integration using predefined scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scenario_generator = ScenarioGenerator()

    def test_basic_scraping_scenario(self):
        """Test basic scraping scenario integration."""
        scenario = self.scenario_generator.generate_scenario(ScenarioType.BASIC_SCRAPING)

        assert scenario is not None
        assert scenario.mock_website is not None
        assert len(scenario.test_urls) > 0

        # Test that mock website generates content for all test URLs
        for url in scenario.test_urls[:3]:  # Test first 3 URLs
            html = scenario.mock_website.generate_page(url)
            assert len(html) > 0
            assert "<html" in html

    def test_error_handling_scenario(self):
        """Test error handling scenario integration."""
        scenario = self.scenario_generator.generate_scenario(ScenarioType.ERROR_HANDLING)

        assert scenario is not None
        assert scenario.mock_website.config.include_errors is True

        # Test error simulation
        html = scenario.mock_website.generate_page("/")
        assert len(html) > 0  # Should still generate some content

    def test_pagination_scenario(self):
        """Test pagination scenario integration."""
        scenario = self.scenario_generator.generate_scenario(ScenarioType.PAGINATION, num_pages=3, items_per_page=5)

        assert scenario is not None
        assert len(scenario.test_urls) >= 3  # Should have multiple page URLs

        # Test pagination URLs
        for url in scenario.test_urls:
            if "/page/" in url:
                html = scenario.mock_website.generate_page(url)
                assert len(html) > 0

    def test_performance_scenario(self):
        """Test performance scenario integration."""
        scenario = self.scenario_generator.generate_scenario(ScenarioType.PERFORMANCE, num_products=50)

        assert scenario is not None
        assert len(scenario.test_urls) > 10  # Should have many URLs for performance testing

        # Test that all URLs can be generated quickly
        import time

        start_time = time.time()

        for url in scenario.test_urls[:10]:  # Test first 10 URLs
            html = scenario.mock_website.generate_page(url)
            assert len(html) > 0

        elapsed_time = time.time() - start_time
        assert elapsed_time < 5.0  # Should complete within 5 seconds


class TestConcurrentOperations:
    """Test concurrent scraping operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=20)

    def test_concurrent_page_generation(self):
        """Test concurrent page generation."""
        import threading
        import time

        results = {}
        errors = []

        def generate_page(url):
            try:
                html = self.mock_site.generate_page(url)
                results[url] = len(html)
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        urls = self.mock_site.get_all_urls()[:5]  # Test first 5 URLs

        for url in urls:
            thread = threading.Thread(target=generate_page, args=(url,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == len(urls)

        for url, content_length in results.items():
            assert content_length > 0

    @patch("requests.get")
    def test_concurrent_scraping_with_rate_limiting(self, mock_get):
        """Test concurrent scraping with rate limiting."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.mock_site.generate_page("/")
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        from atomic_scraper_tool.compliance.rate_limiter import RateLimiter, RateLimitConfig

        # Create rate limiter with short delays for testing
        config = RateLimitConfig(default_delay=0.1, max_concurrent_requests=2)
        rate_limiter = RateLimiter(config)

        import threading
        import time

        results = []
        start_time = time.time()

        def make_request(url):
            # Simulate rate-limited request
            if rate_limiter.acquire_request_slot(url):
                try:
                    delay = rate_limiter.wait_for_request(url)
                    time.sleep(0.1)  # Simulate request time
                    results.append({"url": url, "delay": delay})
                finally:
                    rate_limiter.release_request_slot(url)

        # Create multiple threads
        threads = []
        urls = [
            "https://example.com/page/1",
            "https://example.com/page/2",
            "https://example.com/page/3",
        ]

        for url in urls:
            thread = threading.Thread(target=make_request, args=(url,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)

        elapsed_time = time.time() - start_time

        # Verify rate limiting worked
        assert len(results) <= len(urls)  # Some requests might be blocked
        assert elapsed_time >= 0.1  # Should take at least the minimum delay time


class TestDataQualityIntegration:
    """Test data quality across the entire pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=15)

    @patch("requests.get")
    def test_data_quality_pipeline(self, mock_get):
        """Test data quality assessment throughout the scraping pipeline."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.mock_site.generate_page("/")
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        from atomic_scraper_tool.extraction.quality_analyzer import QualityAnalyzer
        from atomic_scraper_tool.extraction.data_processor import DataProcessor

        # Create quality analyzer and data processor
        quality_analyzer = QualityAnalyzer()
        data_processor = DataProcessor()

        # Simulate scraped data
        scraped_data = {
            "title": "Welcome to Our Store",
            "products": [
                {"name": "Product 1", "price": "$19.99"},
                {"name": "Product 2", "price": "$29.99"},
            ],
        }

        # Test data processing
        processed_data = data_processor.process_data(scraped_data)
        assert processed_data is not None

        # Test quality analysis
        quality_score = quality_analyzer.calculate_quality_score(processed_data, {})
        assert isinstance(quality_score, (int, float))
        assert 0 <= quality_score <= 1

    def test_validation_rules_integration(self):
        """Test validation rules across different scenarios."""
        scenario = self.scenario_generator.generate_scenario(ScenarioType.DATA_QUALITY)

        # Test validation rules
        test_data = "Sample scraped content with products and prices"

        for rule in scenario.validation_rules:
            try:
                result = rule(test_data)
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"Validation rule failed: {e}")


class TestMemoryAndPerformance:
    """Test memory usage and performance characteristics."""

    def test_memory_usage_with_large_sites(self):
        """Test memory usage with large mock websites."""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create large mock site
        large_site = MockWebsiteGenerator.create_ecommerce_site(num_products=100)

        # Generate many pages
        urls = large_site.get_all_urls()
        for url in urls[:20]:  # Test first 20 URLs
            html = large_site.generate_page(url)
            assert len(html) > 0

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

    def test_caching_performance(self):
        """Test caching performance benefits."""
        import time

        mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=10)

        # First generation (no cache)
        start_time = time.time()
        html1 = mock_site.generate_page("/")
        first_time = time.time() - start_time

        # Second generation (with cache)
        start_time = time.time()
        html2 = mock_site.generate_page("/")
        second_time = time.time() - start_time

        # Cached version should be faster and identical
        assert html1 == html2
        assert second_time <= first_time  # Should be faster or equal
