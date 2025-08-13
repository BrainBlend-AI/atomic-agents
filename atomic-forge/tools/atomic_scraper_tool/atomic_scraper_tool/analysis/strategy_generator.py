"""
Scraping strategy generator for the atomic scraper tool.

Creates ScrapingStrategy objects based on website analysis and user criteria.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from atomic_scraper_tool.models.base_models import ScrapingStrategy
from atomic_scraper_tool.analysis.website_analyzer import (
    WebsiteStructureAnalysis, 
    ContentPattern,
    NavigationInfo,
    PaginationInfo
)


@dataclass
class StrategyContext:
    """Context information for strategy generation."""
    user_criteria: str  # Natural language criteria like "scrape Saturday markets"
    target_content_type: str  # 'list', 'article', 'product', 'detail', 'search'
    quality_threshold: float = 50.0
    max_results: int = 10
    include_pagination: bool = True
    extraction_depth: str = 'shallow'  # 'shallow', 'medium', 'deep'


@dataclass
class SelectorRecommendation:
    """Recommendation for a CSS selector with confidence score."""
    selector: str
    confidence: float
    reasoning: str
    fallback_selectors: List[str]


class StrategyGenerator:
    """Generates optimal scraping strategies based on website analysis."""
    
    def __init__(self):
        """Initialize the strategy generator."""
        self.content_type_priorities = {
            'list': ['ul', 'ol', 'div[class*="list"]', 'div[class*="items"]'],
            'article': ['article', 'div[class*="article"]', 'div[class*="post"]'],
            'product': ['div[class*="product"]', 'div[class*="item"]', 'div[class*="card"]'],
            'navigation': ['nav', 'div[class*="nav"]', 'div[class*="menu"]'],
            'pagination': ['div[class*="pagination"]', 'div[class*="pager"]']
        }
        
        self.extraction_patterns = {
            'title': ['h1', 'h2', 'h3', '.title', '.name', '.heading'],
            'description': ['p', '.description', '.summary', '.excerpt', '.content'],
            'price': ['.price', '.cost', '.amount', '[class*="price"]'],
            'link': ['a[href]', '.link', '.url'],
            'image': ['img[src]', '.image', '.photo', '.picture'],
            'date': ['.date', '.time', '.published', '[datetime]'],
            'location': ['.location', '.address', '.place', '.venue'],
            'contact': ['.contact', '.phone', '.email', '.tel']
        }
    
    def generate_strategy(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext
    ) -> ScrapingStrategy:
        """
        Generate an optimal scraping strategy based on analysis and context.
        
        Args:
            analysis: Website structure analysis
            context: Strategy generation context
            
        Returns:
            ScrapingStrategy object with optimal configuration
        """
        # Determine scrape type based on content and context
        scrape_type = self._determine_scrape_type(analysis, context)
        
        # Generate target selectors
        target_selectors = self._generate_target_selectors(analysis, context, scrape_type)
        
        # Determine pagination strategy
        pagination_strategy = self._determine_pagination_strategy(analysis, context)
        
        # Generate content filters
        content_filters = self._generate_content_filters(analysis, context)
        
        # Generate extraction rules
        extraction_rules = self._generate_extraction_rules(analysis, context)
        
        # Calculate optimal request delay
        request_delay = self._calculate_request_delay(analysis)
        
        # Determine max pages
        max_pages = self._determine_max_pages(analysis, context)
        
        return ScrapingStrategy(
            scrape_type=scrape_type,
            target_selectors=target_selectors,
            pagination_strategy=pagination_strategy,
            content_filters=content_filters,
            extraction_rules=extraction_rules,
            max_pages=max_pages,
            request_delay=request_delay
        )
    
    def _determine_scrape_type(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext
    ) -> str:
        """Determine the optimal scrape type."""
        # If user specified a target content type, use that
        if context.target_content_type in ['list', 'detail', 'search', 'sitemap']:
            return context.target_content_type
        
        # Analyze content patterns to determine best type
        content_scores = {
            'list': 0.0,
            'detail': 0.0,
            'search': 0.0,
            'sitemap': 0.0
        }
        
        # Score based on detected patterns
        for pattern in analysis.content_patterns:
            if pattern.pattern_type == 'list':
                content_scores['list'] += pattern.confidence * 2.0
            elif pattern.pattern_type == 'article':
                content_scores['detail'] += pattern.confidence * 1.5
            elif pattern.pattern_type == 'product':
                content_scores['list'] += pattern.confidence * 1.8
            elif pattern.pattern_type == 'navigation':
                content_scores['sitemap'] += pattern.confidence * 0.5
        
        # Boost list score if we have good list containers
        if analysis.list_containers:
            content_scores['list'] += len(analysis.list_containers) * 0.3
        
        # Boost detail score if we have few but rich content areas
        if len(analysis.content_patterns) <= 3 and analysis.main_content_selector:
            content_scores['detail'] += 1.0
        
        # Choose the highest scoring type
        best_type = max(content_scores.items(), key=lambda x: x[1])
        
        # Default to list if no clear winner
        return best_type[0] if best_type[1] > 0.5 else 'list'
    
    def _generate_target_selectors(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext,
        scrape_type: str
    ) -> List[str]:
        """Generate optimal target selectors."""
        selectors = []
        
        if scrape_type == 'list':
            # Use detected list containers
            selectors.extend(analysis.list_containers)
            
            # Add item selectors if we have them
            if analysis.item_selectors:
                selectors.extend(analysis.item_selectors)
            
            # Add pattern-based selectors
            list_patterns = [p for p in analysis.content_patterns if p.pattern_type in ['list', 'product']]
            for pattern in sorted(list_patterns, key=lambda x: x.confidence, reverse=True):
                if pattern.selector not in selectors:
                    selectors.append(pattern.selector)
        
        elif scrape_type == 'detail':
            # Use main content selector
            if analysis.main_content_selector:
                selectors.append(analysis.main_content_selector)
            
            # Add article patterns
            article_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'article']
            for pattern in sorted(article_patterns, key=lambda x: x.confidence, reverse=True):
                if pattern.selector not in selectors:
                    selectors.append(pattern.selector)
        
        elif scrape_type == 'search':
            # Look for search result patterns
            search_indicators = ['result', 'search', 'listing']
            for indicator in search_indicators:
                selector = f'[class*="{indicator}"]'
                selectors.append(selector)
        
        elif scrape_type == 'sitemap':
            # Use navigation patterns
            nav_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'navigation']
            for pattern in nav_patterns:
                selectors.append(pattern.selector)
        
        # Fallback selectors if none found
        if not selectors:
            selectors = self._generate_fallback_selectors(analysis, scrape_type)
        
        return selectors[:5]  # Limit to top 5 selectors
    
    def _generate_fallback_selectors(
        self, 
        analysis: WebsiteStructureAnalysis, 
        scrape_type: str
    ) -> List[str]:
        """Generate fallback selectors when primary detection fails."""
        fallback_selectors = []
        
        if scrape_type == 'list':
            fallback_selectors = [
                'ul li', 'ol li', 'div[class*="item"]', 'div[class*="list"]',
                'article', 'div[class*="card"]', 'div[class*="product"]'
            ]
        elif scrape_type == 'detail':
            fallback_selectors = [
                'main', 'article', 'div[class*="content"]', 'div[class*="main"]',
                'section', 'div[class*="article"]'
            ]
        elif scrape_type == 'search':
            fallback_selectors = [
                'div[class*="result"]', 'div[class*="search"]', 'div[class*="listing"]',
                'li', 'article', 'div[class*="item"]'
            ]
        elif scrape_type == 'sitemap':
            fallback_selectors = [
                'nav a', 'div[class*="nav"] a', 'div[class*="menu"] a',
                'ul a', 'ol a'
            ]
        
        return fallback_selectors
    
    def _determine_pagination_strategy(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext
    ) -> Optional[str]:
        """Determine the optimal pagination strategy."""
        if not context.include_pagination:
            return None
        
        pagination_info = analysis.pagination_info
        
        if pagination_info.pagination_type:
            # Map pagination types to valid strategy values
            type_mapping = {
                'numbered': 'page_numbers',
                'next_prev': 'next_link',
                'infinite_scroll': 'infinite_scroll',
                'load_more': 'load_more'
            }
            return type_mapping.get(pagination_info.pagination_type, 'next_link')
        
        # Look for pagination indicators in patterns
        pagination_patterns = [p for p in analysis.content_patterns if p.pattern_type == 'pagination']
        if pagination_patterns:
            # Analyze the pagination pattern to determine type
            best_pattern = max(pagination_patterns, key=lambda x: x.confidence)
            
            # Simple heuristics based on selector
            if 'next' in best_pattern.selector.lower():
                return 'next_link'
            elif 'page' in best_pattern.selector.lower():
                return 'page_numbers'
            else:
                return 'next_link'  # Default
        
        return None
    
    def _generate_content_filters(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext
    ) -> List[str]:
        """Generate content filtering rules."""
        filters = []
        
        # Add quality-based filters
        if context.quality_threshold > 0:
            filters.append(f'min_quality:{context.quality_threshold}')
        
        # Add content-specific filters based on user criteria
        criteria_lower = context.user_criteria.lower()
        
        # Date-based filters
        if any(word in criteria_lower for word in ['today', 'this week', 'recent']):
            filters.append('recent_content')
        
        if 'saturday' in criteria_lower:
            filters.append('contains:saturday')
        
        if 'market' in criteria_lower:
            filters.append('contains:market')
        
        # Length filters
        if context.extraction_depth == 'shallow':
            filters.append('min_text_length:10')
        elif context.extraction_depth == 'deep':
            filters.append('min_text_length:100')
        
        # Remove duplicates
        filters.append('remove_duplicates')
        
        return filters
    
    def _generate_extraction_rules(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext
    ) -> Dict[str, str]:
        """Generate field extraction rules."""
        rules = {}
        
        # Determine what fields to extract based on content type and criteria
        criteria_lower = context.user_criteria.lower()
        
        # Always try to extract basic fields
        rules['title'] = self._find_best_selector_for_field('title', analysis)
        rules['description'] = self._find_best_selector_for_field('description', analysis)
        rules['url'] = 'a[href]'
        
        # Context-specific fields
        if 'market' in criteria_lower:
            rules['location'] = self._find_best_selector_for_field('location', analysis)
            rules['date'] = self._find_best_selector_for_field('date', analysis)
            rules['contact'] = self._find_best_selector_for_field('contact', analysis)
        
        if 'product' in analysis.content_types or 'price' in criteria_lower:
            rules['price'] = self._find_best_selector_for_field('price', analysis)
            rules['image'] = self._find_best_selector_for_field('image', analysis)
        
        if 'article' in analysis.content_types or 'news' in criteria_lower:
            rules['date'] = self._find_best_selector_for_field('date', analysis)
            rules['author'] = '.author, .by, [class*="author"]'
        
        # Remove empty rules
        rules = {k: v for k, v in rules.items() if v}
        
        return rules
    
    def _find_best_selector_for_field(
        self, 
        field_name: str, 
        analysis: WebsiteStructureAnalysis
    ) -> str:
        """Find the best selector for a specific field."""
        if field_name not in self.extraction_patterns:
            return ''
        
        # Get candidate selectors for this field
        candidates = self.extraction_patterns[field_name]
        
        # Score selectors based on analysis
        best_selector = candidates[0]  # Default to first
        
        # TODO: Could implement more sophisticated selector scoring
        # based on actual presence in the analyzed HTML
        
        return best_selector
    
    def _calculate_request_delay(self, analysis: WebsiteStructureAnalysis) -> float:
        """Calculate optimal request delay based on website characteristics."""
        base_delay = 1.0
        
        # Adjust based on domain
        domain = analysis.metadata.get('domain', '')
        
        # Be more respectful to certain domains
        if any(indicator in domain for indicator in ['gov', 'edu', 'org']):
            base_delay *= 2.0
        
        # Adjust based on page complexity
        total_elements = (
            analysis.metadata.get('total_links', 0) +
            analysis.metadata.get('total_images', 0) +
            analysis.metadata.get('total_forms', 0)
        )
        
        if total_elements > 100:
            base_delay *= 1.5
        elif total_elements > 50:
            base_delay *= 1.2
        
        return min(base_delay, 5.0)  # Cap at 5 seconds
    
    def _determine_max_pages(
        self, 
        analysis: WebsiteStructureAnalysis, 
        context: StrategyContext
    ) -> int:
        """Determine maximum pages to scrape."""
        # Start with context max_results
        if context.max_results <= 10:
            return 1
        elif context.max_results <= 50:
            return 5
        elif context.max_results <= 100:
            return 10
        else:
            return 20
    
    def recommend_selectors(
        self, 
        analysis: WebsiteStructureAnalysis, 
        field_name: str
    ) -> List[SelectorRecommendation]:
        """Recommend selectors for a specific field with confidence scores."""
        recommendations = []
        
        if field_name in self.extraction_patterns:
            candidates = self.extraction_patterns[field_name]
            
            for i, selector in enumerate(candidates):
                confidence = 1.0 - (i * 0.1)  # Decrease confidence for later candidates
                reasoning = f"Standard selector for {field_name} field"
                fallbacks = candidates[i+1:i+3]  # Next 2 as fallbacks
                
                recommendations.append(SelectorRecommendation(
                    selector=selector,
                    confidence=confidence,
                    reasoning=reasoning,
                    fallback_selectors=fallbacks
                ))
        
        return recommendations
    
    def optimize_strategy(
        self, 
        strategy: ScrapingStrategy, 
        analysis: WebsiteStructureAnalysis
    ) -> ScrapingStrategy:
        """Optimize an existing strategy based on analysis."""
        # Create a copy to modify
        optimized = ScrapingStrategy(
            scrape_type=strategy.scrape_type,
            target_selectors=strategy.target_selectors.copy(),
            pagination_strategy=strategy.pagination_strategy,
            content_filters=strategy.content_filters.copy(),
            extraction_rules=strategy.extraction_rules.copy(),
            max_pages=strategy.max_pages,
            request_delay=strategy.request_delay
        )
        
        # Optimize target selectors based on analysis
        if analysis.list_containers:
            # Add high-confidence list containers
            for container in analysis.list_containers:
                if container not in optimized.target_selectors:
                    optimized.target_selectors.append(container)
        
        # Optimize extraction rules
        for field, current_selector in optimized.extraction_rules.items():
            better_selector = self._find_best_selector_for_field(field, analysis)
            if better_selector and better_selector != current_selector:
                optimized.extraction_rules[field] = better_selector
        
        # Optimize request delay
        optimized.request_delay = self._calculate_request_delay(analysis)
        
        return optimized
    
    def validate_strategy(self, strategy: ScrapingStrategy) -> List[str]:
        """Validate a scraping strategy and return any issues."""
        issues = []
        
        # Check target selectors
        if not strategy.target_selectors:
            issues.append("No target selectors defined")
        
        for selector in strategy.target_selectors:
            if not selector.strip():
                issues.append("Empty target selector found")
        
        # Check extraction rules
        if not strategy.extraction_rules:
            issues.append("No extraction rules defined")
        
        # Check scrape type
        valid_types = ['list', 'detail', 'search', 'sitemap']
        if strategy.scrape_type not in valid_types:
            issues.append(f"Invalid scrape type: {strategy.scrape_type}")
        
        # Check pagination strategy
        if strategy.pagination_strategy:
            valid_pagination = ['next_link', 'page_numbers', 'infinite_scroll', 'load_more']
            if strategy.pagination_strategy not in valid_pagination:
                issues.append(f"Invalid pagination strategy: {strategy.pagination_strategy}")
        
        # Check limits
        if strategy.max_pages <= 0:
            issues.append("max_pages must be positive")
        
        if strategy.request_delay < 0.1:
            issues.append("request_delay should be at least 0.1 seconds")
        
        return issues