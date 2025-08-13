"""
Website structure analyzer for the atomic scraper tool.

Analyzes HTML structure and content patterns to identify common content types,
pagination, navigation, and content organization.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag, NavigableString
from pydantic import BaseModel, Field


@dataclass
class ContentPattern:
    """Represents a detected content pattern in the website."""
    pattern_type: str  # 'list', 'article', 'product', 'navigation', 'pagination'
    selector: str  # CSS selector that matches this pattern
    confidence: float  # Confidence score (0.0 to 1.0)
    sample_elements: List[str]  # Sample HTML elements
    attributes: Dict[str, Any]  # Additional pattern attributes


@dataclass
class NavigationInfo:
    """Information about website navigation structure."""
    main_nav_selector: Optional[str] = None
    breadcrumb_selector: Optional[str] = None
    sidebar_nav_selector: Optional[str] = None
    footer_nav_selector: Optional[str] = None
    menu_items: List[str] = None
    
    def __post_init__(self):
        if self.menu_items is None:
            self.menu_items = []


@dataclass
class PaginationInfo:
    """Information about pagination patterns."""
    pagination_type: Optional[str] = None  # 'numbered', 'next_prev', 'infinite_scroll', 'load_more'
    pagination_selector: Optional[str] = None
    next_button_selector: Optional[str] = None
    prev_button_selector: Optional[str] = None
    page_number_selector: Optional[str] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = None


class WebsiteStructureAnalysis(BaseModel):
    """Complete analysis of website structure."""
    
    url: str = Field(..., description="URL that was analyzed")
    title: str = Field(..., description="Page title")
    content_patterns: List[ContentPattern] = Field(default_factory=list, description="Detected content patterns")
    navigation_info: NavigationInfo = Field(default_factory=NavigationInfo, description="Navigation structure")
    pagination_info: PaginationInfo = Field(default_factory=PaginationInfo, description="Pagination information")
    content_types: Set[str] = Field(default_factory=set, description="Detected content types")
    main_content_selector: Optional[str] = Field(None, description="Selector for main content area")
    list_containers: List[str] = Field(default_factory=list, description="Selectors for list containers")
    item_selectors: List[str] = Field(default_factory=list, description="Selectors for individual items")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis metadata")
    
    class Config:
        arbitrary_types_allowed = True


class WebsiteAnalyzer:
    """Analyzes website HTML structure and content patterns."""
    
    def __init__(self):
        """Initialize the website analyzer."""
        self.content_type_patterns = {
            'list': [
                r'ul\s*>\s*li',
                r'ol\s*>\s*li', 
                r'\.list',
                r'\.items',
                r'\[class\*="item"\]',
                r'\[class\*="list"\]'
            ],
            'article': [
                r'article',
                r'\.article',
                r'\.post',
                r'\.blog',
                r'\[class\*="article"\]',
                r'\[class\*="post"\]'
            ],
            'product': [
                r'\.product',
                r'\.item',
                r'\[class\*="product"\]',
                r'\[data-product\]',
                r'\.price',
                r'\.buy'
            ],
            'navigation': [
                r'nav',
                r'\.nav',
                r'\.menu',
                r'\.navigation',
                r'\[role="navigation"\]'
            ],
            'pagination': [
                r'\.pagination',
                r'\.pager',
                r'\.page-numbers',
                r'\[class\*="page"\]'
            ]
        }
        
        self.list_indicators = [
            'ul', 'ol', 'div[class*="list"]', 'div[class*="items"]',
            'section[class*="list"]', 'div[class*="grid"]',
            'div[class*="row"]', 'div[class*="container"]'
        ]
        
        self.item_indicators = [
            'li', 'div[class*="item"]', 'div[class*="card"]',
            'article', 'div[class*="product"]', 'div[class*="post"]',
            'div[class*="entry"]', 'div[class*="result"]'
        ]
    
    def analyze_website(self, html_content: str, url: str) -> WebsiteStructureAnalysis:
        """
        Analyze website structure and content patterns.
        
        Args:
            html_content: HTML content to analyze
            url: URL of the website
            
        Returns:
            WebsiteStructureAnalysis object with detected patterns
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        analysis = WebsiteStructureAnalysis(url=url, title=self._extract_title(soup))
        
        # Analyze different aspects of the website
        analysis.content_patterns = self._detect_content_patterns(soup)
        analysis.navigation_info = self._analyze_navigation(soup)
        analysis.pagination_info = self._analyze_pagination(soup)
        analysis.content_types = self._identify_content_types(soup)
        analysis.main_content_selector = self._find_main_content_selector(soup)
        analysis.list_containers = self._find_list_containers(soup)
        analysis.item_selectors = self._find_item_selectors(soup)
        analysis.metadata = self._extract_metadata(soup, url)
        
        return analysis
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Unknown Title"
    
    def _detect_content_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Detect common content patterns in the HTML."""
        patterns = []
        
        # Detect list patterns
        list_patterns = self._detect_list_patterns(soup)
        patterns.extend(list_patterns)
        
        # Detect article patterns
        article_patterns = self._detect_article_patterns(soup)
        patterns.extend(article_patterns)
        
        # Detect product patterns
        product_patterns = self._detect_product_patterns(soup)
        patterns.extend(product_patterns)
        
        # Detect navigation patterns
        nav_patterns = self._detect_navigation_patterns(soup)
        patterns.extend(nav_patterns)
        
        # Detect pagination patterns
        pagination_patterns = self._detect_pagination_patterns(soup)
        patterns.extend(pagination_patterns)
        
        return patterns
    
    def _detect_list_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Detect list-like content patterns."""
        patterns = []
        
        # Look for actual lists (ul, ol)
        for list_tag in soup.find_all(['ul', 'ol']):
            items = list_tag.find_all('li')
            if len(items) >= 3:  # Minimum 3 items to consider it a content list
                selector = self._generate_selector(list_tag)
                confidence = min(1.0, len(items) / 10.0)  # Higher confidence for more items
                
                sample_elements = [str(item)[:200] + '...' if len(str(item)) > 200 else str(item) 
                                 for item in items[:3]]
                
                patterns.append(ContentPattern(
                    pattern_type='list',
                    selector=selector,
                    confidence=confidence,
                    sample_elements=sample_elements,
                    attributes={'item_count': len(items), 'list_type': list_tag.name}
                ))
        
        # Look for div-based lists
        potential_containers = soup.find_all('div', class_=re.compile(r'(list|items|grid|container)', re.I))
        for container in potential_containers:
            items = self._find_repeated_elements(container)
            if len(items) >= 3:
                selector = self._generate_selector(container)
                confidence = min(0.8, len(items) / 15.0)  # Slightly lower confidence for div lists
                
                sample_elements = [str(item)[:200] + '...' if len(str(item)) > 200 else str(item) 
                                 for item in items[:3]]
                
                patterns.append(ContentPattern(
                    pattern_type='list',
                    selector=selector,
                    confidence=confidence,
                    sample_elements=sample_elements,
                    attributes={'item_count': len(items), 'container_type': 'div'}
                ))
        
        return patterns
    
    def _detect_article_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Detect article-like content patterns."""
        patterns = []
        
        # Look for article tags
        for article in soup.find_all('article'):
            selector = self._generate_selector(article)
            confidence = 0.9  # High confidence for semantic article tags
            
            patterns.append(ContentPattern(
                pattern_type='article',
                selector=selector,
                confidence=confidence,
                sample_elements=[str(article)[:300] + '...'],
                attributes={'has_semantic_tag': True}
            ))
        
        # Look for article-like divs
        article_divs = soup.find_all('div', class_=re.compile(r'(article|post|blog|entry)', re.I))
        for div in article_divs:
            selector = self._generate_selector(div)
            confidence = 0.7  # Lower confidence for class-based detection
            
            patterns.append(ContentPattern(
                pattern_type='article',
                selector=selector,
                confidence=confidence,
                sample_elements=[str(div)[:300] + '...'],
                attributes={'has_semantic_tag': False}
            ))
        
        return patterns
    
    def _detect_product_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Detect product-like content patterns."""
        patterns = []
        
        # Look for product-related elements
        product_indicators = ['product', 'item', 'price', 'buy', 'cart', 'shop']
        
        for indicator in product_indicators:
            elements = soup.find_all(attrs={'class': re.compile(indicator, re.I)})
            if elements:
                # Group similar elements
                grouped = self._group_similar_elements(elements)
                for group in grouped:
                    if len(group) >= 2:  # At least 2 similar elements
                        selector = self._generate_common_selector(group)
                        confidence = min(0.8, len(group) / 10.0)
                        
                        sample_elements = [str(elem)[:200] + '...' if len(str(elem)) > 200 else str(elem) 
                                         for elem in group[:3]]
                        
                        patterns.append(ContentPattern(
                            pattern_type='product',
                            selector=selector,
                            confidence=confidence,
                            sample_elements=sample_elements,
                            attributes={'indicator': indicator, 'count': len(group)}
                        ))
        
        return patterns
    
    def _detect_navigation_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Detect navigation patterns."""
        patterns = []
        
        # Look for nav tags
        for nav in soup.find_all('nav'):
            selector = self._generate_selector(nav)
            confidence = 0.9
            
            patterns.append(ContentPattern(
                pattern_type='navigation',
                selector=selector,
                confidence=confidence,
                sample_elements=[str(nav)[:300] + '...'],
                attributes={'nav_type': 'semantic'}
            ))
        
        # Look for navigation-like divs
        nav_divs = soup.find_all('div', class_=re.compile(r'(nav|menu|navigation)', re.I))
        for div in nav_divs:
            selector = self._generate_selector(div)
            confidence = 0.7
            
            patterns.append(ContentPattern(
                pattern_type='navigation',
                selector=selector,
                confidence=confidence,
                sample_elements=[str(div)[:300] + '...'],
                attributes={'nav_type': 'class_based'}
            ))
        
        return patterns
    
    def _detect_pagination_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Detect pagination patterns."""
        patterns = []
        
        # Look for pagination elements
        pagination_selectors = [
            'div[class*="pagination"]',
            'div[class*="pager"]', 
            'div[class*="page-numbers"]',
            'nav[class*="pagination"]'
        ]
        
        for selector in pagination_selectors:
            elements = soup.select(selector)
            for element in elements:
                confidence = 0.8
                
                patterns.append(ContentPattern(
                    pattern_type='pagination',
                    selector=selector,
                    confidence=confidence,
                    sample_elements=[str(element)[:300] + '...'],
                    attributes={'selector_type': selector}
                ))
        
        return patterns
    
    def _analyze_navigation(self, soup: BeautifulSoup) -> NavigationInfo:
        """Analyze navigation structure."""
        nav_info = NavigationInfo()
        
        # Find main navigation
        main_nav = soup.find('nav') or soup.find('div', class_=re.compile(r'(main.*nav|nav.*main)', re.I))
        if main_nav:
            nav_info.main_nav_selector = self._generate_selector(main_nav)
        
        # Find breadcrumbs
        breadcrumb = soup.find(attrs={'class': re.compile(r'breadcrumb', re.I)})
        if breadcrumb:
            nav_info.breadcrumb_selector = self._generate_selector(breadcrumb)
        
        # Find sidebar navigation
        sidebar_nav = soup.find('div', class_=re.compile(r'(sidebar.*nav|nav.*sidebar)', re.I))
        if sidebar_nav:
            nav_info.sidebar_nav_selector = self._generate_selector(sidebar_nav)
        
        # Find footer navigation
        footer = soup.find('footer')
        if footer:
            footer_nav = footer.find('nav') or footer.find('div', class_=re.compile(r'nav', re.I))
            if footer_nav:
                nav_info.footer_nav_selector = self._generate_selector(footer_nav)
        
        # Extract menu items
        if main_nav:
            links = main_nav.find_all('a')
            nav_info.menu_items = [link.get_text().strip() for link in links if link.get_text().strip()]
        
        return nav_info
    
    def _analyze_pagination(self, soup: BeautifulSoup) -> PaginationInfo:
        """Analyze pagination patterns."""
        pagination_info = PaginationInfo()
        
        # Look for pagination container
        pagination_container = (
            soup.find('div', class_=re.compile(r'pagination', re.I)) or
            soup.find('nav', class_=re.compile(r'pagination', re.I)) or
            soup.find('div', class_=re.compile(r'pager', re.I))
        )
        
        if pagination_container:
            pagination_info.pagination_selector = self._generate_selector(pagination_container)
            
            # Determine pagination type
            if pagination_container.find('a', string=re.compile(r'next', re.I)):
                pagination_info.pagination_type = 'next_prev'
                
                next_link = pagination_container.find('a', string=re.compile(r'next', re.I))
                if next_link:
                    pagination_info.next_button_selector = self._generate_selector(next_link)
                
                prev_link = pagination_container.find('a', string=re.compile(r'prev', re.I))
                if prev_link:
                    pagination_info.prev_button_selector = self._generate_selector(prev_link)
            
            # Look for numbered pagination
            number_links = pagination_container.find_all('a', string=re.compile(r'^\d+$'))
            if number_links:
                pagination_info.pagination_type = 'numbered'
                pagination_info.page_number_selector = self._generate_common_selector(number_links)
                
                # Try to determine total pages
                numbers = [int(link.get_text()) for link in number_links if link.get_text().isdigit()]
                if numbers:
                    pagination_info.total_pages = max(numbers)
        
        # Look for infinite scroll indicators
        if soup.find(attrs={'class': re.compile(r'(infinite|scroll|load.*more)', re.I)}):
            pagination_info.pagination_type = 'infinite_scroll'
        
        return pagination_info
    
    def _identify_content_types(self, soup: BeautifulSoup) -> Set[str]:
        """Identify the types of content present on the page."""
        content_types = set()
        
        # Check for various content type indicators
        if soup.find_all(['ul', 'ol']) or soup.find_all(attrs={'class': re.compile(r'list', re.I)}):
            content_types.add('list')
        
        if soup.find_all('article') or soup.find_all(attrs={'class': re.compile(r'(article|post|blog)', re.I)}):
            content_types.add('article')
        
        if soup.find_all(attrs={'class': re.compile(r'(product|price|buy|cart)', re.I)}):
            content_types.add('product')
        
        if soup.find_all('nav') or soup.find_all(attrs={'class': re.compile(r'(nav|menu)', re.I)}):
            content_types.add('navigation')
        
        if soup.find_all(attrs={'class': re.compile(r'(pagination|pager)', re.I)}):
            content_types.add('pagination')
        
        if soup.find_all('form'):
            content_types.add('form')
        
        if soup.find_all('table'):
            content_types.add('table')
        
        return content_types
    
    def _find_main_content_selector(self, soup: BeautifulSoup) -> Optional[str]:
        """Find the main content area selector."""
        # Look for semantic main tag
        main_tag = soup.find('main')
        if main_tag:
            return self._generate_selector(main_tag)
        
        # Look for content-related classes
        content_indicators = ['content', 'main', 'primary', 'body']
        for indicator in content_indicators:
            element = soup.find(attrs={'class': re.compile(indicator, re.I)})
            if element:
                return self._generate_selector(element)
        
        # Look for the largest content container
        containers = soup.find_all('div')
        if containers:
            # Find container with most text content
            largest_container = max(containers, key=lambda x: len(x.get_text()))
            if len(largest_container.get_text()) > 500:  # Minimum content threshold
                return self._generate_selector(largest_container)
        
        return None
    
    def _find_list_containers(self, soup: BeautifulSoup) -> List[str]:
        """Find selectors for list containers."""
        selectors = []
        
        # Find actual list elements
        for list_elem in soup.find_all(['ul', 'ol']):
            if len(list_elem.find_all('li')) >= 3:
                selectors.append(self._generate_selector(list_elem))
        
        # Find div-based list containers
        for indicator in self.list_indicators:
            elements = soup.select(indicator)
            for element in elements:
                if self._has_repeated_children(element):
                    selector = self._generate_selector(element)
                    if selector not in selectors:
                        selectors.append(selector)
        
        return selectors
    
    def _find_item_selectors(self, soup: BeautifulSoup) -> List[str]:
        """Find selectors for individual items within lists."""
        selectors = []
        
        # Find list items
        if soup.find_all('li'):
            selectors.append('li')
        
        # Find item-like elements
        for indicator in self.item_indicators:
            elements = soup.select(indicator)
            if len(elements) >= 3:  # Multiple similar elements
                if indicator not in selectors:
                    selectors.append(indicator)
        
        return selectors
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract additional metadata about the website."""
        metadata = {}
        
        # Basic page info
        metadata['url'] = url
        metadata['domain'] = urlparse(url).netloc
        
        # Count various elements
        metadata['total_links'] = len(soup.find_all('a'))
        metadata['total_images'] = len(soup.find_all('img'))
        metadata['total_forms'] = len(soup.find_all('form'))
        metadata['total_tables'] = len(soup.find_all('table'))
        
        # Text content analysis
        text_content = soup.get_text()
        metadata['text_length'] = len(text_content)
        metadata['word_count'] = len(text_content.split())
        
        # Meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            metadata['meta_description'] = meta_description.get('content', '')
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['meta_keywords'] = meta_keywords.get('content', '')
        
        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag.get('lang')
        
        return metadata
    
    def _find_repeated_elements(self, container: Tag) -> List[Tag]:
        """Find repeated elements within a container."""
        children = [child for child in container.children if isinstance(child, Tag)]
        
        if len(children) < 3:
            return []
        
        # Group children by tag name and class
        groups = {}
        for child in children:
            key = (child.name, tuple(sorted(child.get('class', []))))
            if key not in groups:
                groups[key] = []
            groups[key].append(child)
        
        # Return the largest group if it has at least 3 elements
        largest_group = max(groups.values(), key=len, default=[])
        return largest_group if len(largest_group) >= 3 else []
    
    def _has_repeated_children(self, element: Tag) -> bool:
        """Check if element has repeated child elements."""
        repeated_elements = self._find_repeated_elements(element)
        return len(repeated_elements) >= 3
    
    def _group_similar_elements(self, elements: List[Tag]) -> List[List[Tag]]:
        """Group similar elements together."""
        groups = {}
        
        for element in elements:
            # Create a signature based on tag name and classes
            classes = tuple(sorted(element.get('class', [])))
            key = (element.name, classes)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(element)
        
        # Return groups with at least 2 elements
        return [group for group in groups.values() if len(group) >= 2]
    
    def _generate_selector(self, element: Tag) -> str:
        """Generate a CSS selector for an element."""
        selectors = []
        
        # Add tag name
        selectors.append(element.name)
        
        # Add ID if present
        if element.get('id'):
            return f"#{element.get('id')}"
        
        # Add classes if present
        classes = element.get('class', [])
        if classes:
            class_selector = '.' + '.'.join(classes)
            selectors.append(class_selector)
            return f"{element.name}{class_selector}"
        
        # Add attributes if no ID or class
        for attr in ['data-id', 'data-type', 'role']:
            if element.get(attr):
                return f"{element.name}[{attr}='{element.get(attr)}']"
        
        return element.name
    
    def _generate_common_selector(self, elements: List[Tag]) -> str:
        """Generate a common selector for a group of similar elements."""
        if not elements:
            return ""
        
        first_element = elements[0]
        
        # If all elements have the same ID pattern, use that
        if all(elem.get('id') for elem in elements):
            return f"#{first_element.get('id')}"
        
        # If all elements have common classes, use those
        common_classes = set(first_element.get('class', []))
        for element in elements[1:]:
            common_classes &= set(element.get('class', []))
        
        if common_classes:
            class_selector = '.' + '.'.join(sorted(common_classes))
            return f"{first_element.name}{class_selector}"
        
        # Fall back to tag name
        return first_element.name