"""
Adaptive Website Analyzer - Intelligently chooses between standard and enhanced analysis.

This analyzer automatically determines when to use the enhanced navigation analyzer
based on website complexity and user requirements, providing seamless integration
with existing code while offering advanced capabilities when needed.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup

from atomic_scraper_tool.analysis.website_analyzer import WebsiteAnalyzer, WebsiteStructureAnalysis
from atomic_scraper_tool.analysis.enhanced_navigation_analyzer import EnhancedNavigationAnalyzer, EnhancedNavigationAnalysis


logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for adaptive website analysis."""

    # Thresholds for triggering enhanced analysis
    min_nav_elements_for_enhanced: int = 5  # Minimum nav elements to trigger enhanced analysis
    min_page_complexity_score: float = 0.6  # Minimum complexity score (0.0-1.0)

    # Feature detection flags
    detect_mega_menus: bool = True
    detect_mobile_navigation: bool = True
    detect_advanced_pagination: bool = True
    detect_contextual_navigation: bool = True
    detect_accessibility_features: bool = True

    # Performance settings
    max_analysis_time: float = 10.0  # Maximum time to spend on analysis (seconds)
    enable_caching: bool = True  # Cache analysis results

    # User preferences
    force_enhanced_analysis: bool = False  # Always use enhanced analysis
    disable_enhanced_analysis: bool = False  # Never use enhanced analysis


@dataclass
class AdaptiveAnalysisResult:
    """Combined result from adaptive website analysis."""

    # Standard analysis (always present)
    standard_analysis: WebsiteStructureAnalysis

    # Enhanced analysis (present when triggered)
    enhanced_analysis: Optional[EnhancedNavigationAnalysis] = None

    # Analysis metadata
    analysis_type: str = "standard"  # "standard", "enhanced", or "hybrid"
    complexity_score: float = 0.0
    analysis_time: float = 0.0
    triggered_features: list = field(default_factory=list)

    # Convenience properties
    @property
    def has_enhanced_analysis(self) -> bool:
        """Check if enhanced analysis was performed."""
        return self.enhanced_analysis is not None

    @property
    def navigation_complexity(self) -> str:
        """Get navigation complexity level."""
        if self.complexity_score < 0.3:
            return "simple"
        elif self.complexity_score < 0.7:
            return "moderate"
        else:
            return "complex"


class AdaptiveWebsiteAnalyzer:
    """
    Adaptive website analyzer that intelligently chooses analysis depth.

    This analyzer maintains backward compatibility with the existing WebsiteAnalyzer
    while providing enhanced capabilities when complex navigation is detected.
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the adaptive analyzer.

        Args:
            config: Analysis configuration (uses defaults if None)
        """
        self.config = config or AnalysisConfig()
        self.standard_analyzer = WebsiteAnalyzer()
        self.enhanced_analyzer = EnhancedNavigationAnalyzer()

        # Analysis cache for performance
        self._analysis_cache: Dict[str, AdaptiveAnalysisResult] = {}

        logger.info(f"AdaptiveWebsiteAnalyzer initialized with config: {self.config}")

    def analyze_website(self, html_content: str, url: str, force_enhanced: Optional[bool] = None) -> AdaptiveAnalysisResult:
        """
        Analyze website with adaptive depth selection.

        Args:
            html_content: HTML content to analyze
            url: URL of the website
            force_enhanced: Override automatic detection (True/False/None for auto)

        Returns:
            AdaptiveAnalysisResult with appropriate analysis depth
        """
        import time

        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(html_content, url)
        if self.config.enable_caching and cache_key in self._analysis_cache:
            cached_result = self._analysis_cache[cache_key]
            logger.debug(f"Returning cached analysis for {url}")
            return cached_result

        try:
            # Always perform standard analysis first
            standard_analysis = self.standard_analyzer.analyze_website(html_content, url)

            # Calculate website complexity
            complexity_score = self._calculate_complexity_score(html_content, standard_analysis)

            # Determine if enhanced analysis is needed
            should_use_enhanced = self._should_use_enhanced_analysis(
                html_content, standard_analysis, complexity_score, force_enhanced
            )

            # Create result with standard analysis
            result = AdaptiveAnalysisResult(
                standard_analysis=standard_analysis, complexity_score=complexity_score, analysis_time=time.time() - start_time
            )

            if should_use_enhanced:
                logger.info(f"Performing enhanced navigation analysis for {url} (complexity: {complexity_score:.2f})")

                # Perform enhanced analysis
                enhanced_analysis = self.enhanced_analyzer.analyze_navigation(html_content, url)
                result.enhanced_analysis = enhanced_analysis
                result.analysis_type = "enhanced"
                result.triggered_features = self._identify_triggered_features(enhanced_analysis)

                logger.info(f"Enhanced analysis completed. Features detected: {', '.join(result.triggered_features)}")
            else:
                result.analysis_type = "standard"
                logger.debug(f"Using standard analysis for {url} (complexity: {complexity_score:.2f})")

            # Update timing
            result.analysis_time = time.time() - start_time

            # Cache result
            if self.config.enable_caching:
                self._analysis_cache[cache_key] = result

            logger.info(f"Website analysis completed in {result.analysis_time:.2f}s using {result.analysis_type} analysis")
            return result

        except Exception as e:
            logger.error(f"Error during adaptive website analysis: {e}")
            # Fallback to standard analysis only
            result = AdaptiveAnalysisResult(
                standard_analysis=standard_analysis,
                complexity_score=0.0,
                analysis_time=time.time() - start_time,
                analysis_type="standard",
            )
            return result

    def _calculate_complexity_score(self, html_content: str, standard_analysis: WebsiteStructureAnalysis) -> float:
        """
        Calculate website navigation complexity score (0.0 to 1.0).

        Args:
            html_content: HTML content
            standard_analysis: Standard website analysis

        Returns:
            Complexity score between 0.0 (simple) and 1.0 (very complex)
        """
        soup = BeautifulSoup(html_content, "html.parser")
        score = 0.0

        # Navigation element count (0.0 - 0.3)
        nav_elements = len(soup.select("nav, .nav, .menu, .navigation, [role='navigation']"))
        nav_score = min(nav_elements / 10.0, 0.3)  # Cap at 0.3
        score += nav_score

        # Menu depth (0.0 - 0.2)
        max_depth = self._calculate_menu_depth(soup)
        depth_score = min(max_depth / 5.0, 0.2)  # Cap at 0.2
        score += depth_score

        # Dropdown/submenu indicators (0.0 - 0.2)
        dropdown_elements = len(soup.select("[class*='dropdown'], [class*='submenu'], [class*='mega']"))
        dropdown_score = min(dropdown_elements / 5.0, 0.2)  # Cap at 0.2
        score += dropdown_score

        # Mobile navigation indicators (0.0 - 0.1)
        mobile_elements = len(soup.select(".hamburger, .menu-toggle, .mobile-menu, [class*='mobile']"))
        mobile_score = min(mobile_elements / 3.0, 0.1)  # Cap at 0.1
        score += mobile_score

        # Pagination complexity (0.0 - 0.1)
        pagination_elements = len(soup.select(".pagination, .pager, [class*='page'], .infinite-scroll"))
        pagination_score = min(pagination_elements / 3.0, 0.1)  # Cap at 0.1
        score += pagination_score

        # Dynamic content indicators (0.0 - 0.1)
        dynamic_elements = len(soup.select("[data-toggle], [onclick], [class*='ajax'], [class*='dynamic']"))
        dynamic_score = min(dynamic_elements / 10.0, 0.1)  # Cap at 0.1
        score += dynamic_score

        return min(score, 1.0)  # Ensure score doesn't exceed 1.0

    def _calculate_menu_depth(self, soup: BeautifulSoup) -> int:
        """Calculate maximum menu nesting depth."""
        max_depth = 0

        for nav in soup.select("nav, .nav, .menu"):
            depth = self._get_nested_list_depth(nav)
            max_depth = max(max_depth, depth)

        return max_depth

    def _get_nested_list_depth(self, element, current_depth: int = 0) -> int:
        """Recursively calculate nested list depth."""
        max_depth = current_depth

        for child_list in element.find_all(["ul", "ol"], recursive=False):
            child_depth = self._get_nested_list_depth(child_list, current_depth + 1)
            max_depth = max(max_depth, child_depth)

        return max_depth

    def _should_use_enhanced_analysis(
        self,
        html_content: str,
        standard_analysis: WebsiteStructureAnalysis,
        complexity_score: float,
        force_enhanced: Optional[bool],
    ) -> bool:
        """
        Determine if enhanced analysis should be used.

        Args:
            html_content: HTML content
            standard_analysis: Standard analysis results
            complexity_score: Calculated complexity score
            force_enhanced: User override (True/False/None)

        Returns:
            True if enhanced analysis should be used
        """
        # Check user overrides first
        if force_enhanced is True or self.config.force_enhanced_analysis:
            return True

        if force_enhanced is False or self.config.disable_enhanced_analysis:
            return False

        # Check complexity threshold
        if complexity_score >= self.config.min_page_complexity_score:
            return True

        # Check navigation element count
        soup = BeautifulSoup(html_content, "html.parser")
        nav_count = len(soup.select("nav, .nav, .menu, .navigation, [role='navigation']"))
        if nav_count >= self.config.min_nav_elements_for_enhanced:
            return True

        # Check for specific complex features
        complex_features = [
            # Mega menus
            soup.select(".mega-menu, [class*='mega'], .dropdown-mega"),
            # Mobile navigation
            soup.select(".hamburger, .menu-toggle, .mobile-menu"),
            # Advanced pagination
            soup.select(".infinite-scroll, [data-infinite], .load-more"),
            # Dynamic content
            soup.select("[data-toggle], [data-target], [onclick]"),
        ]

        # If any complex feature has multiple elements, use enhanced analysis
        for feature_elements in complex_features:
            if len(feature_elements) >= 2:
                return True

        return False

    def _identify_triggered_features(self, enhanced_analysis: EnhancedNavigationAnalysis) -> list:
        """Identify which enhanced features were detected."""
        features = []

        if enhanced_analysis.main_navigation:
            features.append("hierarchical_navigation")

        if enhanced_analysis.mega_menus:
            features.append("mega_menus")

        if enhanced_analysis.mobile_navigation:
            features.append("mobile_navigation")

        if enhanced_analysis.advanced_pagination:
            features.append("advanced_pagination")

        if enhanced_analysis.contextual_navigation:
            features.append("contextual_navigation")

        if enhanced_analysis.search_navigation:
            features.append("search_navigation")

        if enhanced_analysis.filter_navigation:
            features.append("filter_navigation")

        if len(enhanced_analysis.breadcrumb_variations) > 1:
            features.append("breadcrumb_variations")

        if enhanced_analysis.dynamic_content_indicators:
            features.append("dynamic_content")

        if any(enhanced_analysis.accessibility_features.values()):
            features.append("accessibility_features")

        return features

    def _generate_cache_key(self, html_content: str, url: str) -> str:
        """Generate cache key for analysis results."""
        import hashlib

        content_hash = hashlib.md5(html_content.encode()).hexdigest()[:16]
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{url_hash}_{content_hash}"

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._analysis_cache.clear()
        logger.info("Analysis cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {"cache_size": len(self._analysis_cache), "cache_enabled": self.config.enable_caching}


# Backward compatibility function
def analyze_website_adaptive(html_content: str, url: str, config: Optional[AnalysisConfig] = None) -> AdaptiveAnalysisResult:
    """
    Convenience function for adaptive website analysis.

    Args:
        html_content: HTML content to analyze
        url: URL of the website
        config: Analysis configuration

    Returns:
        AdaptiveAnalysisResult with appropriate analysis depth
    """
    analyzer = AdaptiveWebsiteAnalyzer(config)
    return analyzer.analyze_website(html_content, url)
