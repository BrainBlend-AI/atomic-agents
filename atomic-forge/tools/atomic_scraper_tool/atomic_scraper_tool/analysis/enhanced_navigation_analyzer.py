"""
Enhanced navigation analyzer for complex website navigation detection.

This module provides advanced navigation pattern detection including:
- Multi-level navigation hierarchies
- Dynamic/JavaScript-based navigation
- Mobile navigation patterns
- Mega menus and dropdown structures
- Contextual navigation (related links, tags, categories)
- Breadcrumb variations
- Pagination with complex patterns
"""

import re
from typing import Dict, List, Optional, Set, Any, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field


@dataclass
class NavigationHierarchy:
    """Represents a hierarchical navigation structure."""
    
    level: int
    parent_selector: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    dropdown_selector: Optional[str] = None
    has_submenu: bool = False
    submenu_trigger: Optional[str] = None  # hover, click, etc.


@dataclass
class MegaMenuInfo:
    """Information about mega menu structures."""
    
    trigger_selector: str
    content_selector: str
    columns: List[str] = field(default_factory=list)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    activation_method: str = "hover"  # hover, click, focus


@dataclass
class MobileNavigationInfo:
    """Mobile-specific navigation patterns."""
    
    hamburger_selector: Optional[str] = None
    mobile_menu_selector: Optional[str] = None
    overlay_selector: Optional[str] = None
    slide_direction: Optional[str] = None  # left, right, top, bottom
    has_accordion: bool = False


@dataclass
class ContextualNavigationInfo:
    """Contextual navigation elements."""
    
    related_links: List[str] = field(default_factory=list)
    tags_selector: Optional[str] = None
    categories_selector: Optional[str] = None
    social_sharing: List[str] = field(default_factory=list)
    author_links: List[str] = field(default_factory=list)


@dataclass
class AdvancedPaginationInfo:
    """Advanced pagination pattern detection."""
    
    pagination_type: str  # numbered, infinite_scroll, load_more, cursor_based
    container_selector: Optional[str] = None
    current_page_selector: Optional[str] = None
    page_links_selector: Optional[str] = None
    next_selector: Optional[str] = None
    prev_selector: Optional[str] = None
    first_selector: Optional[str] = None
    last_selector: Optional[str] = None
    load_more_selector: Optional[str] = None
    infinite_scroll_trigger: Optional[str] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    has_page_size_selector: bool = False
    page_size_selector: Optional[str] = None


@dataclass
class EnhancedNavigationAnalysis:
    """Complete enhanced navigation analysis results."""
    
    url: str
    main_navigation: List[NavigationHierarchy] = field(default_factory=list)
    mega_menus: List[MegaMenuInfo] = field(default_factory=list)
    mobile_navigation: Optional[MobileNavigationInfo] = None
    contextual_navigation: Optional[ContextualNavigationInfo] = None
    advanced_pagination: Optional[AdvancedPaginationInfo] = None
    breadcrumb_variations: List[str] = field(default_factory=list)
    search_navigation: Dict[str, str] = field(default_factory=dict)
    filter_navigation: Dict[str, List[str]] = field(default_factory=dict)
    dynamic_content_indicators: List[str] = field(default_factory=list)
    accessibility_features: Dict[str, bool] = field(default_factory=dict)


class EnhancedNavigationAnalyzer:
    """Advanced navigation pattern analyzer for complex websites."""
    
    def __init__(self):
        self.navigation_patterns = {
            "main_nav": [
                "nav[role='navigation']",
                "nav.main-nav",
                "nav.primary-nav",
                "nav.navbar",
                "header nav",
                ".main-navigation",
                ".primary-navigation",
                ".navbar",
                "#main-nav",
                "#primary-nav"
            ],
            "mega_menu": [
                ".mega-menu",
                ".dropdown-mega",
                ".nav-mega",
                "[class*='mega']",
                ".large-dropdown",
                ".full-width-dropdown"
            ],
            "mobile_nav": [
                ".mobile-nav",
                ".mobile-menu",
                ".hamburger",
                ".menu-toggle",
                ".nav-toggle",
                "[class*='mobile']",
                ".off-canvas",
                ".slide-menu"
            ],
            "breadcrumb": [
                ".breadcrumb",
                ".breadcrumbs",
                "[aria-label*='breadcrumb']",
                ".crumbs",
                ".path",
                ".navigation-path",
                "[class*='breadcrumb']"
            ],
            "pagination": [
                ".pagination",
                ".pager",
                ".page-numbers",
                ".paginate",
                "[class*='page']",
                "[aria-label*='pagination']",
                ".load-more",
                ".infinite-scroll"
            ]
        }
        
        self.dynamic_indicators = [
            "[data-toggle]",
            "[data-target]",
            "[data-bs-toggle]",
            "[data-bs-target]",
            "[onclick]",
            "[data-href]",
            ".js-",
            "[class*='ajax']",
            "[class*='dynamic']"
        ]
    
    def analyze_navigation(self, html_content: str, url: str) -> EnhancedNavigationAnalysis:
        """
        Perform comprehensive navigation analysis.
        
        Args:
            html_content: HTML content to analyze
            url: URL of the website
            
        Returns:
            EnhancedNavigationAnalysis with detailed navigation information
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        analysis = EnhancedNavigationAnalysis(url=url)
        
        # Analyze different navigation aspects
        analysis.main_navigation = self._analyze_hierarchical_navigation(soup)
        analysis.mega_menus = self._detect_mega_menus(soup)
        analysis.mobile_navigation = self._analyze_mobile_navigation(soup)
        analysis.contextual_navigation = self._analyze_contextual_navigation(soup)
        analysis.advanced_pagination = self._analyze_advanced_pagination(soup)
        analysis.breadcrumb_variations = self._detect_breadcrumb_variations(soup)
        analysis.search_navigation = self._analyze_search_navigation(soup)
        analysis.filter_navigation = self._analyze_filter_navigation(soup)
        analysis.dynamic_content_indicators = self._detect_dynamic_content(soup)
        analysis.accessibility_features = self._analyze_accessibility_features(soup)
        
        return analysis
    
    def _analyze_hierarchical_navigation(self, soup: BeautifulSoup) -> List[NavigationHierarchy]:
        """Analyze multi-level navigation hierarchies."""
        hierarchies = []
        
        # Find main navigation containers
        for pattern in self.navigation_patterns["main_nav"]:
            nav_elements = soup.select(pattern)
            
            for nav_element in nav_elements:
                hierarchy = self._build_navigation_hierarchy(nav_element, 0)
                if hierarchy and hierarchy.items:
                    hierarchies.append(hierarchy)
        
        return hierarchies
    
    def _build_navigation_hierarchy(self, element: Tag, level: int) -> Optional[NavigationHierarchy]:
        """Build navigation hierarchy from an element."""
        if not element:
            return None
            
        hierarchy = NavigationHierarchy(level=level)
        
        # Find direct navigation items
        nav_items = []
        
        # Look for list-based navigation
        lists = element.find_all(["ul", "ol"], recursive=False)
        for nav_list in lists:
            items = nav_list.find_all("li", recursive=False)
            for item in items:
                nav_item = self._extract_nav_item_info(item, level)
                if nav_item:
                    nav_items.append(nav_item)
        
        # Look for div-based navigation
        if not nav_items:
            divs = element.find_all("div", recursive=False)
            for div in divs:
                if self._is_nav_item(div):
                    nav_item = self._extract_nav_item_info(div, level)
                    if nav_item:
                        nav_items.append(nav_item)
        
        # Look for direct links
        if not nav_items:
            links = element.find_all("a", recursive=False)
            for link in links:
                nav_item = self._extract_nav_item_info(link, level)
                if nav_item:
                    nav_items.append(nav_item)
        
        hierarchy.items = nav_items
        
        # Check for dropdowns/submenus
        dropdown_indicators = element.select("[class*='dropdown'], [class*='submenu'], [class*='sub-menu']")
        if dropdown_indicators:
            hierarchy.has_submenu = True
            hierarchy.dropdown_selector = self._generate_selector(dropdown_indicators[0])
            
            # Detect submenu trigger method
            if element.select("[data-toggle='dropdown']"):
                hierarchy.submenu_trigger = "click"
            elif element.select("[class*='hover']"):
                hierarchy.submenu_trigger = "hover"
            else:
                hierarchy.submenu_trigger = "hover"  # default assumption
        
        return hierarchy
    
    def _extract_nav_item_info(self, item: Tag, level: int) -> Optional[Dict[str, Any]]:
        """Extract information from a navigation item."""
        if not item:
            return None
            
        nav_item = {
            "text": "",
            "href": None,
            "selector": self._generate_selector(item),
            "has_submenu": False,
            "submenu_items": [],
            "level": level
        }
        
        # Extract text
        link = item.find("a")
        if link:
            nav_item["text"] = link.get_text(strip=True)
            nav_item["href"] = link.get("href")
        else:
            nav_item["text"] = item.get_text(strip=True)
        
        # Check for submenu - look for nested ul/ol elements
        submenu = item.find(["ul", "ol"], recursive=False)  # Only direct children
        if submenu:
            nav_item["has_submenu"] = True
            # Build submenu hierarchy
            submenu_items = []
            submenu_list_items = submenu.find_all("li", recursive=False)
            for submenu_item in submenu_list_items:
                submenu_nav_item = self._extract_nav_item_info(submenu_item, level + 1)
                if submenu_nav_item:
                    submenu_items.append(submenu_nav_item)
            nav_item["submenu_items"] = submenu_items
        
        return nav_item if nav_item["text"] else None
    
    def _is_nav_item(self, element: Tag) -> bool:
        """Check if an element is likely a navigation item."""
        if not element:
            return False
            
        # Check for navigation-related classes
        classes = element.get("class", [])
        nav_classes = ["nav-item", "menu-item", "navigation-item", "nav-link"]
        
        for nav_class in nav_classes:
            if any(nav_class in cls for cls in classes):
                return True
        
        # Check if it contains a link
        return bool(element.find("a"))
    
    def _detect_mega_menus(self, soup: BeautifulSoup) -> List[MegaMenuInfo]:
        """Detect mega menu structures."""
        mega_menus = []
        
        for pattern in self.navigation_patterns["mega_menu"]:
            mega_elements = soup.select(pattern)
            
            for mega_element in mega_elements:
                mega_menu = MegaMenuInfo(
                    trigger_selector=self._find_mega_menu_trigger(mega_element),
                    content_selector=self._generate_selector(mega_element)
                )
                
                # Analyze mega menu structure
                columns = mega_element.select("[class*='col'], [class*='column']")
                mega_menu.columns = [self._generate_selector(col) for col in columns]
                
                # Find sections within mega menu
                sections = mega_element.select("[class*='section'], [class*='group'], .col, [class*='col']")
                for section in sections:
                    section_info = {
                        "selector": self._generate_selector(section),
                        "title": self._extract_section_title(section),
                        "links": [link.get("href") for link in section.find_all("a") if link.get("href")]
                    }
                    mega_menu.sections.append(section_info)
                
                # Determine activation method
                parent = mega_element.find_parent()
                if parent and (parent.get("data-toggle") == "dropdown" or "click" in str(parent.get("class", []))):
                    mega_menu.activation_method = "click"
                
                mega_menus.append(mega_menu)
        
        return mega_menus
    
    def _find_mega_menu_trigger(self, mega_element: Tag) -> str:
        """Find the trigger element for a mega menu."""
        parent = mega_element.find_parent()
        if parent:
            trigger = parent.find("a") or parent.find("button")
            if trigger:
                return self._generate_selector(trigger)
        
        # Look for sibling trigger
        prev_sibling = mega_element.find_previous_sibling()
        if prev_sibling and (prev_sibling.name in ["a", "button"] or prev_sibling.find(["a", "button"])):
            return self._generate_selector(prev_sibling)
        
        return self._generate_selector(mega_element)
    
    def _extract_section_title(self, section: Tag) -> str:
        """Extract title from a mega menu section."""
        title_elements = section.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if title_elements:
            return title_elements[0].get_text(strip=True)
        
        # Look for elements with title-like classes
        title_element = section.find(class_=re.compile(r"(title|heading|header)", re.I))
        if title_element:
            return title_element.get_text(strip=True)
        
        return ""
    
    def _analyze_mobile_navigation(self, soup: BeautifulSoup) -> Optional[MobileNavigationInfo]:
        """Analyze mobile-specific navigation patterns."""
        mobile_nav = MobileNavigationInfo()
        found_mobile_elements = False
        
        # Find hamburger menu
        hamburger_selectors = [
            ".hamburger", ".menu-toggle", ".nav-toggle", 
            "[class*='hamburger']", "[class*='menu-toggle']",
            ".mobile-menu-trigger", ".sidebar-toggle"
        ]
        
        for selector in hamburger_selectors:
            hamburger = soup.select_one(selector)
            if hamburger:
                mobile_nav.hamburger_selector = selector
                found_mobile_elements = True
                break
        
        # Find mobile menu container
        for pattern in self.navigation_patterns["mobile_nav"]:
            mobile_menu = soup.select_one(pattern)
            if mobile_menu:
                mobile_nav.mobile_menu_selector = pattern
                found_mobile_elements = True
                
                # Detect slide direction from classes
                classes = " ".join(mobile_menu.get("class", []))
                if "left" in classes or "slide-left" in classes:
                    mobile_nav.slide_direction = "left"
                elif "right" in classes or "slide-right" in classes:
                    mobile_nav.slide_direction = "right"
                elif "top" in classes or "slide-top" in classes:
                    mobile_nav.slide_direction = "top"
                elif "bottom" in classes or "slide-bottom" in classes:
                    mobile_nav.slide_direction = "bottom"
                
                # Check for accordion-style mobile menu
                accordion_indicators = mobile_menu.select("[class*='accordion'], [class*='collaps']")
                if accordion_indicators:
                    mobile_nav.has_accordion = True
                
                break
        
        # Find overlay
        overlay_selectors = [".overlay", ".mobile-overlay", ".nav-overlay", "[class*='overlay']"]
        for selector in overlay_selectors:
            overlay = soup.select_one(selector)
            if overlay:
                mobile_nav.overlay_selector = selector
                found_mobile_elements = True
                break
        
        return mobile_nav if found_mobile_elements else None
    
    def _analyze_advanced_pagination(self, soup: BeautifulSoup) -> Optional[AdvancedPaginationInfo]:
        """Analyze advanced pagination patterns."""
        pagination_info = None
        
        # Check for infinite scroll indicators first (higher priority)
        infinite_scroll_indicators = soup.select("[class*='infinite'], [data-infinite], [class*='lazy-load']")
        if infinite_scroll_indicators:
            pagination_info = AdvancedPaginationInfo(pagination_type="infinite_scroll")
            pagination_info.infinite_scroll_trigger = self._generate_selector(infinite_scroll_indicators[0])
            return pagination_info
        
        # Check for load more buttons
        load_more_buttons = soup.select(".load-more, [class*='load-more'], button[class*='more']")
        if load_more_buttons:
            pagination_info = AdvancedPaginationInfo(pagination_type="load_more")
            pagination_info.load_more_selector = self._generate_selector(load_more_buttons[0])
            return pagination_info
        
        # Look for pagination containers (lowest priority)
        for pattern in self.navigation_patterns["pagination"]:
            pagination_container = soup.select_one(pattern)
            if pagination_container:
                pagination_info = AdvancedPaginationInfo(pagination_type="numbered")
                pagination_info.container_selector = pattern
                
                # Analyze pagination elements
                self._analyze_pagination_elements(pagination_container, pagination_info)
                break
        
        return pagination_info
    
    def _analyze_pagination_elements(self, container: Tag, pagination_info: AdvancedPaginationInfo):
        """Analyze elements within a pagination container."""
        # Find current page
        current_indicators = container.select(".current, .active, [aria-current], [class*='current']")
        if current_indicators:
            pagination_info.current_page_selector = self._generate_selector(current_indicators[0])
            try:
                pagination_info.current_page = int(current_indicators[0].get_text(strip=True))
            except (ValueError, AttributeError):
                pass
        
        # Find page links
        page_links = container.select("a[href*='page'], a[href*='p='], a[class*='page']")
        if page_links:
            pagination_info.page_links_selector = "a[href*='page'], a[href*='p='], a[class*='page']"
            
            # Try to determine total pages
            page_numbers = []
            for link in page_links:
                text = link.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))
            
            if page_numbers:
                pagination_info.total_pages = max(page_numbers)
        
        # Find navigation buttons
        next_buttons = container.select("a[class*='next'], button[class*='next'], [aria-label*='next']")
        if next_buttons:
            pagination_info.next_selector = self._generate_selector(next_buttons[0])
        
        prev_buttons = container.select("a[class*='prev'], button[class*='prev'], [aria-label*='prev']")
        if prev_buttons:
            pagination_info.prev_selector = self._generate_selector(prev_buttons[0])
        
        first_buttons = container.select("a[class*='first'], button[class*='first'], [aria-label*='first']")
        if first_buttons:
            pagination_info.first_selector = self._generate_selector(first_buttons[0])
        
        last_buttons = container.select("a[class*='last'], button[class*='last'], [aria-label*='last']")
        if last_buttons:
            pagination_info.last_selector = self._generate_selector(last_buttons[0])
        
        # Check for page size selector
        page_size_selectors = container.select("select[name*='size'], select[name*='per'], select[class*='per-page']")
        if page_size_selectors:
            pagination_info.has_page_size_selector = True
            pagination_info.page_size_selector = self._generate_selector(page_size_selectors[0])
    
    def _analyze_contextual_navigation(self, soup: BeautifulSoup) -> Optional[ContextualNavigationInfo]:
        """Analyze contextual navigation elements."""
        contextual_nav = ContextualNavigationInfo()
        found_elements = False
        
        # Find related links
        related_sections = soup.select("[class*='related'], [class*='similar'], [class*='recommend']")
        for section in related_sections:
            links = section.find_all("a")
            contextual_nav.related_links.extend([self._generate_selector(link) for link in links])
            if links:
                found_elements = True
        
        # Find tags
        tag_containers = soup.select("[class*='tag'], [class*='label'], [class*='keyword']")
        if tag_containers:
            contextual_nav.tags_selector = self._generate_selector(tag_containers[0])
            found_elements = True
        
        # Find categories
        category_containers = soup.select("[class*='categor'], [class*='topic'], [class*='subject']")
        if category_containers:
            contextual_nav.categories_selector = self._generate_selector(category_containers[0])
            found_elements = True
        
        # Find social sharing
        social_containers = soup.select("[class*='social'], [class*='share']")
        for container in social_containers:
            links = container.find_all("a")
            contextual_nav.social_sharing.extend([self._generate_selector(link) for link in links])
            if links:
                found_elements = True
        
        # Find author links
        author_containers = soup.select("[class*='author'], [class*='writer'], [class*='by-']")
        for container in author_containers:
            links = container.find_all("a")
            contextual_nav.author_links.extend([self._generate_selector(link) for link in links])
            if links:
                found_elements = True
        
        return contextual_nav if found_elements else None
    
    def _detect_breadcrumb_variations(self, soup: BeautifulSoup) -> List[str]:
        """Detect various breadcrumb patterns."""
        breadcrumb_selectors = []
        
        for pattern in self.navigation_patterns["breadcrumb"]:
            breadcrumbs = soup.select(pattern)
            if breadcrumbs:
                breadcrumb_selectors.append(pattern)
        
        # Additional breadcrumb patterns
        additional_patterns = [
            "[itemtype*='BreadcrumbList']",
            "[typeof*='BreadcrumbList']",
            "nav[aria-label*='breadcrumb']",
            "[role='navigation'][aria-label*='breadcrumb']"
        ]
        
        for pattern in additional_patterns:
            breadcrumbs = soup.select(pattern)
            if breadcrumbs:
                breadcrumb_selectors.append(pattern)
        
        return list(set(breadcrumb_selectors))  # Remove duplicates
    
    def _analyze_search_navigation(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Analyze search-related navigation elements."""
        search_nav = {}
        
        # Find search forms
        search_forms = soup.select("form[role='search'], form[class*='search'], .search-form")
        if search_forms:
            search_nav["search_form"] = self._generate_selector(search_forms[0])
        
        # Find search inputs
        search_inputs = soup.select("input[type='search'], input[name*='search'], input[placeholder*='search']")
        if search_inputs:
            search_nav["search_input"] = self._generate_selector(search_inputs[0])
        
        # Find search buttons
        search_buttons = soup.select("button[type='submit'], input[type='submit'], .search-button")
        if search_buttons:
            search_nav["search_button"] = self._generate_selector(search_buttons[0])
        
        # Find search suggestions/autocomplete
        suggestion_containers = soup.select("[class*='suggest'], [class*='autocomplete'], [class*='dropdown']")
        if suggestion_containers:
            search_nav["suggestions"] = self._generate_selector(suggestion_containers[0])
        
        return search_nav
    
    def _analyze_filter_navigation(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Analyze filter and sorting navigation elements."""
        filter_nav = {}
        
        # Find filter containers
        filter_containers = soup.select("[class*='filter'], [class*='facet'], [class*='refine']")
        if filter_containers:
            filter_nav["filter_containers"] = [self._generate_selector(container) for container in filter_containers]
        
        # Find sort options
        sort_selects = soup.select("select[name*='sort'], select[class*='sort']")
        if sort_selects:
            filter_nav["sort_selectors"] = [self._generate_selector(select) for select in sort_selects]
        
        # Find view options (grid/list)
        view_toggles = soup.select("[class*='view-'], [class*='display-'], [data-view]")
        if view_toggles:
            filter_nav["view_toggles"] = [self._generate_selector(toggle) for toggle in view_toggles]
        
        # Find price range filters
        price_filters = soup.select("input[name*='price'], input[class*='price'], .price-range")
        if price_filters:
            filter_nav["price_filters"] = [self._generate_selector(filter_elem) for filter_elem in price_filters]
        
        return filter_nav
    
    def _detect_dynamic_content(self, soup: BeautifulSoup) -> List[str]:
        """Detect indicators of dynamic/JavaScript-based content."""
        dynamic_selectors = []
        
        for pattern in self.dynamic_indicators:
            elements = soup.select(pattern)
            if elements:
                dynamic_selectors.extend([self._generate_selector(elem) for elem in elements[:3]])  # Limit to first 3
        
        # Look for AJAX loading indicators
        ajax_indicators = soup.select("[class*='loading'], [class*='spinner'], [class*='ajax']")
        if ajax_indicators:
            dynamic_selectors.extend([self._generate_selector(elem) for elem in ajax_indicators[:2]])
        
        # Look for lazy loading images
        lazy_images = soup.select("img[data-src], img[loading='lazy'], img[class*='lazy']")
        if lazy_images:
            dynamic_selectors.append("img[data-src], img[loading='lazy'], img[class*='lazy']")
        
        return list(set(dynamic_selectors))  # Remove duplicates
    
    def _analyze_accessibility_features(self, soup: BeautifulSoup) -> Dict[str, bool]:
        """Analyze accessibility features in navigation."""
        accessibility = {
            "has_skip_links": False,
            "has_aria_labels": False,
            "has_role_attributes": False,
            "has_keyboard_navigation": False,
            "has_focus_indicators": False
        }
        
        # Check for skip links
        skip_links = soup.select("a[href*='#main'], a[href*='#content'], .skip-link")
        accessibility["has_skip_links"] = bool(skip_links)
        
        # Check for ARIA labels
        aria_elements = soup.select("[aria-label], [aria-labelledby], [aria-describedby]")
        accessibility["has_aria_labels"] = bool(aria_elements)
        
        # Check for role attributes
        role_elements = soup.select("[role]")
        accessibility["has_role_attributes"] = bool(role_elements)
        
        # Check for keyboard navigation indicators
        tabindex_elements = soup.select("[tabindex]")
        accessibility["has_keyboard_navigation"] = bool(tabindex_elements)
        
        # Check for focus indicators (CSS-based, so limited detection)
        focus_elements = soup.select("[class*='focus'], [class*='outline']")
        accessibility["has_focus_indicators"] = bool(focus_elements)
        
        return accessibility
    
    def _generate_selector(self, element: Tag) -> str:
        """Generate a CSS selector for an element."""
        if not element:
            return ""
        
        # Try to use ID first
        if element.get("id"):
            return f"#{element['id']}"
        
        # Try to use unique class
        classes = element.get("class", [])
        if classes:
            for cls in classes:
                if cls and not any(common in cls.lower() for common in ["active", "current", "selected"]):
                    # Check if this class is unique enough
                    similar_elements = element.find_parent().select(f".{cls}") if element.find_parent() else []
                    if len(similar_elements) <= 3:  # Reasonably unique
                        return f".{cls}"
        
        # Fall back to tag name with position
        tag_name = element.name
        parent = element.find_parent()
        if parent:
            siblings = parent.find_all(tag_name)
            if len(siblings) > 1:
                index = siblings.index(element) + 1
                return f"{tag_name}:nth-of-type({index})"
        
        return tag_name or ""
