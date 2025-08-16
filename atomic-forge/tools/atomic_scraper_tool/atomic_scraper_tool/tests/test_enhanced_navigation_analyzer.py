"""
Tests for the enhanced navigation analyzer.
"""

import pytest
from bs4 import BeautifulSoup
from atomic_scraper_tool.analysis.enhanced_navigation_analyzer import (
    EnhancedNavigationAnalyzer,
    NavigationHierarchy,
    MegaMenuInfo,
    MobileNavigationInfo,
    AdvancedPaginationInfo,
)


class TestEnhancedNavigationAnalyzer:
    """Test cases for enhanced navigation analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = EnhancedNavigationAnalyzer()

    def test_hierarchical_navigation_detection(self):
        """Test detection of hierarchical navigation structures."""
        html = """
        <nav class="main-nav">
            <ul>
                <li><a href="/home">Home</a></li>
                <li>
                    <a href="/products">Products</a>
                    <ul class="submenu">
                        <li><a href="/products/laptops">Laptops</a></li>
                        <li><a href="/products/phones">Phones</a></li>
                    </ul>
                </li>
                <li><a href="/about">About</a></li>
            </ul>
        </nav>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert len(analysis.main_navigation) > 0
        main_nav = analysis.main_navigation[0]
        assert main_nav.level == 0
        assert len(main_nav.items) == 3
        
        # Check submenu detection
        products_item = next((item for item in main_nav.items if item["text"] == "Products"), None)
        assert products_item is not None
        assert products_item["has_submenu"] is True
        assert len(products_item["submenu_items"]) == 2

    def test_mega_menu_detection(self):
        """Test detection of mega menu structures."""
        html = """
        <nav class="navbar">
            <div class="nav-item dropdown">
                <a href="#" class="nav-link">Categories</a>
                <div class="mega-menu">
                    <div class="col">
                        <h3>Electronics</h3>
                        <a href="/laptops">Laptops</a>
                        <a href="/phones">Phones</a>
                    </div>
                    <div class="col">
                        <h3>Clothing</h3>
                        <a href="/shirts">Shirts</a>
                        <a href="/pants">Pants</a>
                    </div>
                </div>
            </div>
        </nav>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert len(analysis.mega_menus) > 0
        mega_menu = analysis.mega_menus[0]
        assert len(mega_menu.columns) == 2
        assert len(mega_menu.sections) == 2
        assert mega_menu.sections[0]["title"] == "Electronics"

    def test_mobile_navigation_detection(self):
        """Test detection of mobile navigation patterns."""
        html = """
        <header>
            <button class="hamburger menu-toggle">☰</button>
            <nav class="mobile-menu slide-left">
                <ul>
                    <li><a href="/home">Home</a></li>
                    <li><a href="/products">Products</a></li>
                </ul>
            </nav>
            <div class="overlay"></div>
        </header>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert analysis.mobile_navigation is not None
        mobile_nav = analysis.mobile_navigation
        assert mobile_nav.hamburger_selector is not None
        assert mobile_nav.mobile_menu_selector is not None
        assert mobile_nav.overlay_selector is not None
        assert mobile_nav.slide_direction == "left"

    def test_advanced_pagination_detection(self):
        """Test detection of advanced pagination patterns."""
        html = """
        <div class="pagination">
            <a href="?page=1" class="first">First</a>
            <a href="?page=2" class="prev">Previous</a>
            <span class="current">3</span>
            <a href="?page=4" class="next">Next</a>
            <a href="?page=10" class="last">Last</a>
            <select class="per-page">
                <option value="10">10 per page</option>
                <option value="25">25 per page</option>
            </select>
        </div>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert analysis.advanced_pagination is not None
        pagination = analysis.advanced_pagination
        assert pagination.pagination_type == "numbered"
        assert pagination.current_page == 3
        assert pagination.has_page_size_selector is True
        assert pagination.next_selector is not None
        assert pagination.prev_selector is not None

    def test_infinite_scroll_detection(self):
        """Test detection of infinite scroll patterns."""
        html = """
        <div class="content">
            <div class="items">
                <div class="item">Item 1</div>
                <div class="item">Item 2</div>
            </div>
            <div class="infinite-scroll" data-infinite="true">
                Loading more...
            </div>
        </div>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert analysis.advanced_pagination is not None
        pagination = analysis.advanced_pagination
        assert pagination.pagination_type == "infinite_scroll"
        assert pagination.infinite_scroll_trigger is not None

    def test_breadcrumb_variations_detection(self):
        """Test detection of various breadcrumb patterns."""
        html = """
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                <li><a href="/">Home</a></li>
                <li><a href="/category">Category</a></li>
                <li class="active">Current Page</li>
            </ol>
        </nav>
        <div itemtype="http://schema.org/BreadcrumbList">
            <span itemtype="http://schema.org/ListItem">
                <a href="/" itemprop="item">Home</a>
            </span>
        </div>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert len(analysis.breadcrumb_variations) >= 2
        assert any("breadcrumb" in selector for selector in analysis.breadcrumb_variations)
        assert any("BreadcrumbList" in selector for selector in analysis.breadcrumb_variations)

    def test_search_navigation_detection(self):
        """Test detection of search navigation elements."""
        html = """
        <form role="search" class="search-form">
            <input type="search" name="q" placeholder="Search products...">
            <button type="submit" class="search-button">Search</button>
            <div class="search-suggestions" style="display:none;">
                <div class="suggestion">Suggestion 1</div>
            </div>
        </form>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert "search_form" in analysis.search_navigation
        assert "search_input" in analysis.search_navigation
        assert "search_button" in analysis.search_navigation
        assert "suggestions" in analysis.search_navigation

    def test_filter_navigation_detection(self):
        """Test detection of filter and sorting navigation."""
        html = """
        <div class="filters">
            <div class="filter-group">
                <h3>Price</h3>
                <input type="range" name="price_min" class="price-filter">
            </div>
            <select name="sort_by" class="sort-select">
                <option value="price">Price</option>
                <option value="name">Name</option>
            </select>
            <div class="view-toggles">
                <button data-view="grid" class="view-grid">Grid</button>
                <button data-view="list" class="view-list">List</button>
            </div>
        </div>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert "filter_containers" in analysis.filter_navigation
        assert "sort_selectors" in analysis.filter_navigation
        assert "view_toggles" in analysis.filter_navigation
        assert "price_filters" in analysis.filter_navigation

    def test_dynamic_content_detection(self):
        """Test detection of dynamic content indicators."""
        html = """
        <div>
            <button data-toggle="modal" data-target="#myModal">Open Modal</button>
            <div class="loading-spinner" style="display:none;">Loading...</div>
            <img data-src="image.jpg" class="lazy-load" alt="Lazy loaded image">
            <div onclick="loadMore()" class="js-load-more">Load More</div>
        </div>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert len(analysis.dynamic_content_indicators) > 0
        indicators = " ".join(analysis.dynamic_content_indicators)
        assert "data-toggle" in indicators or "loading" in indicators or "lazy" in indicators

    def test_accessibility_features_detection(self):
        """Test detection of accessibility features."""
        html = """
        <nav role="navigation" aria-label="Main navigation">
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <ul>
                <li><a href="/" tabindex="0" aria-label="Home page">Home</a></li>
                <li><a href="/about" tabindex="0">About</a></li>
            </ul>
        </nav>
        <main id="main-content">Content here</main>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        accessibility = analysis.accessibility_features
        assert accessibility["has_skip_links"] is True
        assert accessibility["has_aria_labels"] is True
        assert accessibility["has_role_attributes"] is True
        assert accessibility["has_keyboard_navigation"] is True

    def test_contextual_navigation_detection(self):
        """Test detection of contextual navigation elements."""
        html = """
        <article>
            <div class="tags">
                <a href="/tag/python" class="tag">Python</a>
                <a href="/tag/web" class="tag">Web Development</a>
            </div>
            <div class="categories">
                <a href="/category/programming">Programming</a>
            </div>
            <div class="social-share">
                <a href="#" class="share-twitter">Twitter</a>
                <a href="#" class="share-facebook">Facebook</a>
            </div>
            <div class="author-info">
                <a href="/author/john" class="author-link">John Doe</a>
            </div>
            <div class="related-posts">
                <h3>Related Articles</h3>
                <a href="/related-1">Related Article 1</a>
                <a href="/related-2">Related Article 2</a>
            </div>
        </article>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert analysis.contextual_navigation is not None
        contextual = analysis.contextual_navigation
        assert contextual.tags_selector is not None
        assert contextual.categories_selector is not None
        assert len(contextual.social_sharing) > 0
        assert len(contextual.author_links) > 0
        assert len(contextual.related_links) > 0

    def test_empty_html_handling(self):
        """Test handling of empty or minimal HTML."""
        html = "<html><body></body></html>"
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert analysis.url == "https://example.com"
        assert len(analysis.main_navigation) == 0
        assert len(analysis.mega_menus) == 0
        assert analysis.mobile_navigation is None
        assert analysis.advanced_pagination is None

    def test_complex_nested_navigation(self):
        """Test handling of complex nested navigation structures."""
        html = """
        <nav class="primary-nav">
            <ul>
                <li>
                    <a href="/products">Products</a>
                    <ul class="dropdown">
                        <li>
                            <a href="/electronics">Electronics</a>
                            <ul class="sub-dropdown">
                                <li><a href="/laptops">Laptops</a></li>
                                <li><a href="/phones">Phones</a></li>
                            </ul>
                        </li>
                        <li><a href="/clothing">Clothing</a></li>
                    </ul>
                </li>
            </ul>
        </nav>
        """
        
        analysis = self.analyzer.analyze_navigation(html, "https://example.com")
        
        assert len(analysis.main_navigation) > 0
        main_nav = analysis.main_navigation[0]
        products_item = main_nav.items[0]
        
        assert products_item["has_submenu"] is True
        assert len(products_item["submenu_items"]) == 2
        
        # Check for nested submenu
        electronics_item = products_item["submenu_items"][0]
        assert electronics_item["has_submenu"] is True
        assert len(electronics_item["submenu_items"]) == 2
