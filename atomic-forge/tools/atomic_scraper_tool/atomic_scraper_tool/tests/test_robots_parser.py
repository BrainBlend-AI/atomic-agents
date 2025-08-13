"""
Unit tests for robots.txt parser functionality.
"""

import time
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests

from atomic_scraper_tool.compliance.robots_parser import (
    RobotsParser, 
    RobotsTxtInfo, 
    RobotsTxtRule
)
from atomic_scraper_tool.core.exceptions import ScrapingError


class TestRobotsParser:
    """Test cases for RobotsParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RobotsParser(user_agent="TestBot/1.0")
        
    def test_init(self):
        """Test RobotsParser initialization."""
        parser = RobotsParser(user_agent="CustomBot", timeout=20)
        assert parser.user_agent == "CustomBot"
        assert parser.timeout == 20
        assert parser._cache == {}
        assert parser._cache_ttl == 3600
    
    def test_get_domain(self):
        """Test domain extraction from URLs."""
        assert self.parser._get_domain("https://example.com/path") == "example.com"
        assert self.parser._get_domain("http://subdomain.example.com") == "subdomain.example.com"
        assert self.parser._get_domain("https://EXAMPLE.COM/PATH") == "example.com"
    
    @patch('requests.get')
    def test_fetch_and_parse_robots_success(self, mock_get):
        """Test successful robots.txt fetching and parsing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
User-agent: *
Disallow: /private/
Allow: /public/
Crawl-delay: 1
Sitemap: https://example.com/sitemap.xml

User-agent: TestBot
Disallow: /admin/
Crawl-delay: 2
"""
        mock_get.return_value = mock_response
        
        robots_info = self.parser._fetch_and_parse_robots("https://example.com/robots.txt")
        
        assert robots_info.url == "https://example.com/robots.txt"
        assert robots_info.is_accessible is True
        assert robots_info.crawl_delay == 2.0  # Last crawl-delay wins
        assert "https://example.com/sitemap.xml" in robots_info.sitemap_urls
        assert len(robots_info.rules) == 5  # Including crawl-delay rules
        
        # Check specific rules
        rule_paths = [rule.path for rule in robots_info.rules]
        assert "/private/" in rule_paths
        assert "/public/" in rule_paths
        assert "/admin/" in rule_paths
    
    @patch('requests.get')
    def test_fetch_and_parse_robots_404(self, mock_get):
        """Test handling of missing robots.txt (404 response)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        robots_info = self.parser._fetch_and_parse_robots("https://example.com/robots.txt")
        
        assert robots_info.url == "https://example.com/robots.txt"
        assert robots_info.is_accessible is False
        assert robots_info.content == ""
        assert len(robots_info.rules) == 0
    
    @patch('requests.get')
    def test_fetch_and_parse_robots_network_error(self, mock_get):
        """Test handling of network errors when fetching robots.txt."""
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(ScrapingError) as exc_info:
            self.parser._fetch_and_parse_robots("https://example.com/robots.txt")
        
        assert "Failed to fetch robots.txt" in str(exc_info.value)
        assert exc_info.value.error_type == "network_error"
    
    def test_parse_robots_content(self):
        """Test parsing of robots.txt content."""
        content = """
# This is a comment
User-agent: *
Disallow: /private/
Allow: /public/

User-agent: GoogleBot
Disallow: /admin/
Crawl-delay: 5
Request-rate: 1/10s

Sitemap: https://example.com/sitemap1.xml
Sitemap: https://example.com/sitemap2.xml
"""
        
        robots_info = self.parser._parse_robots_content(
            "https://example.com/robots.txt", 
            content
        )
        
        assert robots_info.crawl_delay == 5.0
        assert robots_info.request_rate == "1/10s"
        assert len(robots_info.sitemap_urls) == 2
        assert len(robots_info.rules) == 4
        
        # Check rule details
        googlebot_rules = [r for r in robots_info.rules if r.user_agent == "GoogleBot"]
        assert len(googlebot_rules) == 2
        assert any(r.path == "/admin/" and r.directive == "Disallow" for r in googlebot_rules)
    
    @patch.object(RobotsParser, '_fetch_and_parse_robots')
    def test_get_robots_info_caching(self, mock_fetch):
        """Test caching behavior of get_robots_info."""
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="User-agent: *\nDisallow: /",
            last_fetched=time.time()
        )
        mock_fetch.return_value = mock_robots_info
        
        # First call should fetch
        result1 = self.parser.get_robots_info("https://example.com/test")
        assert mock_fetch.call_count == 1
        
        # Second call should use cache
        result2 = self.parser.get_robots_info("https://example.com/test")
        assert mock_fetch.call_count == 1
        assert result1 == result2
        
        # Force refresh should fetch again
        result3 = self.parser.get_robots_info("https://example.com/test", force_refresh=True)
        assert mock_fetch.call_count == 2
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_can_fetch_allowed(self, mock_get_robots):
        """Test can_fetch method for allowed URLs."""
        # Mock robots info with content that allows /public/
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="User-agent: *\nAllow: /public/",
            is_accessible=True
        )
        mock_get_robots.return_value = mock_robots_info
        
        result = self.parser.can_fetch("https://example.com/public/page")
        
        assert result is True
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_can_fetch_disallowed(self, mock_get_robots):
        """Test can_fetch method for disallowed URLs."""
        # Mock robots info with content that disallows /private/
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="User-agent: *\nDisallow: /private/",
            is_accessible=True
        )
        mock_get_robots.return_value = mock_robots_info
        
        result = self.parser.can_fetch("https://example.com/private/page")
        
        assert result is False
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_can_fetch_no_robots_txt(self, mock_get_robots):
        """Test can_fetch when robots.txt is not accessible."""
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="",
            is_accessible=False
        )
        mock_get_robots.return_value = mock_robots_info
        
        result = self.parser.can_fetch("https://example.com/any/page")
        
        assert result is True  # Should allow when no robots.txt
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_get_crawl_delay(self, mock_get_robots):
        """Test crawl delay extraction."""
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="",
            crawl_delay=2.5,
            rules=[
                RobotsTxtRule(user_agent="TestBot/1.0", directive="Crawl-delay", path="5.0"),
                RobotsTxtRule(user_agent="*", directive="Crawl-delay", path="1.0")
            ]
        )
        mock_get_robots.return_value = mock_robots_info
        
        # Should return user-agent specific delay
        delay = self.parser.get_crawl_delay("https://example.com/test")
        assert delay == 5.0
        
        # Test with different user agent
        delay = self.parser.get_crawl_delay("https://example.com/test", "OtherBot")
        assert delay == 1.0  # Should fall back to * rule
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_get_request_rate(self, mock_get_robots):
        """Test request rate extraction."""
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="",
            request_rate="1/5s"
        )
        mock_get_robots.return_value = mock_robots_info
        
        rate = self.parser.get_request_rate("https://example.com/test")
        assert rate == "1/5s"
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_get_sitemap_urls(self, mock_get_robots):
        """Test sitemap URL extraction."""
        mock_robots_info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="",
            sitemap_urls=[
                "https://example.com/sitemap.xml",
                "https://example.com/sitemap-news.xml"
            ]
        )
        mock_get_robots.return_value = mock_robots_info
        
        sitemaps = self.parser.get_sitemap_urls("https://example.com/test")
        assert len(sitemaps) == 2
        assert "https://example.com/sitemap.xml" in sitemaps
        assert "https://example.com/sitemap-news.xml" in sitemaps
    
    @patch.object(RobotsParser, 'can_fetch')
    def test_filter_urls(self, mock_can_fetch):
        """Test URL filtering based on robots.txt rules."""
        # Mock can_fetch to return True for some URLs, False for others
        def mock_can_fetch_side_effect(url, user_agent=None):
            return "allowed" in url
        
        mock_can_fetch.side_effect = mock_can_fetch_side_effect
        
        urls = [
            "https://example.com/allowed/page1",
            "https://example.com/blocked/page2",
            "https://example.com/allowed/page3",
            "https://example.com/blocked/page4"
        ]
        
        filtered_urls = self.parser.filter_urls(urls)
        
        assert len(filtered_urls) == 2
        assert "https://example.com/allowed/page1" in filtered_urls
        assert "https://example.com/allowed/page3" in filtered_urls
        assert "https://example.com/blocked/page2" not in filtered_urls
        assert "https://example.com/blocked/page4" not in filtered_urls
    
    @patch.object(RobotsParser, 'get_robots_info')
    def test_error_handling_graceful_degradation(self, mock_get_robots):
        """Test graceful error handling."""
        mock_get_robots.side_effect = Exception("Network error")
        
        # Should return False for can_fetch on error
        result = self.parser.can_fetch("https://example.com/test")
        assert result is False
        
        # Should return None for crawl_delay on error
        delay = self.parser.get_crawl_delay("https://example.com/test")
        assert delay is None
        
        # Should return empty list for sitemaps on error
        sitemaps = self.parser.get_sitemap_urls("https://example.com/test")
        assert sitemaps == []


class TestRobotsTxtModels:
    """Test cases for robots.txt data models."""
    
    def test_robots_txt_rule_model(self):
        """Test RobotsTxtRule model."""
        rule = RobotsTxtRule(
            user_agent="TestBot",
            directive="Disallow",
            path="/private/"
        )
        
        assert rule.user_agent == "TestBot"
        assert rule.directive == "Disallow"
        assert rule.path == "/private/"
    
    def test_robots_txt_info_model(self):
        """Test RobotsTxtInfo model."""
        info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content="User-agent: *\nDisallow: /",
            crawl_delay=1.5,
            sitemap_urls=["https://example.com/sitemap.xml"],
            rules=[
                RobotsTxtRule(user_agent="*", directive="Disallow", path="/")
            ]
        )
        
        assert info.url == "https://example.com/robots.txt"
        assert info.crawl_delay == 1.5
        assert len(info.sitemap_urls) == 1
        assert len(info.rules) == 1
        assert info.is_accessible is True
        assert isinstance(info.last_fetched, float)
    
    def test_robots_txt_info_defaults(self):
        """Test RobotsTxtInfo model with default values."""
        info = RobotsTxtInfo(
            url="https://example.com/robots.txt",
            content=""
        )
        
        assert info.crawl_delay is None
        assert info.request_rate is None
        assert info.sitemap_urls == []
        assert info.rules == []
        assert info.is_accessible is True