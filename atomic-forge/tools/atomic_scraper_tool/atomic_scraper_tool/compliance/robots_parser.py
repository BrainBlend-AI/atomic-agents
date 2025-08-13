"""
Robots.txt parser for ethical web scraping compliance.

This module provides functionality to fetch, parse, and respect robots.txt files
according to the Robots Exclusion Protocol.
"""

import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from pydantic import BaseModel, Field

from atomic_scraper_tool.core.exceptions import ScrapingError


class RobotsTxtRule(BaseModel):
    """Represents a single robots.txt rule."""
    user_agent: str
    directive: str  # "Allow" or "Disallow"
    path: str
    
    
class RobotsTxtInfo(BaseModel):
    """Complete robots.txt information for a domain."""
    url: str
    content: str
    crawl_delay: Optional[float] = None
    request_rate: Optional[str] = None
    sitemap_urls: List[str] = Field(default_factory=list)
    rules: List[RobotsTxtRule] = Field(default_factory=list)
    last_fetched: float = Field(default_factory=time.time)
    is_accessible: bool = True


class RobotsParser:
    """
    Parser for robots.txt files with compliance checking capabilities.
    
    This class handles fetching, parsing, and interpreting robots.txt files
    to ensure ethical web scraping practices.
    """
    
    def __init__(self, user_agent: str = "*", timeout: int = 10):
        """
        Initialize the robots parser.
        
        Args:
            user_agent: User agent string to use for compliance checking
            timeout: Timeout for fetching robots.txt files
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache: Dict[str, RobotsTxtInfo] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        
    def get_robots_info(self, url: str, force_refresh: bool = False) -> RobotsTxtInfo:
        """
        Get robots.txt information for a given URL.
        
        Args:
            url: The URL to check robots.txt for
            force_refresh: Whether to bypass cache and fetch fresh data
            
        Returns:
            RobotsTxtInfo object containing parsed robots.txt data
            
        Raises:
            ScrapingError: If robots.txt cannot be fetched or parsed
        """
        domain = self._get_domain(url)
        
        # Check cache first
        if not force_refresh and domain in self._cache:
            cached_info = self._cache[domain]
            if time.time() - cached_info.last_fetched < self._cache_ttl:
                return cached_info
        
        # Fetch and parse robots.txt
        robots_url = urljoin(f"https://{domain}", "/robots.txt")
        
        try:
            robots_info = self._fetch_and_parse_robots(robots_url)
            self._cache[domain] = robots_info
            return robots_info
            
        except Exception as e:
            # If robots.txt is not accessible, create a permissive default
            robots_info = RobotsTxtInfo(
                url=robots_url,
                content="",
                is_accessible=False,
                last_fetched=time.time()
            )
            self._cache[domain] = robots_info
            return robots_info
    
    def can_fetch(self, url: str, user_agent: str = None) -> bool:
        """
        Check if a URL can be fetched according to robots.txt rules.
        
        Args:
            url: The URL to check
            user_agent: User agent to check for (defaults to instance user_agent)
            
        Returns:
            True if the URL can be fetched, False otherwise
        """
        if user_agent is None:
            user_agent = self.user_agent
            
        try:
            robots_info = self.get_robots_info(url)
            
            # If robots.txt is not accessible, assume permission granted
            if not robots_info.is_accessible:
                return True
            
            # Use urllib's RobotFileParser for standard compliance checking
            import tempfile
            import os
            
            # Create a temporary file with the robots.txt content
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(robots_info.content)
                temp_file = f.name
            
            try:
                rp = RobotFileParser()
                rp.set_url('file://' + temp_file)
                rp.read()
                
                return rp.can_fetch(user_agent, url)
            finally:
                os.unlink(temp_file)
            
        except Exception as e:
            # If there's any error, err on the side of caution
            return False
    
    def get_crawl_delay(self, url: str, user_agent: str = None) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt for a user agent.
        
        Args:
            url: The URL to check
            user_agent: User agent to check for (defaults to instance user_agent)
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        if user_agent is None:
            user_agent = self.user_agent
            
        try:
            robots_info = self.get_robots_info(url)
            
            # Check for user-agent specific crawl delay
            for rule in robots_info.rules:
                if (rule.user_agent.lower() == user_agent.lower() or 
                    rule.user_agent == "*") and rule.directive.lower() == "crawl-delay":
                    try:
                        return float(rule.path)
                    except ValueError:
                        continue
            
            # Return general crawl delay if found
            return robots_info.crawl_delay
            
        except Exception:
            return None
    
    def get_request_rate(self, url: str, user_agent: str = None) -> Optional[str]:
        """
        Get the request rate specified in robots.txt for a user agent.
        
        Args:
            url: The URL to check
            user_agent: User agent to check for (defaults to instance user_agent)
            
        Returns:
            Request rate string (e.g., "1/10s"), or None if not specified
        """
        if user_agent is None:
            user_agent = self.user_agent
            
        try:
            robots_info = self.get_robots_info(url)
            return robots_info.request_rate
        except Exception:
            return None
    
    def get_sitemap_urls(self, url: str) -> List[str]:
        """
        Get sitemap URLs specified in robots.txt.
        
        Args:
            url: The URL to check
            
        Returns:
            List of sitemap URLs
        """
        try:
            robots_info = self.get_robots_info(url)
            return robots_info.sitemap_urls
        except Exception:
            return []
    
    def filter_urls(self, urls: List[str], user_agent: str = None) -> List[str]:
        """
        Filter a list of URLs based on robots.txt rules.
        
        Args:
            urls: List of URLs to filter
            user_agent: User agent to check for (defaults to instance user_agent)
            
        Returns:
            List of URLs that are allowed to be fetched
        """
        if user_agent is None:
            user_agent = self.user_agent
            
        allowed_urls = []
        
        for url in urls:
            if self.can_fetch(url, user_agent):
                allowed_urls.append(url)
                
        return allowed_urls
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _fetch_and_parse_robots(self, robots_url: str) -> RobotsTxtInfo:
        """
        Fetch and parse robots.txt content.
        
        Args:
            robots_url: URL of the robots.txt file
            
        Returns:
            Parsed RobotsTxtInfo object
            
        Raises:
            ScrapingError: If robots.txt cannot be fetched or parsed
        """
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/plain, */*',
            }
            
            response = requests.get(robots_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 404:
                # No robots.txt file - assume everything is allowed
                return RobotsTxtInfo(
                    url=robots_url,
                    content="",
                    is_accessible=False,
                    last_fetched=time.time()
                )
            
            response.raise_for_status()
            content = response.text
            
            # Parse the robots.txt content
            return self._parse_robots_content(robots_url, content)
            
        except requests.RequestException as e:
            raise ScrapingError(
                f"Failed to fetch robots.txt from {robots_url}: {str(e)}",
                "network_error",
                robots_url
            )
    
    def _parse_robots_content(self, robots_url: str, content: str) -> RobotsTxtInfo:
        """
        Parse robots.txt content into structured data.
        
        Args:
            robots_url: URL of the robots.txt file
            content: Raw robots.txt content
            
        Returns:
            Parsed RobotsTxtInfo object
        """
        rules = []
        sitemap_urls = []
        crawl_delay = None
        request_rate = None
        current_user_agent = "*"
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Split on first colon
            if ':' not in line:
                continue
                
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()
            
            if directive == 'user-agent':
                current_user_agent = value
            elif directive in ['allow', 'disallow']:
                rules.append(RobotsTxtRule(
                    user_agent=current_user_agent,
                    directive=directive.title(),
                    path=value
                ))
            elif directive == 'crawl-delay':
                try:
                    # Store crawl-delay as a rule for user-agent specific handling
                    rules.append(RobotsTxtRule(
                        user_agent=current_user_agent,
                        directive="Crawl-delay",
                        path=value
                    ))
                    # Also set the general crawl_delay (last one wins)
                    crawl_delay = float(value)
                except ValueError:
                    pass
            elif directive == 'request-rate':
                request_rate = value
            elif directive == 'sitemap':
                sitemap_urls.append(value)
        
        return RobotsTxtInfo(
            url=robots_url,
            content=content,
            crawl_delay=crawl_delay,
            request_rate=request_rate,
            sitemap_urls=sitemap_urls,
            rules=rules,
            last_fetched=time.time(),
            is_accessible=True
        )