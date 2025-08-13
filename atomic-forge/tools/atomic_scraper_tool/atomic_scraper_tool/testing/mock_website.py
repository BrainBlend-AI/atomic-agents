"""
Mock website generator for testing scraping functionality.

This module provides comprehensive mock website generation capabilities
for testing various scraping scenarios without relying on external websites.
"""

import random
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field


class WebsiteType(str, Enum):
    """Types of websites that can be generated."""
    ECOMMERCE = "ecommerce"
    NEWS = "news"
    BLOG = "blog"
    DIRECTORY = "directory"
    PORTFOLIO = "portfolio"
    DOCUMENTATION = "documentation"
    FORUM = "forum"
    SOCIAL = "social"


class MockWebsiteConfig(BaseModel):
    """Configuration for mock website generation."""
    website_type: WebsiteType
    base_url: str = "https://example.com"
    num_pages: int = 10
    items_per_page: int = 20
    include_pagination: bool = True
    include_navigation: bool = True
    include_errors: bool = False
    error_rate: float = 0.1
    include_malformed_html: bool = False
    malformed_rate: float = 0.05
    include_dynamic_content: bool = False
    language: str = "en"
    include_metadata: bool = True


class MockWebsite:
    """Mock website generator for testing scraping functionality."""
    
    def __init__(self, config: MockWebsiteConfig):
        self.config = config
        self._pages_cache: Dict[str, str] = {}
        self._setup_generators()
    
    def _setup_generators(self):
        """Set up content generators based on website type."""
        self.generators = {
            WebsiteType.ECOMMERCE: self._generate_ecommerce_content,
            WebsiteType.NEWS: self._generate_news_content,
            WebsiteType.BLOG: self._generate_blog_content,
            WebsiteType.DIRECTORY: self._generate_directory_content,
            WebsiteType.PORTFOLIO: self._generate_portfolio_content,
            WebsiteType.DOCUMENTATION: self._generate_documentation_content,
            WebsiteType.FORUM: self._generate_forum_content,
            WebsiteType.SOCIAL: self._generate_social_content
        }
    
    def generate_page(self, path: str = "/") -> str:
        """Generate HTML content for a specific page."""
        if path in self._pages_cache:
            return self._pages_cache[path]
        
        # Determine page type and content
        if path == "/" or path == "/index.html":
            html = self._generate_homepage()
        elif path.startswith("/page/"):
            page_num = self._extract_page_number(path)
            html = self._generate_listing_page(page_num)
        elif path.startswith("/item/") or path.startswith("/product/"):
            item_id = self._extract_item_id(path)
            html = self._generate_item_page(item_id)
        elif path.startswith("/category/"):
            category = self._extract_category(path)
            html = self._generate_category_page(category)
        else:
            html = self._generate_generic_page(path)
        
        # Apply error simulation if enabled
        if self.config.include_errors and random.random() < self.config.error_rate:
            html = self._simulate_error(html)
        
        # Apply malformed HTML if enabled
        if self.config.include_malformed_html and random.random() < self.config.malformed_rate:
            html = self._introduce_malformed_html(html)
        
        self._pages_cache[path] = html
        return html
    
    def _generate_homepage(self) -> str:
        """Generate homepage HTML."""
        generator = self.generators[self.config.website_type]
        content = generator("homepage")
        
        return self._wrap_in_html_template(
            title=f"Homepage - {self.config.website_type.title()} Site",
            content=content,
            include_navigation=True
        )
    
    def _generate_listing_page(self, page_num: int) -> str:
        """Generate a listing page with multiple items."""
        generator = self.generators[self.config.website_type]
        
        # Generate items for this page
        items_html = []
        start_item = (page_num - 1) * self.config.items_per_page + 1
        end_item = start_item + self.config.items_per_page
        
        for item_id in range(start_item, end_item):
            if self.config.website_type == WebsiteType.ECOMMERCE:
                items_html.append(self._generate_product_card(item_id))
            elif self.config.website_type == WebsiteType.NEWS:
                items_html.append(self._generate_article_card(item_id))
            elif self.config.website_type == WebsiteType.BLOG:
                items_html.append(self._generate_blog_card(item_id))
            else:
                items_html.append(self._generate_generic_card(item_id))
        
        # Generate pagination
        pagination_html = self._generate_pagination(page_num) if self.config.include_pagination else ""
        
        content = f"""
        <div class="listing-page">
            <h1>Page {page_num}</h1>
            <div class="items-grid">
                {''.join(items_html)}
            </div>
            {pagination_html}
        </div>
        """
        
        return self._wrap_in_html_template(
            title=f"Page {page_num} - {self.config.website_type.title()} Site",
            content=content,
            include_navigation=True
        )
    
    def _generate_item_page(self, item_id: str) -> str:
        """Generate a detailed item page."""
        if self.config.website_type == WebsiteType.ECOMMERCE:
            content = self._generate_product_detail(item_id)
        elif self.config.website_type == WebsiteType.NEWS:
            content = self._generate_article_detail(item_id)
        elif self.config.website_type == WebsiteType.BLOG:
            content = self._generate_blog_detail(item_id)
        else:
            content = self._generate_generic_detail(item_id)
        
        return self._wrap_in_html_template(
            title=f"Item {item_id} - {self.config.website_type.title()} Site",
            content=content,
            include_navigation=True
        )
    
    def _generate_category_page(self, category: str) -> str:
        """Generate a category page."""
        content = f"""
        <div class="category-page">
            <h1>Category: {category.title()}</h1>
            <div class="category-items">
                <div class="item-card">
                    <h3><a href="/item/1">Sample Item in {category}</a></h3>
                    <p>Description of item in {category} category</p>
                </div>
            </div>
        </div>
        """
        
        return self._wrap_in_html_template(
            title=f"{category.title()} - {self.config.website_type.title()} Site",
            content=content,
            include_navigation=True
        )
    
    def _generate_generic_page(self, path: str) -> str:
        """Generate a generic page for unknown paths."""
        content = f"""
        <div class="generic-page">
            <h1>Page: {path}</h1>
            <p>This is a generic page for path: {path}</p>
        </div>
        """
        
        return self._wrap_in_html_template(
            title=f"Page {path} - {self.config.website_type.title()} Site",
            content=content,
            include_navigation=True
        )
    
    def _generate_ecommerce_content(self, page_type: str, **kwargs) -> str:
        """Generate e-commerce website content."""
        if page_type == "homepage":
            return """
            <div class="homepage">
                <div class="hero-section">
                    <h1>Welcome to Our Store</h1>
                    <p>Find the best products at amazing prices!</p>
                </div>
                <div class="featured-products">
                    <h2>Featured Products</h2>
                    <div class="product-grid">
                        <div class="product-card" data-product-id="1">
                            <img src="/images/product1.jpg" alt="Smartphone X1">
                            <h3><a href="/product/1">Smartphone X1</a></h3>
                            <p class="price">$599.99</p>
                            <p class="rating">★★★★☆ (4.2/5)</p>
                        </div>
                    </div>
                </div>
            </div>
            """
        return "<div>E-commerce content</div>"
    
    def _generate_news_content(self, page_type: str, **kwargs) -> str:
        """Generate news website content."""
        if page_type == "homepage":
            return """
            <div class="news-homepage">
                <div class="breaking-news">
                    <h1>Breaking News</h1>
                    <div class="headline-story">
                        <h2><a href="/article/1">Major Development</a></h2>
                        <p class="summary">Industry leaders announce...</p>
                        <p class="meta">By John Reporter | 2 hours ago</p>
                    </div>
                </div>
                <div class="top-stories">
                    <h2>Top Stories</h2>
                    <div class="story-grid">
                        <article class="story-card">
                            <h3><a href="/article/1">Economic Markets Show Growth</a></h3>
                            <p class="meta">By Jane Smith | 4 hours ago</p>
                        </article>
                    </div>
                </div>
            </div>
            """
        return "<div>News content</div>"
    
    def _generate_blog_content(self, page_type: str, **kwargs) -> str:
        """Generate blog website content."""
        if page_type == "homepage":
            return """
            <div class="blog-homepage">
                <h1>Welcome to My Blog</h1>
                <div class="recent-posts">
                    <article class="post-card">
                        <h3><a href="/post/1">My First Blog Post</a></h3>
                        <p class="excerpt">This is an excerpt...</p>
                    </article>
                </div>
            </div>
            """
        return "<div>Blog content</div>"
    
    def _generate_directory_content(self, page_type: str, **kwargs) -> str:
        """Generate directory website content."""
        if page_type == "homepage":
            return """
            <div class="directory-homepage">
                <h1>Business Directory</h1>
                <div class="listing-grid">
                    <div class="listing-card">
                        <h3><a href="/item/1">Acme Corporation</a></h3>
                        <p class="category">Technology</p>
                    </div>
                </div>
            </div>
            """
        return "<div>Directory content</div>"
    
    def _generate_portfolio_content(self, page_type: str, **kwargs) -> str:
        """Generate portfolio website content."""
        return "<div class='portfolio'>Portfolio content</div>"
    
    def _generate_documentation_content(self, page_type: str, **kwargs) -> str:
        """Generate documentation website content."""
        return "<div class='documentation'>Documentation content</div>"
    
    def _generate_forum_content(self, page_type: str, **kwargs) -> str:
        """Generate forum website content."""
        return "<div class='forum'>Forum content</div>"
    
    def _generate_social_content(self, page_type: str, **kwargs) -> str:
        """Generate social media website content."""
        return "<div class='social'>Social content</div>"
    
    def _generate_product_card(self, item_id: int) -> str:
        """Generate a product card for e-commerce sites."""
        return f"""
        <div class="product-card" data-product-id="{item_id}">
            <img src="/images/product{item_id}.jpg" alt="Product {item_id}">
            <h3><a href="/product/{item_id}">Product {item_id}</a></h3>
            <p class="price">${19.99 + item_id * 10}</p>
            <p class="rating">★★★★☆ ({4.0 + (item_id % 10) / 10:.1f}/5)</p>
            <button class="add-to-cart" data-product-id="{item_id}">Add to Cart</button>
        </div>
        """
    
    def _generate_article_card(self, item_id: int) -> str:
        """Generate an article card for news sites."""
        return f"""
        <article class="story-card" data-article-id="{item_id}">
            <h3><a href="/article/{item_id}">Breaking News Story {item_id}</a></h3>
            <p class="summary">This is a summary of news story {item_id}...</p>
            <p class="meta">By Reporter {item_id} | {item_id} hours ago</p>
        </article>
        """
    
    def _generate_blog_card(self, item_id: int) -> str:
        """Generate a blog post card."""
        return f"""
        <article class="post-card" data-post-id="{item_id}">
            <h3><a href="/post/{item_id}">Blog Post {item_id}</a></h3>
            <p class="excerpt">This is an excerpt from blog post {item_id}...</p>
            <p class="meta">Published {item_id} days ago</p>
        </article>
        """
    
    def _generate_generic_card(self, item_id: int) -> str:
        """Generate a generic item card."""
        return f"""
        <div class="item-card" data-item-id="{item_id}">
            <h3><a href="/item/{item_id}">Item {item_id}</a></h3>
            <p>Description of item {item_id}</p>
        </div>
        """
    
    def _generate_product_detail(self, item_id: str) -> str:
        """Generate detailed product page content."""
        return f"""
        <div class="product-detail" data-product-id="{item_id}">
            <h1>Product {item_id}</h1>
            <div class="product-images">
                <img src="/images/product{item_id}.jpg" alt="Product {item_id}" class="main-image">
                <div class="thumbnail-gallery">
                    <img src="/images/product{item_id}_thumb1.jpg" alt="Product {item_id} view 1">
                    <img src="/images/product{item_id}_thumb2.jpg" alt="Product {item_id} view 2">
                </div>
            </div>
            <div class="product-info">
                <div class="details">
                    <p class="price">${19.99 + int(item_id) * 10}</p>
                    <p class="rating">★★★★☆ ({4.0 + (int(item_id) % 10) / 10:.1f}/5)</p>
                    <p class="description">Detailed description of product {item_id}...</p>
                    <button class="add-to-cart" data-product-id="{item_id}">Add to Cart</button>
                </div>
            </div>
            <div class="specifications">
                <h3>Specifications</h3>
                <ul>
                    <li>Brand: Example Brand</li>
                    <li>Model: Product-{item_id}</li>
                    <li>Weight: {1.5 + int(item_id) * 0.1:.1f} lbs</li>
                    <li>Dimensions: {10 + int(item_id)}x{8 + int(item_id)}x{2 + int(item_id)} inches</li>
                </ul>
            </div>
        </div>
        """
    
    def _generate_article_detail(self, item_id: str) -> str:
        """Generate detailed article page content."""
        return f"""
        <article class="article-detail" data-article-id="{item_id}">
            <h1>Breaking News Story {item_id}</h1>
            <p class="meta">By Reporter {item_id} | {item_id} hours ago</p>
            <div class="article-content">
                <p>This is the full content of news story {item_id}...</p>
                <p>More detailed information about the story...</p>
            </div>
        </article>
        """
    
    def _generate_blog_detail(self, item_id: str) -> str:
        """Generate detailed blog post content."""
        return f"""
        <article class="blog-detail" data-post-id="{item_id}">
            <h1>Blog Post {item_id}</h1>
            <p class="meta">Published {item_id} days ago</p>
            <div class="post-content">
                <p>This is the full content of blog post {item_id}...</p>
                <p>More detailed blog content...</p>
            </div>
        </article>
        """
    
    def _generate_generic_detail(self, item_id: str) -> str:
        """Generate generic item detail content."""
        return f"""
        <div class="item-detail" data-item-id="{item_id}">
            <h1>Item {item_id}</h1>
            <div class="item-content">
                <p>Detailed information about item {item_id}...</p>
            </div>
        </div>
        """
    
    def _generate_pagination(self, current_page: int) -> str:
        """Generate pagination HTML."""
        pagination_html = ['<div class="pagination">']
        
        # Previous link
        if current_page > 1:
            pagination_html.append(f'<a href="/page/{current_page - 1}" class="prev">Previous</a>')
        
        # Page numbers
        for page in range(max(1, current_page - 2), min(self.config.num_pages + 1, current_page + 3)):
            if page == current_page:
                pagination_html.append(f'<span class="current">{page}</span>')
            else:
                pagination_html.append(f'<a href="/page/{page}">{page}</a>')
        
        # Next link
        if current_page < self.config.num_pages:
            pagination_html.append(f'<a href="/page/{current_page + 1}" class="next">Next</a>')
        
        pagination_html.append('</div>')
        return ''.join(pagination_html)
    
    def _wrap_in_html_template(self, title: str, content: str, include_navigation: bool = True) -> str:
        """Wrap content in a complete HTML template."""
        navigation_html = ""
        if include_navigation and self.config.include_navigation:
            navigation_html = self._generate_navigation()
        
        metadata_html = ""
        if self.config.include_metadata:
            metadata_html = self._generate_metadata(title)
        
        return f"""<!DOCTYPE html>
<html lang="{self.config.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="Mock website for testing">
    <meta name="keywords" content="test, mock, website, scraping">
    {metadata_html}
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
        .product-card {{ border: 1px solid #ddd; padding: 15px; }}
        .price {{ font-weight: bold; color: #007cba; }}
        .rating {{ color: #ffa500; }}
        .navigation {{ background: #f8f9fa; padding: 10px 0; margin-bottom: 20px; }}
        .navigation ul {{ list-style: none; margin: 0; padding: 0; display: flex; }}
        .navigation li {{ margin-right: 20px; }}
        .navigation a {{ text-decoration: none; color: #333; }}
    </style>
</head>
<body>
    {navigation_html}
    <div class="container">
        {content}
    </div>
</body>
</html>"""
    
    def _generate_navigation(self) -> str:
        """Generate navigation menu HTML."""
        nav_items = []
        if self.config.website_type == WebsiteType.ECOMMERCE:
            nav_items = [
                ('/', 'Home'),
                ('/products', 'Products'),
                ('/categories', 'Categories'),
                ('/about', 'About'),
                ('/contact', 'Contact')
            ]
        elif self.config.website_type == WebsiteType.NEWS:
            nav_items = [
                ('/', 'Home'),
                ('/politics', 'Politics'),
                ('/sports', 'Sports'),
                ('/technology', 'Technology'),
                ('/about', 'About')
            ]
        else:
            nav_items = [
                ('/', 'Home'),
                ('/about', 'About'),
                ('/contact', 'Contact')
            ]
        
        nav_links = []
        for href, text in nav_items:
            nav_links.append(f'<li><a href="{href}">{text}</a></li>')
        
        return f"""
        <nav class="navigation">
            <div class="container">
                <ul>
                    {''.join(nav_links)}
                </ul>
            </div>
        </nav>
        """
    
    def _generate_metadata(self, title: str) -> str:
        """Generate additional metadata tags."""
        return f"""
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="Mock website for testing web scraping">
        <meta property="og:type" content="website">
        <meta name="twitter:card" content="summary">
        <meta name="twitter:title" content="{title}">
        """
    
    def _simulate_error(self, html: str) -> str:
        """Simulate various types of errors in HTML."""
        error_types = ["network_timeout", "server_error", "partial_content"]
        error_type = random.choice(error_types)
        
        if error_type == "server_error":
            return "<html><body><h1>500 Internal Server Error</h1></body></html>"
        elif error_type == "partial_content":
            return html[:len(html)//2]
        else:
            return html[:len(html)//2] + "<!-- Connection timed out -->"
    
    def _introduce_malformed_html(self, html: str) -> str:
        """Introduce malformed HTML for testing error handling."""
        return html.replace("<div>", "<div")  # Missing closing bracket
    
    def _extract_page_number(self, path: str) -> int:
        """Extract page number from URL path."""
        try:
            return int(path.split("/")[-1])
        except (ValueError, IndexError):
            return 1
    
    def _extract_item_id(self, path: str) -> str:
        """Extract item ID from URL path."""
        try:
            parts = path.split("/")
            return parts[-1] if parts[-1] else "1"
        except IndexError:
            return "1"
    
    def _extract_category(self, path: str) -> str:
        """Extract category from URL path."""
        try:
            return path.split("/")[-1]
        except IndexError:
            return "general"
    
    def get_all_urls(self) -> List[str]:
        """Get all available URLs for this mock website."""
        urls = ["/"]
        
        # Add pagination URLs
        for page in range(1, self.config.num_pages + 1):
            urls.append(f"/page/{page}")
        
        # Add item URLs
        for item_id in range(1, min(self.config.items_per_page, 5) + 1):
            if self.config.website_type == WebsiteType.ECOMMERCE:
                urls.append(f"/product/{item_id}")
            elif self.config.website_type == WebsiteType.NEWS:
                urls.append(f"/article/{item_id}")
            elif self.config.website_type == WebsiteType.BLOG:
                urls.append(f"/post/{item_id}")
            else:
                urls.append(f"/item/{item_id}")
        
        # Add category URLs
        categories = ["electronics", "clothing"]
        for category in categories:
            urls.append(f"/category/{category}")
        
        return urls


class MockWebsiteGenerator:
    """Factory class for generating different types of mock websites."""
    
    @staticmethod
    def create_ecommerce_site(num_products: int = 50, include_errors: bool = False) -> MockWebsite:
        """Create a mock e-commerce website."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.ECOMMERCE,
            num_pages=max(1, (num_products + 19) // 20),
            items_per_page=20,
            include_errors=include_errors,
            include_pagination=True,
            include_navigation=True
        )
        return MockWebsite(config)
    
    @staticmethod
    def create_news_site(num_articles: int = 30, include_errors: bool = False) -> MockWebsite:
        """Create a mock news website."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.NEWS,
            num_pages=max(1, (num_articles + 14) // 15),
            items_per_page=15,
            include_errors=include_errors,
            include_pagination=True,
            include_navigation=True
        )
        return MockWebsite(config)
    
    @staticmethod
    def create_blog_site(num_posts: int = 25, include_errors: bool = False) -> MockWebsite:
        """Create a mock blog website."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.BLOG,
            num_pages=max(1, (num_posts + 9) // 10),
            items_per_page=10,
            include_errors=include_errors,
            include_pagination=True,
            include_navigation=True
        )
        return MockWebsite(config)
    
    @staticmethod
    def create_directory_site(num_entries: int = 100, include_errors: bool = False) -> MockWebsite:
        """Create a mock directory website."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.DIRECTORY,
            num_pages=max(1, (num_entries + 24) // 25),
            items_per_page=25,
            include_errors=include_errors,
            include_pagination=True,
            include_navigation=True
        )
        return MockWebsite(config)
    
    @staticmethod
    def create_problematic_site() -> MockWebsite:
        """Create a mock website with various problems for testing error handling."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.ECOMMERCE,
            num_pages=5,
            items_per_page=10,
            include_errors=True,
            error_rate=0.3,
            include_malformed_html=True,
            malformed_rate=0.2,
            include_navigation=True
        )
        return MockWebsite(config)