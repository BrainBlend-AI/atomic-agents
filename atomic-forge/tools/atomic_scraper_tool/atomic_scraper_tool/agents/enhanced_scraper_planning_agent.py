"""
Enhanced Scraper Planning Agent with Adaptive Website Analysis.

This agent extends the standard scraper planning agent to use adaptive website analysis,
automatically leveraging enhanced navigation detection when complex websites are encountered.
"""

import logging
from typing import Dict, Any, Optional, List
from atomic_scraper_tool.agents.scraper_planning_agent import (
    AtomicScraperPlanningAgent,
    ScraperPlanningInputSchema,
    ScraperPlanningOutputSchema
)
from atomic_scraper_tool.analysis.adaptive_website_analyzer import (
    AdaptiveWebsiteAnalyzer,
    AnalysisConfig,
    AdaptiveAnalysisResult
)
from atomic_scraper_tool.models.base_models import ScrapingStrategy


logger = logging.getLogger(__name__)


class EnhancedScraperPlanningAgent(AtomicScraperPlanningAgent):
    """
    Enhanced scraper planning agent with adaptive website analysis.
    
    This agent automatically uses enhanced navigation analysis for complex websites
    while maintaining backward compatibility with the standard planning agent.
    """
    
    def __init__(self, config, analysis_config: Optional[AnalysisConfig] = None):
        """
        Initialize the enhanced planning agent.
        
        Args:
            config: Agent configuration
            analysis_config: Adaptive analysis configuration
        """
        super().__init__(config)
        
        # Initialize adaptive analyzer
        self.analysis_config = analysis_config or AnalysisConfig()
        self.adaptive_analyzer = AdaptiveWebsiteAnalyzer(self.analysis_config)
        
        logger.info("EnhancedScraperPlanningAgent initialized with adaptive analysis")
    
    def _analyze_target_website(self, url: str) -> AdaptiveAnalysisResult:
        """
        Analyze the target website using adaptive analysis.
        
        This method replaces the standard website analysis with adaptive analysis
        that automatically chooses the appropriate depth based on website complexity.
        """
        import requests
        
        try:
            # Fetch the website content
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Perform adaptive analysis
            analysis_result = self.adaptive_analyzer.analyze_website(response.text, url)
            
            # Log analysis results
            logger.info(f"Website analysis completed for {url}")
            logger.info(f"Analysis type: {analysis_result.analysis_type}")
            logger.info(f"Complexity score: {analysis_result.complexity_score:.2f}")
            logger.info(f"Navigation complexity: {analysis_result.navigation_complexity}")
            
            if analysis_result.has_enhanced_analysis:
                logger.info(f"Enhanced features detected: {', '.join(analysis_result.triggered_features)}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing website {url}: {e}")
            # Return a minimal analysis result for error handling
            from atomic_scraper_tool.analysis.website_analyzer import WebsiteStructureAnalysis
            fallback_analysis = WebsiteStructureAnalysis(url=url, title="Error - Could not analyze")
            return AdaptiveAnalysisResult(standard_analysis=fallback_analysis)
    
    def _generate_scraping_strategy(
        self, 
        website_analysis: AdaptiveAnalysisResult, 
        parsed_request: Dict[str, Any], 
        input_data: ScraperPlanningInputSchema
    ) -> ScrapingStrategy:
        """
        Generate enhanced scraping strategy using adaptive analysis results.
        
        This method leverages both standard and enhanced analysis to create
        more intelligent scraping strategies for complex websites.
        """
        # Start with standard strategy generation
        standard_analysis = website_analysis.standard_analysis
        base_strategy = super()._generate_scraping_strategy(standard_analysis, parsed_request, input_data)
        
        # Enhance strategy if enhanced analysis is available
        if website_analysis.has_enhanced_analysis:
            enhanced_analysis = website_analysis.enhanced_analysis
            base_strategy = self._enhance_strategy_with_navigation_analysis(
                base_strategy, enhanced_analysis, parsed_request
            )
        
        return base_strategy
    
    def _enhance_strategy_with_navigation_analysis(
        self,
        base_strategy: ScrapingStrategy,
        enhanced_analysis,
        parsed_request: Dict[str, Any]
    ) -> ScrapingStrategy:
        """
        Enhance scraping strategy using enhanced navigation analysis.
        
        Args:
            base_strategy: Base scraping strategy
            enhanced_analysis: Enhanced navigation analysis results
            parsed_request: Parsed user request
            
        Returns:
            Enhanced scraping strategy
        """
        # Enhance pagination handling
        if enhanced_analysis.advanced_pagination:
            pagination = enhanced_analysis.advanced_pagination
            
            if pagination.pagination_type == "infinite_scroll":
                base_strategy.pagination_enabled = True
                base_strategy.pagination_type = "infinite_scroll"
                base_strategy.max_pages = 50  # Higher limit for infinite scroll
                logger.info("Enhanced strategy: Configured for infinite scroll pagination")
                
            elif pagination.pagination_type == "load_more":
                base_strategy.pagination_enabled = True
                base_strategy.pagination_type = "load_more"
                base_strategy.max_pages = 20
                logger.info("Enhanced strategy: Configured for load-more pagination")
                
            elif pagination.pagination_type == "numbered" and pagination.total_pages:
                base_strategy.max_pages = min(pagination.total_pages, base_strategy.max_pages)
                logger.info(f"Enhanced strategy: Limited pages to {base_strategy.max_pages} based on detected pagination")
        
        # Enhance selectors based on navigation analysis
        if enhanced_analysis.main_navigation:
            # Use hierarchical navigation for better content discovery
            nav_hierarchy = enhanced_analysis.main_navigation[0]  # Use first/main navigation
            if nav_hierarchy.items:
                # Update selectors based on navigation structure
                self._update_selectors_from_navigation(base_strategy, nav_hierarchy)
        
        # Enhance mobile handling
        if enhanced_analysis.mobile_navigation:
            mobile_nav = enhanced_analysis.mobile_navigation
            if mobile_nav.hamburger_selector:
                # Add mobile-specific handling
                base_strategy.mobile_optimized = True
                logger.info("Enhanced strategy: Enabled mobile optimization")
        
        # Enhance filtering capabilities
        if enhanced_analysis.filter_navigation:
            filters = enhanced_analysis.filter_navigation
            if "sort_selectors" in filters:
                # Enable sorting for better data collection
                base_strategy.enable_sorting = True
                logger.info("Enhanced strategy: Enabled sorting capabilities")
        
        # Enhance contextual navigation
        if enhanced_analysis.contextual_navigation:
            contextual = enhanced_analysis.contextual_navigation
            if contextual.related_links:
                # Enable related content discovery
                base_strategy.follow_related_links = True
                logger.info("Enhanced strategy: Enabled related content discovery")
        
        return base_strategy
    
    def _update_selectors_from_navigation(self, strategy: ScrapingStrategy, nav_hierarchy):
        """Update strategy selectors based on navigation hierarchy."""
        # This is a simplified example - in practice, you'd have more sophisticated logic
        if hasattr(strategy, 'content_selectors') and nav_hierarchy.items:
            # Use navigation structure to improve content selection
            main_content_indicators = [
                "main", "#main", ".main-content", ".content", 
                "article", ".article", ".post", ".entry"
            ]
            
            # Add navigation-aware selectors
            for selector in main_content_indicators:
                if selector not in strategy.content_selectors:
                    strategy.content_selectors.append(selector)
    
    def _generate_scraping_plan(
        self,
        strategy: ScrapingStrategy,
        schema_recipe,
        parsed_request: Dict[str, Any],
        website_analysis: Optional[AdaptiveAnalysisResult] = None
    ) -> str:
        """
        Generate enhanced scraping plan with navigation insights.
        
        This method creates a more detailed scraping plan that includes
        insights from enhanced navigation analysis when available.
        """
        # Generate base plan
        base_plan = super()._generate_scraping_plan(strategy, schema_recipe, parsed_request)
        
        # Add enhanced insights if available
        if website_analysis and website_analysis.has_enhanced_analysis:
            enhanced_insights = self._generate_navigation_insights(website_analysis)
            enhanced_plan = f"{base_plan}\n\n## Enhanced Navigation Insights\n{enhanced_insights}"
            return enhanced_plan
        
        return base_plan
    
    def _generate_navigation_insights(self, analysis_result: AdaptiveAnalysisResult) -> str:
        """Generate human-readable navigation insights."""
        insights = []
        enhanced = analysis_result.enhanced_analysis
        
        insights.append(f"**Website Complexity**: {analysis_result.navigation_complexity.title()} (score: {analysis_result.complexity_score:.2f})")
        
        if enhanced.main_navigation:
            nav_count = len(enhanced.main_navigation)
            insights.append(f"**Navigation Structure**: {nav_count} hierarchical navigation levels detected")
        
        if enhanced.mega_menus:
            mega_count = len(enhanced.mega_menus)
            insights.append(f"**Mega Menus**: {mega_count} complex dropdown menus found")
        
        if enhanced.mobile_navigation:
            insights.append("**Mobile Navigation**: Mobile-optimized navigation detected")
        
        if enhanced.advanced_pagination:
            pagination_type = enhanced.advanced_pagination.pagination_type
            insights.append(f"**Pagination**: {pagination_type.replace('_', ' ').title()} pagination detected")
        
        if enhanced.contextual_navigation:
            contextual = enhanced.contextual_navigation
            related_count = len(contextual.related_links)
            if related_count > 0:
                insights.append(f"**Related Content**: {related_count} related content links available")
        
        if enhanced.search_navigation:
            search_elements = len(enhanced.search_navigation)
            insights.append(f"**Search Capabilities**: {search_elements} search elements detected")
        
        if enhanced.filter_navigation:
            filter_types = len(enhanced.filter_navigation)
            insights.append(f"**Filtering Options**: {filter_types} types of filters available")
        
        if enhanced.dynamic_content_indicators:
            dynamic_count = len(enhanced.dynamic_content_indicators)
            insights.append(f"**Dynamic Content**: {dynamic_count} JavaScript-based elements detected")
        
        accessibility_count = sum(enhanced.accessibility_features.values())
        insights.append(f"**Accessibility**: {accessibility_count}/5 accessibility features present")
        
        return "\n".join(f"- {insight}" for insight in insights)
    
    def run(self, input_data: ScraperPlanningInputSchema) -> ScraperPlanningOutputSchema:
        """
        Run enhanced scraper planning with adaptive analysis.
        
        This method overrides the base run method to use adaptive website analysis
        and generate enhanced scraping strategies.
        """
        try:
            # Parse the natural language request
            parsed_request = self._parse_natural_language_request(input_data.request)
            
            # Perform adaptive website analysis
            website_analysis = self._analyze_target_website(input_data.target_url)
            
            # Generate enhanced scraping strategy
            strategy = self._generate_scraping_strategy(website_analysis, parsed_request, input_data)
            
            # Generate schema recipe (using standard method)
            schema_recipe = self._generate_schema_recipe(website_analysis.standard_analysis, parsed_request, input_data)
            
            # Generate enhanced scraping plan
            scraping_plan = self._generate_scraping_plan(strategy, schema_recipe, parsed_request, website_analysis)
            
            # Create output with enhanced information
            output = ScraperPlanningOutputSchema(
                strategy=strategy.dict(),
                schema_recipe=schema_recipe.dict(),
                scraping_plan=scraping_plan,
                confidence_score=0.95 if website_analysis.has_enhanced_analysis else 0.85,
                estimated_items=self._estimate_items_count(website_analysis.standard_analysis, strategy),
                estimated_time=self._estimate_scraping_time(website_analysis.standard_analysis, strategy),
                recommendations=self._generate_enhanced_recommendations(website_analysis, strategy)
            )
            
            logger.info(f"Enhanced scraping plan generated with {len(output.recommendations)} recommendations")
            return output
            
        except Exception as e:
            logger.error(f"Error in enhanced scraper planning: {e}")
            # Fallback to standard planning
            return super().run(input_data)
    
    def _generate_enhanced_recommendations(
        self, 
        website_analysis: AdaptiveAnalysisResult, 
        strategy: ScrapingStrategy
    ) -> List[str]:
        """Generate enhanced recommendations based on adaptive analysis."""
        recommendations = []
        
        if website_analysis.has_enhanced_analysis:
            enhanced = website_analysis.enhanced_analysis
            
            # Navigation-based recommendations
            if enhanced.mega_menus:
                recommendations.append("Consider scraping category hierarchies from mega menus for comprehensive data coverage")
            
            if enhanced.advanced_pagination:
                pagination_type = enhanced.advanced_pagination.pagination_type
                if pagination_type == "infinite_scroll":
                    recommendations.append("Use scroll-based scraping strategy for infinite scroll pagination")
                elif pagination_type == "load_more":
                    recommendations.append("Implement load-more button clicking for complete data extraction")
            
            if enhanced.mobile_navigation:
                recommendations.append("Test scraping on mobile viewport for mobile-specific content")
            
            if enhanced.contextual_navigation and enhanced.contextual_navigation.related_links:
                recommendations.append("Follow related content links for additional data discovery")
            
            if enhanced.filter_navigation:
                recommendations.append("Utilize filtering options to scrape categorized data subsets")
            
            if enhanced.dynamic_content_indicators:
                recommendations.append("Consider using JavaScript rendering for dynamic content")
            
            # Accessibility-based recommendations
            accessibility_count = sum(enhanced.accessibility_features.values())
            if accessibility_count >= 3:
                recommendations.append("Website follows accessibility standards - reliable for automated scraping")
        
        # Complexity-based recommendations
        if website_analysis.complexity_score > 0.7:
            recommendations.append("High complexity website - consider implementing robust error handling")
        elif website_analysis.complexity_score < 0.3:
            recommendations.append("Simple website structure - standard scraping approach should be sufficient")
        
        return recommendations
