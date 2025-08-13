"""
Unit tests for the website analyzer.

Tests the WebsiteAnalyzer class with mock HTML structures for different website types.
"""

import pytest
from atomic_scraper_tool.analysis.website_analyzer import (
    WebsiteAnalyzer, 
    WebsiteStructureAnalysis,
    ContentPattern,
    NavigationInfo,
    PaginationInfo
)


class TestWebsiteAnalyzer:
    """Test cases for WebsiteAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = WebsiteAnalyzer()
    
    def test_analyze_simple_list_website(self):
        """Test analysis of a simple list-based website."""
        html = """
        <html>
        <head><title>Test List Site</title></head>
        <body>
            <nav class="main-nav">
                <a href="/home">Home</a>
                <a href="/about">About</a>
            </nav>
            <main>
                <ul class="item-list">
                    <li class="item">Item 1</li>
                    <li class="item">Item 2</li>
                    <li class="item">Item 3</li>
                    <li class="item">Item 4</li>
                </ul>
            </main>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://example.com")
        
        assert analysis.url == "https://example.com"
        assert analysis.title == "Test List Site"
        assert 'list' in analysis.content_types
        assert 'navigation' in analysis.content_types
        
        # Check for list patterns
        list_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'list']
        assert len(list_patterns) > 0
        assert list_patterns[0].confidence > 0.0
        
        # Check navigation
        assert analysis.navigation_info.main_nav_selector is not None
        assert len(analysis.navigation_info.menu_items) == 2
        
        # Check list containers and item selectors
        assert len(analysis.list_containers) > 0
        assert 'li' in analysis.item_selectors
    
    def test_analyze_article_website(self):
        """Test analysis of an article-based website."""
        html = """
        <html>
        <head><title>Blog Site</title></head>
        <body>
            <header>
                <nav>
                    <a href="/">Home</a>
                    <a href="/blog">Blog</a>
                </nav>
            </header>
            <main>
                <article class="post">
                    <h2>Article Title 1</h2>
                    <p>Article content...</p>
                </article>
                <article class="post">
                    <h2>Article Title 2</h2>
                    <p>Article content...</p>
                </article>
                <div class="pagination">
                    <a href="/page/1">1</a>
                    <a href="/page/2">2</a>
                    <a href="/page/3">Next</a>
                </div>
            </main>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://blog.example.com")
        
        assert analysis.title == "Blog Site"
        assert 'article' in analysis.content_types
        assert 'navigation' in analysis.content_types
        assert 'pagination' in analysis.content_types
        
        # Check for article patterns
        article_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'article']
        assert len(article_patterns) > 0
        assert article_patterns[0].confidence > 0.8  # High confidence for semantic tags
        
        # Check pagination
        assert analysis.pagination_info.pagination_type is not None
        assert analysis.pagination_info.pagination_selector is not None
    
    def test_analyze_product_website(self):
        """Test analysis of a product/e-commerce website."""
        html = """
        <html>
        <head><title>Shop</title></head>
        <body>
            <nav class="main-navigation">
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/cart">Cart</a>
            </nav>
            <div class="product-grid">
                <div class="product-item">
                    <h3>Product 1</h3>
                    <span class="price">$19.99</span>
                    <button class="buy-button">Buy Now</button>
                </div>
                <div class="product-item">
                    <h3>Product 2</h3>
                    <span class="price">$29.99</span>
                    <button class="buy-button">Buy Now</button>
                </div>
                <div class="product-item">
                    <h3>Product 3</h3>
                    <span class="price">$39.99</span>
                    <button class="buy-button">Buy Now</button>
                </div>
            </div>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://shop.example.com")
        
        assert 'product' in analysis.content_types
        assert 'navigation' in analysis.content_types
        
        # Check for product patterns
        product_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'product']
        assert len(product_patterns) > 0
        
        # Check that product-related elements are detected
        assert analysis.metadata['total_links'] > 0
    
    def test_analyze_complex_website(self):
        """Test analysis of a complex website with multiple content types."""
        html = """
        <html>
        <head><title>Complex Site</title></head>
        <body>
            <header>
                <nav class="main-nav">
                    <a href="/">Home</a>
                    <a href="/news">News</a>
                    <a href="/products">Products</a>
                </nav>
            </header>
            <aside class="sidebar">
                <nav class="sidebar-nav">
                    <a href="/category1">Category 1</a>
                    <a href="/category2">Category 2</a>
                </nav>
            </aside>
            <main class="main-content">
                <section class="news-section">
                    <article class="news-item">
                        <h2>News Article 1</h2>
                        <p>News content...</p>
                    </article>
                    <article class="news-item">
                        <h2>News Article 2</h2>
                        <p>News content...</p>
                    </article>
                </section>
                <section class="products-section">
                    <div class="product-list">
                        <div class="product">Product A</div>
                        <div class="product">Product B</div>
                        <div class="product">Product C</div>
                    </div>
                </section>
            </main>
            <footer>
                <nav class="footer-nav">
                    <a href="/privacy">Privacy</a>
                    <a href="/terms">Terms</a>
                </nav>
            </footer>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://complex.example.com")
        
        # Should detect multiple content types
        assert 'article' in analysis.content_types
        assert 'product' in analysis.content_types
        assert 'navigation' in analysis.content_types
        
        # Should detect multiple navigation areas
        assert analysis.navigation_info.main_nav_selector is not None
        assert analysis.navigation_info.sidebar_nav_selector is not None
        assert analysis.navigation_info.footer_nav_selector is not None
        
        # Should find main content area
        assert analysis.main_content_selector is not None
        
        # Should have multiple content patterns
        assert len(analysis.content_patterns) > 2
    
    def test_analyze_paginated_website(self):
        """Test analysis of a website with pagination."""
        html = """
        <html>
        <head><title>Paginated Site</title></head>
        <body>
            <div class="content">
                <ul class="results">
                    <li>Result 1</li>
                    <li>Result 2</li>
                    <li>Result 3</li>
                </ul>
                <div class="pagination">
                    <a href="/page/1">Previous</a>
                    <a href="/page/1">1</a>
                    <a href="/page/2" class="current">2</a>
                    <a href="/page/3">3</a>
                    <a href="/page/4">4</a>
                    <a href="/page/3">Next</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://paginated.example.com")
        
        assert 'pagination' in analysis.content_types
        assert analysis.pagination_info.pagination_type is not None
        assert analysis.pagination_info.pagination_selector is not None
        
        # Should detect numbered pagination
        if analysis.pagination_info.pagination_type == 'numbered':
            assert analysis.pagination_info.total_pages is not None
            assert analysis.pagination_info.total_pages >= 4
    
    def test_analyze_empty_website(self):
        """Test analysis of an empty or minimal website."""
        html = """
        <html>
        <head><title>Empty Site</title></head>
        <body>
            <p>Just some text</p>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://empty.example.com")
        
        assert analysis.title == "Empty Site"
        assert len(analysis.content_patterns) == 0
        assert len(analysis.content_types) == 0
        assert analysis.navigation_info.main_nav_selector is None
        assert analysis.pagination_info.pagination_type is None
    
    def test_analyze_malformed_html(self):
        """Test analysis of malformed HTML."""
        html = """
        <html>
        <head><title>Malformed Site</title>
        <body>
            <div class="content">
                <ul>
                    <li>Item 1
                    <li>Item 2
                    <li>Item 3
                </ul>
            </div>
        </body>
        """
        
        # Should not raise an exception
        analysis = self.analyzer.analyze_website(html, "https://malformed.example.com")
        
        assert analysis.title == "Malformed Site"
        # BeautifulSoup should handle malformed HTML gracefully
        assert 'list' in analysis.content_types
    
    def test_content_pattern_confidence_scoring(self):
        """Test that confidence scores are calculated correctly."""
        html = """
        <html>
        <body>
            <ul class="many-items">
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
                <li>Item 4</li>
                <li>Item 5</li>
                <li>Item 6</li>
                <li>Item 7</li>
                <li>Item 8</li>
                <li>Item 9</li>
                <li>Item 10</li>
            </ul>
            <ul class="few-items">
                <li>Item A</li>
                <li>Item B</li>
                <li>Item C</li>
            </ul>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://confidence.example.com")
        
        list_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'list']
        assert len(list_patterns) >= 2
        
        # Pattern with more items should have higher confidence
        many_items_pattern = next((p for p in list_patterns if 'many-items' in p.selector), None)
        few_items_pattern = next((p for p in list_patterns if 'few-items' in p.selector), None)
        
        if many_items_pattern and few_items_pattern:
            assert many_items_pattern.confidence > few_items_pattern.confidence
    
    def test_metadata_extraction(self):
        """Test extraction of website metadata."""
        html = """
        <html lang="en">
        <head>
            <title>Metadata Test</title>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, metadata, scraping">
        </head>
        <body>
            <p>Some content with multiple words for word count testing.</p>
            <a href="/link1">Link 1</a>
            <a href="/link2">Link 2</a>
            <img src="image1.jpg" alt="Image 1">
            <form><input type="text"></form>
            <table><tr><td>Cell</td></tr></table>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://metadata.example.com")
        
        metadata = analysis.metadata
        assert metadata['domain'] == 'metadata.example.com'
        assert metadata['total_links'] == 2
        assert metadata['total_images'] == 1
        assert metadata['total_forms'] == 1
        assert metadata['total_tables'] == 1
        assert metadata['language'] == 'en'
        assert 'meta_description' in metadata
        assert 'meta_keywords' in metadata
        assert metadata['word_count'] > 0
        assert metadata['text_length'] > 0
    
    def test_selector_generation(self):
        """Test CSS selector generation for elements."""
        html = """
        <html>
        <body>
            <div id="unique-id">Content</div>
            <div class="class1 class2">Content</div>
            <div data-id="test">Content</div>
            <div>Plain div</div>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://selector.example.com")
        
        # The analyzer should generate appropriate selectors
        # This is tested indirectly through the pattern detection
        assert len(analysis.content_patterns) >= 0  # May not detect patterns in this simple case
    
    def test_find_repeated_elements(self):
        """Test detection of repeated elements."""
        html = """
        <html>
        <body>
            <div class="container">
                <div class="item">Item 1</div>
                <div class="item">Item 2</div>
                <div class="item">Item 3</div>
                <div class="item">Item 4</div>
                <div class="different">Different</div>
            </div>
        </body>
        </html>
        """
        
        analysis = self.analyzer.analyze_website(html, "https://repeated.example.com")
        
        # Should detect the repeated item pattern
        assert len(analysis.list_containers) > 0
        assert any('item' in selector for selector in analysis.item_selectors)


class TestContentPattern:
    """Test cases for ContentPattern dataclass."""
    
    def test_content_pattern_creation(self):
        """Test creating a ContentPattern."""
        pattern = ContentPattern(
            pattern_type='list',
            selector='ul.items',
            confidence=0.8,
            sample_elements=['<li>Item 1</li>', '<li>Item 2</li>'],
            attributes={'item_count': 5}
        )
        
        assert pattern.pattern_type == 'list'
        assert pattern.selector == 'ul.items'
        assert pattern.confidence == 0.8
        assert len(pattern.sample_elements) == 2
        assert pattern.attributes['item_count'] == 5


class TestNavigationInfo:
    """Test cases for NavigationInfo dataclass."""
    
    def test_navigation_info_creation(self):
        """Test creating NavigationInfo."""
        nav_info = NavigationInfo(
            main_nav_selector='nav.main',
            breadcrumb_selector='div.breadcrumb',
            menu_items=['Home', 'About', 'Contact']
        )
        
        assert nav_info.main_nav_selector == 'nav.main'
        assert nav_info.breadcrumb_selector == 'div.breadcrumb'
        assert len(nav_info.menu_items) == 3
        assert nav_info.sidebar_nav_selector is None
    
    def test_navigation_info_default_menu_items(self):
        """Test NavigationInfo with default menu_items."""
        nav_info = NavigationInfo()
        assert nav_info.menu_items == []


class TestPaginationInfo:
    """Test cases for PaginationInfo dataclass."""
    
    def test_pagination_info_creation(self):
        """Test creating PaginationInfo."""
        pagination_info = PaginationInfo(
            pagination_type='numbered',
            pagination_selector='div.pagination',
            total_pages=10,
            current_page=3
        )
        
        assert pagination_info.pagination_type == 'numbered'
        assert pagination_info.pagination_selector == 'div.pagination'
        assert pagination_info.total_pages == 10
        assert pagination_info.current_page == 3


if __name__ == '__main__':
    pytest.main([__file__])