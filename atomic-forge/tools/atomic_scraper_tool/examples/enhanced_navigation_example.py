"""
Example demonstrating the enhanced navigation analyzer for complex navigation detection.

This example shows how to use the EnhancedNavigationAnalyzer to detect and analyze
complex navigation patterns including hierarchical menus, mega menus, mobile navigation,
advanced pagination, and contextual navigation elements.
"""

import asyncio
import json
from typing import Dict, Any
from atomic_scraper_tool.analysis.enhanced_navigation_analyzer import EnhancedNavigationAnalyzer
from atomic_scraper_tool.analysis.website_analyzer import WebsiteAnalyzer


def analyze_navigation_patterns(html_content: str, url: str) -> Dict[str, Any]:
    """
    Analyze navigation patterns using both standard and enhanced analyzers.
    
    Args:
        html_content: HTML content to analyze
        url: URL of the website
        
    Returns:
        Dictionary containing comprehensive navigation analysis
    """
    # Standard analysis
    standard_analyzer = WebsiteAnalyzer()
    standard_analysis = standard_analyzer.analyze_website(html_content, url)
    
    # Enhanced analysis
    enhanced_analyzer = EnhancedNavigationAnalyzer()
    enhanced_analysis = enhanced_analyzer.analyze_navigation(html_content, url)
    
    return {
        "url": url,
        "standard_navigation": {
            "main_nav_selector": standard_analysis.navigation_info.main_nav_selector,
            "breadcrumb_selector": standard_analysis.navigation_info.breadcrumb_selector,
            "menu_items": standard_analysis.navigation_info.menu_items,
        },
        "enhanced_navigation": {
            "hierarchical_navigation": [
                {
                    "level": nav.level,
                    "items_count": len(nav.items),
                    "has_submenu": nav.has_submenu,
                    "submenu_trigger": nav.submenu_trigger,
                    "sample_items": [item["text"] for item in nav.items[:3]]  # First 3 items
                }
                for nav in enhanced_analysis.main_navigation
            ],
            "mega_menus": [
                {
                    "trigger_selector": menu.trigger_selector,
                    "columns_count": len(menu.columns),
                    "sections_count": len(menu.sections),
                    "activation_method": menu.activation_method,
                    "section_titles": [section.get("title", "") for section in menu.sections]
                }
                for menu in enhanced_analysis.mega_menus
            ],
            "mobile_navigation": {
                "has_hamburger": enhanced_analysis.mobile_navigation.hamburger_selector is not None if enhanced_analysis.mobile_navigation else False,
                "slide_direction": enhanced_analysis.mobile_navigation.slide_direction if enhanced_analysis.mobile_navigation else None,
                "has_overlay": enhanced_analysis.mobile_navigation.overlay_selector is not None if enhanced_analysis.mobile_navigation else False,
                "has_accordion": enhanced_analysis.mobile_navigation.has_accordion if enhanced_analysis.mobile_navigation else False,
            },
            "pagination": {
                "type": enhanced_analysis.advanced_pagination.pagination_type if enhanced_analysis.advanced_pagination else None,
                "current_page": enhanced_analysis.advanced_pagination.current_page if enhanced_analysis.advanced_pagination else None,
                "total_pages": enhanced_analysis.advanced_pagination.total_pages if enhanced_analysis.advanced_pagination else None,
                "has_page_size_selector": enhanced_analysis.advanced_pagination.has_page_size_selector if enhanced_analysis.advanced_pagination else False,
            },
            "contextual_navigation": {
                "has_tags": enhanced_analysis.contextual_navigation.tags_selector is not None if enhanced_analysis.contextual_navigation else False,
                "has_categories": enhanced_analysis.contextual_navigation.categories_selector is not None if enhanced_analysis.contextual_navigation else False,
                "related_links_count": len(enhanced_analysis.contextual_navigation.related_links) if enhanced_analysis.contextual_navigation else 0,
                "social_sharing_count": len(enhanced_analysis.contextual_navigation.social_sharing) if enhanced_analysis.contextual_navigation else 0,
            },
            "search_navigation": enhanced_analysis.search_navigation,
            "filter_navigation": {
                key: len(value) if isinstance(value, list) else 1
                for key, value in enhanced_analysis.filter_navigation.items()
            },
            "breadcrumb_variations": len(enhanced_analysis.breadcrumb_variations),
            "dynamic_content_indicators": len(enhanced_analysis.dynamic_content_indicators),
            "accessibility_features": enhanced_analysis.accessibility_features,
        }
    }


def print_navigation_summary(analysis: Dict[str, Any]):
    """Print a human-readable summary of navigation analysis."""
    print(f"\n🔍 Navigation Analysis for: {analysis['url']}")
    print("=" * 60)
    
    # Standard navigation
    standard = analysis["standard_navigation"]
    print(f"\n📋 Standard Navigation:")
    print(f"  • Main nav selector: {standard['main_nav_selector'] or 'Not found'}")
    print(f"  • Breadcrumb selector: {standard['breadcrumb_selector'] or 'Not found'}")
    print(f"  • Menu items: {len(standard['menu_items'])} items")
    
    # Enhanced navigation
    enhanced = analysis["enhanced_navigation"]
    
    # Hierarchical navigation
    hierarchical = enhanced["hierarchical_navigation"]
    if hierarchical:
        print(f"\n🏗️  Hierarchical Navigation:")
        for i, nav in enumerate(hierarchical):
            print(f"  • Level {nav['level']}: {nav['items_count']} items")
            if nav['has_submenu']:
                print(f"    - Has submenu (trigger: {nav['submenu_trigger']})")
            if nav['sample_items']:
                print(f"    - Sample items: {', '.join(nav['sample_items'])}")
    
    # Mega menus
    mega_menus = enhanced["mega_menus"]
    if mega_menus:
        print(f"\n🎯 Mega Menus: {len(mega_menus)} found")
        for i, menu in enumerate(mega_menus):
            print(f"  • Menu {i+1}: {menu['columns_count']} columns, {menu['sections_count']} sections")
            print(f"    - Activation: {menu['activation_method']}")
            if menu['section_titles']:
                print(f"    - Sections: {', '.join(menu['section_titles'])}")
    
    # Mobile navigation
    mobile = enhanced["mobile_navigation"]
    print(f"\n📱 Mobile Navigation:")
    print(f"  • Hamburger menu: {'✅' if mobile['has_hamburger'] else '❌'}")
    print(f"  • Slide direction: {mobile['slide_direction'] or 'Not detected'}")
    print(f"  • Overlay: {'✅' if mobile['has_overlay'] else '❌'}")
    print(f"  • Accordion style: {'✅' if mobile['has_accordion'] else '❌'}")
    
    # Pagination
    pagination = enhanced["pagination"]
    if pagination["type"]:
        print(f"\n📄 Pagination:")
        print(f"  • Type: {pagination['type']}")
        if pagination["current_page"]:
            print(f"  • Current page: {pagination['current_page']}")
        if pagination["total_pages"]:
            print(f"  • Total pages: {pagination['total_pages']}")
        print(f"  • Page size selector: {'✅' if pagination['has_page_size_selector'] else '❌'}")
    
    # Contextual navigation
    contextual = enhanced["contextual_navigation"]
    print(f"\n🔗 Contextual Navigation:")
    print(f"  • Tags: {'✅' if contextual['has_tags'] else '❌'}")
    print(f"  • Categories: {'✅' if contextual['has_categories'] else '❌'}")
    print(f"  • Related links: {contextual['related_links_count']}")
    print(f"  • Social sharing: {contextual['social_sharing_count']}")
    
    # Search and filters
    search = enhanced["search_navigation"]
    filters = enhanced["filter_navigation"]
    print(f"\n🔍 Search & Filters:")
    print(f"  • Search elements: {len(search)}")
    print(f"  • Filter types: {len(filters)}")
    
    # Additional features
    print(f"\n✨ Additional Features:")
    print(f"  • Breadcrumb variations: {enhanced['breadcrumb_variations']}")
    print(f"  • Dynamic content indicators: {enhanced['dynamic_content_indicators']}")
    
    # Accessibility
    accessibility = enhanced["accessibility_features"]
    accessible_features = sum(accessibility.values())
    print(f"  • Accessibility features: {accessible_features}/5")
    for feature, present in accessibility.items():
        print(f"    - {feature.replace('has_', '').replace('_', ' ').title()}: {'✅' if present else '❌'}")


def main():
    """Main example function."""
    # Example HTML with complex navigation
    complex_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complex Navigation Example</title>
    </head>
    <body>
        <header>
            <nav class="main-nav" role="navigation" aria-label="Main navigation">
                <a href="#main-content" class="skip-link">Skip to main content</a>
                <button class="hamburger menu-toggle" aria-label="Toggle menu">☰</button>
                
                <ul class="nav-list">
                    <li class="nav-item">
                        <a href="/" tabindex="0">Home</a>
                    </li>
                    <li class="nav-item dropdown">
                        <a href="/products" data-toggle="dropdown">Products</a>
                        <div class="mega-menu">
                            <div class="col">
                                <h3>Electronics</h3>
                                <a href="/laptops">Laptops</a>
                                <a href="/phones">Phones</a>
                                <a href="/tablets">Tablets</a>
                            </div>
                            <div class="col">
                                <h3>Clothing</h3>
                                <a href="/shirts">Shirts</a>
                                <a href="/pants">Pants</a>
                                <a href="/shoes">Shoes</a>
                            </div>
                        </div>
                    </li>
                    <li class="nav-item">
                        <a href="/services">Services</a>
                        <ul class="submenu">
                            <li><a href="/consulting">Consulting</a></li>
                            <li><a href="/support">Support</a></li>
                        </ul>
                    </li>
                </ul>
                
                <form role="search" class="search-form">
                    <input type="search" name="q" placeholder="Search products..." aria-label="Search">
                    <button type="submit" class="search-button">Search</button>
                </form>
            </nav>
            
            <nav class="mobile-menu slide-left" style="display:none;">
                <ul>
                    <li><a href="/">Home</a></li>
                    <li class="has-submenu">
                        <a href="/products">Products</a>
                        <ul class="submenu-mobile">
                            <li><a href="/laptops">Laptops</a></li>
                            <li><a href="/phones">Phones</a></li>
                        </ul>
                    </li>
                </ul>
            </nav>
            <div class="overlay" style="display:none;"></div>
        </header>
        
        <nav aria-label="breadcrumb" class="breadcrumb-nav">
            <ol class="breadcrumb">
                <li><a href="/">Home</a></li>
                <li><a href="/category">Category</a></li>
                <li class="active">Current Page</li>
            </ol>
        </nav>
        
        <main id="main-content">
            <div class="filters">
                <select name="sort_by" class="sort-select">
                    <option value="price">Sort by Price</option>
                    <option value="name">Sort by Name</option>
                </select>
                
                <div class="filter-group">
                    <h3>Price Range</h3>
                    <input type="range" name="price_min" class="price-filter">
                </div>
                
                <div class="view-toggles">
                    <button data-view="grid" class="view-grid active">Grid</button>
                    <button data-view="list" class="view-list">List</button>
                </div>
            </div>
            
            <div class="content">
                <article>
                    <h1>Sample Article</h1>
                    <div class="tags">
                        <a href="/tag/python" class="tag">Python</a>
                        <a href="/tag/web" class="tag">Web Development</a>
                    </div>
                    <div class="social-share">
                        <a href="#" class="share-twitter">Share on Twitter</a>
                        <a href="#" class="share-facebook">Share on Facebook</a>
                    </div>
                </article>
                
                <div class="related-posts">
                    <h3>Related Articles</h3>
                    <a href="/related-1">Related Article 1</a>
                    <a href="/related-2">Related Article 2</a>
                </div>
            </div>
            
            <div class="pagination">
                <a href="?page=1" class="first">First</a>
                <a href="?page=2" class="prev">Previous</a>
                <span class="current">3</span>
                <a href="?page=4">4</a>
                <a href="?page=5">5</a>
                <a href="?page=4" class="next">Next</a>
                <a href="?page=10" class="last">Last</a>
                <select class="per-page">
                    <option value="10">10 per page</option>
                    <option value="25">25 per page</option>
                </select>
            </div>
        </main>
        
        <footer>
            <nav class="footer-nav">
                <a href="/privacy">Privacy</a>
                <a href="/terms">Terms</a>
                <a href="/contact">Contact</a>
            </nav>
        </footer>
    </body>
    </html>
    """
    
    # Analyze the navigation
    analysis = analyze_navigation_patterns(complex_html, "https://example-ecommerce.com/products")
    
    # Print summary
    print_navigation_summary(analysis)
    
    # Save detailed analysis to JSON
    with open("navigation_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to navigation_analysis.json")
    
    # Example of using the analysis for scraping strategy
    print(f"\n🎯 Scraping Strategy Recommendations:")
    enhanced = analysis["enhanced_navigation"]
    
    if enhanced["mega_menus"]:
        print("  • Detected mega menus - consider scraping category hierarchies")
    
    if enhanced["pagination"]["type"] == "numbered":
        print(f"  • Numbered pagination detected - can scrape up to {enhanced['pagination']['total_pages']} pages")
    elif enhanced["pagination"]["type"] == "infinite_scroll":
        print("  • Infinite scroll detected - use scroll-based scraping strategy")
    
    if enhanced["filter_navigation"]:
        print("  • Filters detected - can scrape filtered results for comprehensive data")
    
    if enhanced["contextual_navigation"]["has_tags"]:
        print("  • Tags detected - can scrape related content via tag navigation")
    
    if enhanced["dynamic_content_indicators"] > 0:
        print("  • Dynamic content detected - may need JavaScript rendering")


if __name__ == "__main__":
    main()
