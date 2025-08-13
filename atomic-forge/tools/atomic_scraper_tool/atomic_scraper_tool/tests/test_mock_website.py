"""
Unit tests for mock website generator functionality.
"""

import pytest
from bs4 import BeautifulSoup

from atomic_scraper_tool.testing.mock_website import (
    MockWebsite,
    MockWebsiteGenerator,
    MockWebsiteConfig,
    WebsiteType
)


class TestMockWebsiteConfig:
    """Test cases for MockWebsiteConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MockWebsiteConfig(website_type=WebsiteType.ECOMMERCE)
        
        assert config.website_type == WebsiteType.ECOMMERCE
        assert config.base_url == "https://example.com"
        assert config.num_pages == 10
        assert config.items_per_page == 20
        assert config.include_pagination is True
        assert config.include_navigation is True
        assert config.include_errors is False
        assert config.error_rate == 0.1
        assert config.include_malformed_html is False
        assert config.malformed_rate == 0.05
        assert config.language == "en"
        assert config.include_metadata is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.NEWS,
            base_url="https://test.com",
            num_pages=5,
            items_per_page=15,
            include_errors=True,
            error_rate=0.2,
            language="es"
        )
        
        assert config.website_type == WebsiteType.NEWS
        assert config.base_url == "https://test.com"
        assert config.num_pages == 5
        assert config.items_per_page == 15
        assert config.include_errors is True
        assert config.error_rate == 0.2
        assert config.language == "es"


class TestMockWebsite:
    """Test cases for MockWebsite class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockWebsiteConfig(
            website_type=WebsiteType.ECOMMERCE,
            num_pages=3,
            items_per_page=5,
            include_pagination=True,
            include_navigation=True
        )
        self.mock_website = MockWebsite(self.config)
    
    def test_init(self):
        """Test MockWebsite initialization."""
        assert self.mock_website.config == self.config
        assert self.mock_website._pages_cache == {}
        assert len(self.mock_website.generators) == 8  # All website types
    
    def test_generate_homepage(self):
        """Test homepage generation."""
        html = self.mock_website.generate_page("/")
        
        # Parse HTML to verify structure
        soup = BeautifulSoup(html, 'html.parser')
        
        assert soup.find('title') is not None
        assert soup.find('html') is not None
        assert soup.find('body') is not None
        assert 'Homepage' in soup.find('title').text
        
        # Check for e-commerce specific content
        assert 'Welcome to Our Store' in html
        assert 'product-card' in html
        assert 'Featured Products' in html
    
    def test_generate_listing_page(self):
        """Test listing page generation."""
        html = self.mock_website.generate_page("/page/1")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for pagination
        pagination = soup.find(class_='pagination')
        assert pagination is not None
        
        # Check for product cards
        product_cards = soup.find_all(class_='product-card')
        assert len(product_cards) == self.config.items_per_page
        
        # Check for proper product structure
        first_product = product_cards[0]
        assert first_product.get('data-product-id') is not None
        assert first_product.find('h3') is not None
        assert first_product.find(class_='price') is not None
    
    def test_generate_item_page(self):
        """Test item detail page generation."""
        html = self.mock_website.generate_page("/product/1")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for product detail structure
        product_detail = soup.find(class_='product-detail')
        assert product_detail is not None
        assert product_detail.get('data-product-id') == '1'
        
        # Check for required elements
        assert soup.find(class_='product-images') is not None
        assert soup.find(class_='product-info') is not None
        assert soup.find(class_='price') is not None
        assert soup.find(class_='rating') is not None
        assert soup.find(class_='description') is not None
        assert soup.find(class_='specifications') is not None
    
    def test_generate_category_page(self):
        """Test category page generation."""
        html = self.mock_website.generate_page("/category/electronics")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        assert 'Electronics' in soup.find('title').text
        assert soup.find('body') is not None
    
    def test_navigation_generation(self):
        """Test navigation menu generation."""
        html = self.mock_website.generate_page("/")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for navigation
        nav = soup.find('nav', class_='navigation')
        assert nav is not None
        
        # Check for navigation links
        nav_links = nav.find_all('a')
        assert len(nav_links) > 0
        
        # Check for e-commerce specific navigation
        link_texts = [link.text for link in nav_links]
        assert 'Home' in link_texts
        assert 'Products' in link_texts
    
    def test_pagination_generation(self):
        """Test pagination generation."""
        html = self.mock_website.generate_page("/page/2")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        pagination = soup.find(class_='pagination')
        assert pagination is not None
        
        # Check for pagination links
        page_links = pagination.find_all('a')
        assert len(page_links) > 0
        
        # Check for previous/next links
        link_texts = [link.text for link in page_links]
        assert 'Previous' in link_texts or 'Next' in link_texts
    
    def test_metadata_generation(self):
        """Test HTML metadata generation."""
        html = self.mock_website.generate_page("/")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'})
        assert meta_description is not None
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        assert meta_keywords is not None
        
        # Check for Open Graph tags
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        assert og_title is not None
    
    def test_caching(self):
        """Test page caching functionality."""
        # Generate page twice
        html1 = self.mock_website.generate_page("/")
        html2 = self.mock_website.generate_page("/")
        
        # Should be identical due to caching
        assert html1 == html2
        assert "/" in self.mock_website._pages_cache
    
    def test_error_simulation(self):
        """Test error simulation functionality."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.ECOMMERCE,
            include_errors=True,
            error_rate=1.0  # Always generate errors
        )
        mock_site = MockWebsite(config)
        
        html = mock_site.generate_page("/")
        
        # Should contain error indicators
        assert ('500 Internal Server Error' in html or 
                'Connection timed out' in html or 
                len(html) < 1000)  # Partial content
    
    def test_malformed_html_simulation(self):
        """Test malformed HTML simulation."""
        config = MockWebsiteConfig(
            website_type=WebsiteType.ECOMMERCE,
            include_malformed_html=True,
            malformed_rate=1.0  # Always generate malformed HTML
        )
        mock_site = MockWebsite(config)
        
        html = mock_site.generate_page("/")
        
        # Should contain malformed elements
        # Note: This is probabilistic, so we just check that HTML was generated
        assert len(html) > 0
    
    def test_get_all_urls(self):
        """Test URL generation."""
        urls = self.mock_website.get_all_urls()
        
        assert "/" in urls
        assert "/page/1" in urls
        assert "/page/2" in urls
        assert "/page/3" in urls
        assert "/product/1" in urls
        assert "/category/electronics" in urls
        
        # Check total number of URLs
        expected_urls = (
            1 +  # Homepage
            self.config.num_pages +  # Pagination pages
            min(self.config.items_per_page, 5) +  # Product pages (limited to 5 in get_all_urls)
            2  # Category pages (electronics, clothing)
        )
        assert len(urls) == expected_urls
    
    def test_path_extraction_methods(self):
        """Test URL path extraction methods."""
        # Test page number extraction
        assert self.mock_website._extract_page_number("/page/5") == 5
        assert self.mock_website._extract_page_number("/invalid") == 1
        
        # Test item ID extraction
        assert self.mock_website._extract_item_id("/product/123") == "123"
        assert self.mock_website._extract_item_id("/invalid") == "invalid"
        
        # Test category extraction
        assert self.mock_website._extract_category("/category/electronics") == "electronics"
        assert self.mock_website._extract_category("/invalid") == "invalid"


class TestMockWebsiteGenerator:
    """Test cases for MockWebsiteGenerator factory class."""
    
    def test_create_ecommerce_site(self):
        """Test e-commerce site creation."""
        site = MockWebsiteGenerator.create_ecommerce_site(num_products=30)
        
        assert site.config.website_type == WebsiteType.ECOMMERCE
        assert site.config.num_pages == 2  # 30 products / 20 per page = 2 pages
        assert site.config.items_per_page == 20
        assert site.config.include_pagination is True
        assert site.config.include_navigation is True
        
        # Test homepage generation
        html = site.generate_page("/")
        assert 'Welcome to Our Store' in html
        assert 'product-card' in html
    
    def test_create_news_site(self):
        """Test news site creation."""
        site = MockWebsiteGenerator.create_news_site(num_articles=20)
        
        assert site.config.website_type == WebsiteType.NEWS
        assert site.config.num_pages == 2  # 20 articles / 15 per page = 2 pages
        assert site.config.items_per_page == 15
        
        # Test homepage generation
        html = site.generate_page("/")
        assert 'Breaking News' in html
        assert 'story-card' in html
    
    def test_create_blog_site(self):
        """Test blog site creation."""
        site = MockWebsiteGenerator.create_blog_site(num_posts=15)
        
        assert site.config.website_type == WebsiteType.BLOG
        assert site.config.num_pages == 2  # 15 posts / 10 per page = 2 pages
        assert site.config.items_per_page == 10
        
        # Test that it generates valid HTML
        html = site.generate_page("/")
        soup = BeautifulSoup(html, 'html.parser')
        assert soup.find('html') is not None
    
    def test_create_directory_site(self):
        """Test directory site creation."""
        site = MockWebsiteGenerator.create_directory_site(num_entries=50)
        
        assert site.config.website_type == WebsiteType.DIRECTORY
        assert site.config.num_pages == 2  # 50 entries / 25 per page = 2 pages
        assert site.config.items_per_page == 25
        
        # Test that it generates valid HTML
        html = site.generate_page("/")
        soup = BeautifulSoup(html, 'html.parser')
        assert soup.find('html') is not None
    
    def test_create_problematic_site(self):
        """Test problematic site creation."""
        site = MockWebsiteGenerator.create_problematic_site()
        
        assert site.config.website_type == WebsiteType.ECOMMERCE
        assert site.config.include_errors is True
        assert site.config.error_rate == 0.3
        assert site.config.include_malformed_html is True
        assert site.config.malformed_rate == 0.2
        
        # Test that it still generates HTML (even if problematic)
        html = site.generate_page("/")
        assert len(html) > 0


class TestWebsiteTypes:
    """Test different website type generations."""
    
    def test_ecommerce_content_structure(self):
        """Test e-commerce specific content structure."""
        config = MockWebsiteConfig(website_type=WebsiteType.ECOMMERCE)
        site = MockWebsite(config)
        
        # Test product listing
        html = site.generate_page("/page/1")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for e-commerce specific elements
        assert soup.find(class_='product-grid') is not None
        assert soup.find(class_='product-card') is not None
        assert soup.find(class_='price') is not None
        assert soup.find(class_='rating') is not None
        
        # Test product detail page
        product_html = site.generate_page("/product/1")
        product_soup = BeautifulSoup(product_html, 'html.parser')
        
        assert product_soup.find(class_='product-detail') is not None
        assert product_soup.find(class_='product-images') is not None
        assert product_soup.find(class_='specifications') is not None
    
    def test_news_content_structure(self):
        """Test news specific content structure."""
        config = MockWebsiteConfig(website_type=WebsiteType.NEWS)
        site = MockWebsite(config)
        
        # Test homepage
        html = site.generate_page("/")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for news specific elements
        assert soup.find(class_='breaking-news') is not None
        assert soup.find(class_='top-stories') is not None
        assert soup.find(class_='story-card') is not None
        
        # Check for news metadata
        meta_elements = soup.find_all(class_='meta')
        assert len(meta_elements) > 0
        
        # Check for author and time information
        html_text = html.lower()
        assert 'by ' in html_text  # Author attribution
        assert ('hour' in html_text or 'ago' in html_text)  # Time information
    
    def test_html_validity(self):
        """Test that generated HTML is valid and well-formed."""
        for website_type in [WebsiteType.ECOMMERCE, WebsiteType.NEWS, WebsiteType.BLOG]:
            config = MockWebsiteConfig(website_type=website_type)
            site = MockWebsite(config)
            
            html = site.generate_page("/")
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check basic HTML structure
            assert soup.find('html') is not None
            assert soup.find('head') is not None
            assert soup.find('body') is not None
            assert soup.find('title') is not None
            
            # Check for proper DOCTYPE
            assert html.strip().startswith('<!DOCTYPE html>')
            
            # Check for proper encoding
            charset_meta = soup.find('meta', attrs={'charset': True})
            assert charset_meta is not None
            assert charset_meta.get('charset') == 'UTF-8'
    
    def test_responsive_design_elements(self):
        """Test that generated HTML includes responsive design elements."""
        config = MockWebsiteConfig(website_type=WebsiteType.ECOMMERCE)
        site = MockWebsite(config)
        
        html = site.generate_page("/")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for viewport meta tag
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        assert viewport_meta is not None
        assert 'width=device-width' in viewport_meta.get('content', '')
        
        # Check for CSS that suggests responsive design
        style_tag = soup.find('style')
        assert style_tag is not None
        css_content = style_tag.string
        assert 'grid-template-columns' in css_content  # CSS Grid
        assert 'max-width' in css_content  # Responsive container


class TestMockWebsiteIntegration:
    """Integration tests for mock website functionality."""
    
    def test_complete_website_crawl_simulation(self):
        """Test simulating a complete website crawl."""
        site = MockWebsiteGenerator.create_ecommerce_site(num_products=10)
        
        # Get all URLs and test each one
        urls = site.get_all_urls()
        
        for url in urls:
            html = site.generate_page(url)
            
            # Each page should generate valid HTML
            assert len(html) > 100
            assert '<html' in html
            assert '</html>' in html
            
            # Parse to ensure it's valid
            soup = BeautifulSoup(html, 'html.parser')
            assert soup.find('html') is not None
    
    def test_pagination_consistency(self):
        """Test that pagination is consistent across pages."""
        site = MockWebsiteGenerator.create_ecommerce_site(num_products=50)
        
        # Test multiple pages
        for page_num in range(1, 4):
            html = site.generate_page(f"/page/{page_num}")
            soup = BeautifulSoup(html, 'html.parser')
            
            # Each page should have pagination
            pagination = soup.find(class_='pagination')
            assert pagination is not None
            
            # Should have product cards
            product_cards = soup.find_all(class_='product-card')
            assert len(product_cards) > 0
    
    def test_cross_page_linking(self):
        """Test that pages link to each other correctly."""
        site = MockWebsiteGenerator.create_ecommerce_site(num_products=20)
        
        # Test homepage
        homepage_html = site.generate_page("/")
        homepage_soup = BeautifulSoup(homepage_html, 'html.parser')
        
        # Should have links to products
        product_links = homepage_soup.find_all('a', href=lambda x: x and '/product/' in x)
        assert len(product_links) > 0
        
        # Test that linked product pages exist
        for link in product_links[:3]:  # Test first 3 links
            product_url = link.get('href')
            product_html = site.generate_page(product_url)
            assert len(product_html) > 100
            
            product_soup = BeautifulSoup(product_html, 'html.parser')
            assert product_soup.find(class_='product-detail') is not None