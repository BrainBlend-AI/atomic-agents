#!/usr/bin/env python3
"""
Demo: Adaptive Website Analysis - Conditional Logic Explanation

This demo shows how the atomic scraper tool intelligently switches between
standard and enhanced website analysis based on website complexity.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "atomic_scraper_tool"))

from analysis.adaptive_website_analyzer import AdaptiveWebsiteAnalyzer, AnalysisConfig


def demo_conditional_logic():
    """Demonstrate the conditional logic for choosing analysis depth."""

    print("🔄 Adaptive Website Analysis - Conditional Logic Demo")
    print("=" * 60)

    # Initialize analyzer with custom config
    config = AnalysisConfig(
        min_nav_elements_for_enhanced=3,
        min_page_complexity_score=0.5,
        detect_mega_menus=True,
        detect_mobile_navigation=True,
        detect_advanced_pagination=True,
    )

    analyzer = AdaptiveWebsiteAnalyzer(config)

    # Test cases with different complexity levels
    test_cases = [
        {
            "name": "Simple Blog Website",
            "html": """
            <html>
                <body>
                    <nav>
                        <a href="/">Home</a>
                        <a href="/about">About</a>
                        <a href="/contact">Contact</a>
                    </nav>
                    <main>
                        <article>
                            <h1>Blog Post Title</h1>
                            <p>Simple blog content...</p>
                        </article>
                    </main>
                </body>
            </html>
            """,
            "expected": "standard",
        },
        {
            "name": "E-commerce with Mega Menu",
            "html": """
            <html>
                <body>
                    <header>
                        <nav class="main-nav">
                            <ul>
                                <li><a href="/">Home</a></li>
                                <li class="dropdown">
                                    <a href="/products">Products</a>
                                    <div class="mega-menu">
                                        <div class="col">
                                            <h3>Electronics</h3>
                                            <a href="/laptops">Laptops</a>
                                            <a href="/phones">Phones</a>
                                        </div>
                                        <div class="col">
                                            <h3>Clothing</h3>
                                            <a href="/shirts">Shirts</a>
                                        </div>
                                    </div>
                                </li>
                                <li><a href="/services">Services</a></li>
                            </ul>
                        </nav>
                        <button class="hamburger menu-toggle">☰</button>
                        <nav class="mobile-menu">
                            <ul>
                                <li><a href="/">Home</a></li>
                                <li><a href="/products">Products</a></li>
                            </ul>
                        </nav>
                    </header>
                    <main>
                        <div class="filters">
                            <select name="sort">
                                <option>Sort by Price</option>
                            </select>
                        </div>
                        <div class="pagination">
                            <a href="?page=1">1</a>
                            <a href="?page=2">2</a>
                        </div>
                    </main>
                </body>
            </html>
            """,
            "expected": "enhanced",
        },
        {
            "name": "News Site with Complex Navigation",
            "html": """
            <html>
                <body>
                    <header>
                        <nav class="primary-nav" role="navigation">
                            <ul>
                                <li><a href="/">Home</a></li>
                                <li>
                                    <a href="/news">News</a>
                                    <ul class="submenu">
                                        <li><a href="/politics">Politics</a></li>
                                        <li><a href="/sports">Sports</a></li>
                                        <li><a href="/tech">Technology</a></li>
                                    </ul>
                                </li>
                                <li><a href="/opinion">Opinion</a></li>
                            </ul>
                        </nav>
                        <nav class="secondary-nav">
                            <a href="/breaking">Breaking</a>
                            <a href="/trending">Trending</a>
                        </nav>
                        <form class="search-form">
                            <input type="search" name="q">
                            <button type="submit">Search</button>
                        </form>
                    </header>
                    <nav class="breadcrumb">
                        <a href="/">Home</a> > <a href="/news">News</a> > <span>Article</span>
                    </nav>
                    <main>
                        <article>
                            <div class="tags">
                                <a href="/tag/politics">Politics</a>
                                <a href="/tag/election">Election</a>
                            </div>
                            <div class="social-share">
                                <a href="#" class="share-twitter">Twitter</a>
                                <a href="#" class="share-facebook">Facebook</a>
                            </div>
                        </article>
                        <div class="related-articles">
                            <h3>Related</h3>
                            <a href="/related-1">Related Article 1</a>
                        </div>
                        <div class="infinite-scroll" data-infinite="true">
                            Loading more articles...
                        </div>
                    </main>
                </body>
            </html>
            """,
            "expected": "enhanced",
        },
    ]

    print(f"\n📊 Testing {len(test_cases)} websites with different complexity levels:")
    print("-" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("   " + "=" * (len(test_case["name"]) + 3))

        # Analyze the website
        result = analyzer.analyze_website(test_case["html"], f"https://example{i}.com")

        # Show decision factors
        print(f"   🔍 Complexity Score: {result.complexity_score:.3f}")
        print(f"   📊 Navigation Complexity: {result.navigation_complexity}")
        print(f"   ⚙️  Analysis Type: {result.analysis_type}")
        print(f"   ⏱️  Analysis Time: {result.analysis_time:.3f}s")

        # Show why this decision was made
        print("   🤔 Decision Logic:")

        if result.analysis_type == "enhanced":
            print("      ✅ Enhanced analysis triggered because:")
            if result.complexity_score >= config.min_page_complexity_score:
                print(
                    f"         • Complexity score ({result.complexity_score:.3f}) >= threshold ({config.min_page_complexity_score})"
                )

            if result.enhanced_analysis:
                features = result.triggered_features
                if features:
                    print(f"         • Complex features detected: {', '.join(features)}")
        else:
            print("      ⚡ Standard analysis used because:")
            print(
                f"         • Complexity score ({result.complexity_score:.3f}) < threshold ({config.min_page_complexity_score})"
            )
            print("         • No complex navigation features detected")

        # Show what was detected
        if result.has_enhanced_analysis:
            enhanced = result.enhanced_analysis
            print("   🎯 Enhanced Features Detected:")

            if enhanced.main_navigation:
                nav_count = len(enhanced.main_navigation)
                print(f"      • {nav_count} navigation hierarchies")

            if enhanced.mega_menus:
                mega_count = len(enhanced.mega_menus)
                print(f"      • {mega_count} mega menus")

            if enhanced.mobile_navigation:
                print("      • Mobile navigation (hamburger menu)")

            if enhanced.advanced_pagination:
                pagination_type = enhanced.advanced_pagination.pagination_type
                print(f"      • {pagination_type.replace('_', ' ').title()} pagination")

            if enhanced.contextual_navigation:
                contextual = enhanced.contextual_navigation
                if contextual.related_links:
                    print(f"      • {len(contextual.related_links)} related content links")
                if contextual.social_sharing:
                    print(f"      • {len(contextual.social_sharing)} social sharing buttons")

            if enhanced.search_navigation:
                print(f"      • Search functionality ({len(enhanced.search_navigation)} elements)")

            if enhanced.filter_navigation:
                print(f"      • Filtering options ({len(enhanced.filter_navigation)} types)")

        # Verify expectation
        expected = test_case["expected"]
        actual = result.analysis_type
        status = "✅ CORRECT" if actual == expected else "❌ UNEXPECTED"
        print(f"   📋 Expected: {expected}, Got: {actual} {status}")

    print("\n" + "=" * 60)
    print("🧠 How the Conditional Logic Works:")
    print("=" * 60)

    print(
        """
The adaptive analyzer uses a multi-factor decision system:

1. **Complexity Score Calculation (0.0 - 1.0):**
   • Navigation elements count (0.0 - 0.3)
   • Menu nesting depth (0.0 - 0.2)
   • Dropdown/submenu indicators (0.0 - 0.2)
   • Mobile navigation elements (0.0 - 0.1)
   • Pagination complexity (0.0 - 0.1)
   • Dynamic content indicators (0.0 - 0.1)

2. **Decision Triggers:**
   • Complexity score >= threshold (default: 0.6)
   • Navigation element count >= minimum (default: 5)
   • Presence of complex features (mega menus, mobile nav, etc.)
   • User override (force_enhanced=True/False)

3. **Analysis Types:**
   • **Standard**: Basic navigation analysis (fast, lightweight)
   • **Enhanced**: Deep navigation analysis (comprehensive, slower)

4. **Backward Compatibility:**
   • All existing code continues to work unchanged
   • Enhanced features are additive, not breaking
   • Graceful fallback to standard analysis on errors
    """
    )

    print("\n🎯 Integration Points:")
    print("-" * 30)
    print(
        """
The atomic scraper tool integrates this logic at key points:

1. **Scraper Planning Agent**:
   • Uses adaptive analysis in _analyze_target_website()
   • Generates enhanced strategies for complex sites

2. **Main Scraper Tool**:
   • Can optionally use adaptive analysis for strategy refinement
   • Leverages enhanced navigation data for better scraping

3. **Configuration**:
   • Tunable thresholds for different use cases
   • Can be disabled/forced via configuration
   • Caching for performance optimization
    """
    )

    print("\n✨ Benefits:")
    print("-" * 15)
    print(
        """
• **Automatic**: No code changes needed for basic usage
• **Intelligent**: Adapts to website complexity automatically
• **Performance**: Only uses enhanced analysis when beneficial
• **Comprehensive**: Detects modern navigation patterns
• **Backward Compatible**: Existing code continues to work
• **Configurable**: Tunable for different requirements
    """
    )


if __name__ == "__main__":
    demo_conditional_logic()
