#!/usr/bin/env python3
"""
Simple demo of the enhanced navigation analyzer.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "atomic_scraper_tool"))

from analysis.enhanced_navigation_analyzer import EnhancedNavigationAnalyzer


def demo_enhanced_navigation():
    """Demonstrate the enhanced navigation analyzer capabilities."""

    # Complex HTML example
    complex_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complex Navigation Demo</title>
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

    print("🔍 Enhanced Navigation Analysis Demo")
    print("=" * 50)

    # Initialize analyzer
    analyzer = EnhancedNavigationAnalyzer()

    # Analyze the HTML
    analysis = analyzer.analyze_navigation(complex_html, "https://example-ecommerce.com/products")

    # Display results
    print(f"\n📋 Analysis Results for: {analysis.url}")
    print("-" * 40)

    # Hierarchical Navigation
    print(f"\n🏗️  Hierarchical Navigation: {len(analysis.main_navigation)} levels detected")
    for i, nav in enumerate(analysis.main_navigation):
        print(f"  Level {nav.level}: {len(nav.items)} items")
        if nav.has_submenu:
            print(f"    - Has submenu (trigger: {nav.submenu_trigger})")

        # Show sample items
        sample_items = [item["text"] for item in nav.items[:3]]
        if sample_items:
            print(f"    - Items: {', '.join(sample_items)}")

    # Mega Menus
    print(f"\n🎯 Mega Menus: {len(analysis.mega_menus)} detected")
    for i, menu in enumerate(analysis.mega_menus):
        print(f"  Menu {i + 1}:")
        print(f"    - Columns: {len(menu.columns)}")
        print(f"    - Sections: {len(menu.sections)}")
        print(f"    - Activation: {menu.activation_method}")

        section_titles = [section.get("title", "") for section in menu.sections if section.get("title")]
        if section_titles:
            print(f"    - Section titles: {', '.join(section_titles)}")

    # Mobile Navigation
    mobile = analysis.mobile_navigation
    print("\n📱 Mobile Navigation:")
    if mobile:
        print(f"  - Hamburger menu: {'✅' if mobile.hamburger_selector else '❌'}")
        print(f"  - Mobile menu: {'✅' if mobile.mobile_menu_selector else '❌'}")
        print(f"  - Overlay: {'✅' if mobile.overlay_selector else '❌'}")
        print(f"  - Slide direction: {mobile.slide_direction or 'Not detected'}")
        print(f"  - Accordion style: {'✅' if mobile.has_accordion else '❌'}")
    else:
        print("  - No mobile navigation detected")

    # Pagination
    pagination = analysis.advanced_pagination
    print("\n📄 Advanced Pagination:")
    if pagination:
        print(f"  - Type: {pagination.pagination_type}")
        print(f"  - Current page: {pagination.current_page or 'Not detected'}")
        print(f"  - Total pages: {pagination.total_pages or 'Not detected'}")
        print(f"  - Page size selector: {'✅' if pagination.has_page_size_selector else '❌'}")
    else:
        print("  - No pagination detected")

    # Contextual Navigation
    contextual = analysis.contextual_navigation
    print("\n🔗 Contextual Navigation:")
    if contextual:
        print(f"  - Tags: {'✅' if contextual.tags_selector else '❌'}")
        print(f"  - Categories: {'✅' if contextual.categories_selector else '❌'}")
        print(f"  - Related links: {len(contextual.related_links)}")
        print(f"  - Social sharing: {len(contextual.social_sharing)}")
        print(f"  - Author links: {len(contextual.author_links)}")
    else:
        print("  - No contextual navigation detected")

    # Search & Filters
    print("\n🔍 Search & Filter Navigation:")
    print(f"  - Search elements: {len(analysis.search_navigation)}")
    for key, value in analysis.search_navigation.items():
        print(f"    - {key}: {value}")

    print(f"  - Filter types: {len(analysis.filter_navigation)}")
    for key, values in analysis.filter_navigation.items():
        count = len(values) if isinstance(values, list) else 1
        print(f"    - {key}: {count} elements")

    # Breadcrumbs
    print(f"\n🍞 Breadcrumb Variations: {len(analysis.breadcrumb_variations)}")
    for breadcrumb in analysis.breadcrumb_variations:
        print(f"  - {breadcrumb}")

    # Dynamic Content
    print(f"\n⚡ Dynamic Content Indicators: {len(analysis.dynamic_content_indicators)}")
    for indicator in analysis.dynamic_content_indicators[:3]:  # Show first 3
        print(f"  - {indicator}")

    # Accessibility
    print("\n♿ Accessibility Features:")
    accessibility = analysis.accessibility_features
    accessible_count = sum(accessibility.values())
    print(f"  - Features detected: {accessible_count}/5")
    for feature, present in accessibility.items():
        feature_name = feature.replace("has_", "").replace("_", " ").title()
        print(f"    - {feature_name}: {'✅' if present else '❌'}")

    # Scraping Strategy Recommendations
    print("\n🎯 Scraping Strategy Recommendations:")

    if analysis.mega_menus:
        print("  ✅ Mega menus detected - consider scraping category hierarchies")

    if pagination and pagination.pagination_type == "numbered":
        total = pagination.total_pages or "unknown"
        print(f"  ✅ Numbered pagination - can scrape up to {total} pages")
    elif pagination and pagination.pagination_type == "infinite_scroll":
        print("  ✅ Infinite scroll detected - use scroll-based scraping strategy")

    if analysis.filter_navigation:
        print("  ✅ Filters detected - can scrape filtered results for comprehensive data")

    if contextual and contextual.tags_selector:
        print("  ✅ Tags detected - can scrape related content via tag navigation")

    if analysis.dynamic_content_indicators:
        print("  ⚠️  Dynamic content detected - may need JavaScript rendering")

    if mobile:
        print("  📱 Mobile navigation detected - consider mobile-specific scraping")

    print("\n✨ Analysis complete! The enhanced navigation analyzer detected:")
    print(f"   • {len(analysis.main_navigation)} navigation hierarchies")
    print(f"   • {len(analysis.mega_menus)} mega menus")
    print(f"   • {'Mobile navigation' if mobile else 'No mobile navigation'}")
    print(f"   • {pagination.pagination_type if pagination else 'No pagination'}")
    print(f"   • {len(analysis.breadcrumb_variations)} breadcrumb variations")
    print(f"   • {accessible_count}/5 accessibility features")


if __name__ == "__main__":
    demo_enhanced_navigation()
