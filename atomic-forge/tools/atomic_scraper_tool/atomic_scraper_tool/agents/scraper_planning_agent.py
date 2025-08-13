"""
Atomic Scraper Planning Agent - AI-Powered Scraping Strategy Generation

Next-generation conversational agent that interprets natural language requests
and coordinates intelligent scraping operations with dynamic strategy generation.
"""

from typing import Dict, Any, Optional, List
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase
from pydantic import Field

from atomic_scraper_tool.models.base_models import ScrapingStrategy
from atomic_scraper_tool.models.schema_models import SchemaRecipe


class AtomicScraperAgentInputSchema(BaseIOSchema):
    """Input schema for the atomic scraper planning agent."""
    
    request: str = Field(..., description="Natural language scraping request")
    target_url: str = Field(..., description="Website URL to scrape")
    max_results: int = Field(10, ge=1, le=1000, description="Maximum items to return")
    quality_threshold: float = Field(50.0, ge=0.0, le=100.0, description="Minimum quality score")


class AtomicScraperAgentOutputSchema(BaseIOSchema):
    """Output schema for the atomic scraper planning agent."""
    
    scraping_plan: str = Field(..., description="Human-readable scraping plan")
    strategy: Dict[str, Any] = Field(..., description="Generated scraping strategy")
    schema_recipe: Dict[str, Any] = Field(..., description="Dynamic JSON schema recipe")
    reasoning: str = Field(..., description="Agent's reasoning process")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the plan")


class AtomicScrapingContextProvider(SystemPromptContextProviderBase):
    """Context provider for atomic scraper strategy planning."""
    
    def __init__(self):
        """Initialize the atomic scraping context provider."""
        super().__init__(title="Atomic Scraper Capabilities")
    
    def get_info(self) -> str:
        """Provide context about scraping capabilities and strategies."""
        return """You are an expert website scraping planning agent. Your role is to analyze user requests and target websites to generate optimal scraping strategies.

### Scraping Types Available:
- **list**: Extract multiple items from list pages (e.g., product listings, article lists)
- **detail**: Extract detailed information from individual pages
- **search**: Extract results from search pages
- **sitemap**: Extract URLs and metadata from sitemaps

### Strategy Components:
- **target_selectors**: CSS selectors to identify content containers
- **extraction_rules**: Field-specific extraction rules with CSS selectors
- **pagination_strategy**: How to handle multiple pages (next_link, page_numbers, infinite_scroll, load_more)
- **content_filters**: Rules to filter out unwanted content
- **quality_thresholds**: Minimum quality scores for extracted data

### Schema Recipe Generation:
- Analyze website structure to identify data patterns
- Generate appropriate field definitions with extraction selectors
- Set quality weights based on field importance
- Create validation rules for data integrity

### Best Practices:
- Always respect robots.txt and rate limiting
- Prefer specific CSS selectors over generic ones
- Include fallback selectors for robustness
- Set appropriate quality thresholds based on data criticality
- Consider pagination and dynamic content loading"""


class AtomicScraperPlanningAgent(BaseAgent):
    """
    Next-Generation AI-Powered Scraping Planning Agent.
    
    This intelligent agent interprets natural language requests, analyzes target websites,
    and generates optimal scraping strategies with dynamic schema recipes using advanced
    AI-powered decision making.
    """
    
    def __init__(self, config: BaseAgentConfig):
        """
        Initialize the scraper planning agent.
        
        Args:
            config: Agent configuration with client and model settings
        """
        # Set up system prompt generator with scraping context
        context_providers = {"scraping_context": AtomicScrapingContextProvider()}
        system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are an expert website scraping planning agent.",
                "Your role is to analyze user requests and target websites to generate optimal scraping strategies.",
                "You understand website structures and can create appropriate extraction strategies."
            ],
            steps=[
                "Analyze the user's natural language request to understand what data they want to extract",
                "Examine the target website structure and content patterns",
                "Determine the most appropriate scraping strategy (list, detail, search, sitemap)",
                "Generate CSS selectors and extraction rules for the identified data",
                "Create a dynamic schema recipe that matches the expected data structure",
                "Provide reasoning for your decisions and confidence in the strategy"
            ],
            output_instructions=[
                "Always provide a clear, human-readable scraping plan",
                "Include specific CSS selectors and extraction strategies",
                "Generate a complete schema recipe with field definitions",
                "Explain your reasoning process and decision-making",
                "Provide a confidence score between 0.0 and 1.0"
            ],
            context_providers=context_providers
        )
        
        # Update config with our schemas and system prompt generator
        config.input_schema = AtomicScraperAgentInputSchema
        config.output_schema = AtomicScraperAgentOutputSchema
        config.system_prompt_generator = system_prompt_generator
        
        super().__init__(config)
    
    def run(self, input_data: AtomicScraperAgentInputSchema) -> AtomicScraperAgentOutputSchema:
        """
        Process scraping request and generate plan.
        
        Args:
            input_data: User's scraping request and parameters
            
        Returns:
            Generated scraping plan with strategy and schema
        """
        try:
            # Parse the natural language request
            parsed_request = self._parse_natural_language_request(input_data.request)
            
            # Analyze the target website
            website_analysis = self._analyze_target_website(input_data.target_url)
            
            # Generate scraping strategy
            strategy = self._generate_scraping_strategy(
                website_analysis, 
                parsed_request, 
                input_data
            )
            
            # Generate schema recipe
            schema_recipe = self._generate_schema_recipe(
                website_analysis, 
                parsed_request, 
                input_data
            )
            
            # Generate human-readable plan
            scraping_plan = self._generate_scraping_plan(
                strategy, 
                schema_recipe, 
                parsed_request
            )
            
            # Generate reasoning explanation
            reasoning = self._generate_reasoning(
                website_analysis, 
                strategy, 
                schema_recipe, 
                parsed_request
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                website_analysis, 
                strategy, 
                schema_recipe
            )
            
            return AtomicScraperAgentOutputSchema(
                scraping_plan=scraping_plan,
                strategy=strategy.model_dump(),
                schema_recipe=schema_recipe.model_dump(),
                reasoning=reasoning,
                confidence=confidence
            )
            
        except Exception as e:
            # Handle errors gracefully
            return self._handle_error(str(e), input_data)
    
    def _parse_natural_language_request(self, request: str) -> Dict[str, Any]:
        """Parse natural language request to extract key information."""
        request_lower = request.lower()
        
        parsed = {
            'content_type': 'list',  # Default
            'target_data': [],
            'filters': [],
            'keywords': [],
            'temporal_filters': [],
            'location_filters': []
        }
        
        # Determine content type
        if any(word in request_lower for word in ['list', 'items', 'multiple', 'all']):
            parsed['content_type'] = 'list'
        elif any(word in request_lower for word in ['detail', 'information', 'about', 'specific']):
            parsed['content_type'] = 'detail'
        elif any(word in request_lower for word in ['search', 'find', 'results']):
            parsed['content_type'] = 'search'
        
        # Extract target data types
        data_indicators = {
            'markets': ['market', 'marketplace', 'bazaar'],
            'events': ['event', 'happening', 'activity'],
            'products': ['product', 'item', 'goods'],
            'articles': ['article', 'post', 'blog', 'news'],
            'contacts': ['contact', 'phone', 'email', 'address'],
            'prices': ['price', 'cost', 'fee', 'rate'],
            'dates': ['date', 'time', 'when', 'schedule'],
            'locations': ['location', 'place', 'where', 'address']
        }
        
        for data_type, indicators in data_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                parsed['target_data'].append(data_type)
        
        # Extract temporal filters
        temporal_keywords = ['saturday', 'sunday', 'weekend', 'today', 'tomorrow', 'this week']
        for keyword in temporal_keywords:
            if keyword in request_lower:
                parsed['temporal_filters'].append(keyword)
        
        # Extract location filters
        location_keywords = ['cape town', 'johannesburg', 'durban', 'local', 'nearby']
        for keyword in location_keywords:
            if keyword in request_lower:
                parsed['location_filters'].append(keyword)
        
        # Extract general keywords
        import re
        words = re.findall(r'\b\w+\b', request_lower)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'scrape', 'get', 'find'}
        parsed['keywords'] = [word for word in words if word not in stop_words and len(word) > 2]
        
        return parsed
    
    def _analyze_target_website(self, url: str) -> 'WebsiteStructureAnalysis':
        """Analyze the target website structure."""
        from atomic_scraper_tool.analysis.website_analyzer import WebsiteAnalyzer
        import requests
        from bs4 import BeautifulSoup
        
        try:
            # Fetch the website content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Analyze the website structure
            analyzer = WebsiteAnalyzer()
            analysis = analyzer.analyze_website(response.text, url)
            
            return analysis
            
        except Exception as e:
            # Create a minimal analysis if website fetch fails
            from atomic_scraper_tool.analysis.website_analyzer import WebsiteStructureAnalysis
            return WebsiteStructureAnalysis(
                url=url,
                title="Unknown Website",
                content_patterns=[],
                metadata={'error': str(e)}
            )
    
    def _generate_scraping_strategy(
        self, 
        analysis: 'WebsiteStructureAnalysis', 
        parsed_request: Dict[str, Any], 
        input_data: AtomicScraperAgentInputSchema
    ) -> ScrapingStrategy:
        """Generate optimal scraping strategy."""
        from atomic_scraper_tool.analysis.strategy_generator import StrategyGenerator, StrategyContext
        
        # Create strategy context
        context = StrategyContext(
            user_criteria=input_data.request,
            target_content_type=parsed_request['content_type'],
            quality_threshold=input_data.quality_threshold,
            max_results=input_data.max_results,
            include_pagination=True,
            extraction_depth='medium'
        )
        
        # Generate strategy
        generator = StrategyGenerator()
        strategy = generator.generate_strategy(analysis, context)
        
        return strategy
    
    def _generate_schema_recipe(
        self, 
        analysis: 'WebsiteStructureAnalysis', 
        parsed_request: Dict[str, Any], 
        input_data: AtomicScraperAgentInputSchema
    ) -> 'SchemaRecipe':
        """Generate dynamic schema recipe."""
        from atomic_scraper_tool.analysis.schema_recipe_generator import SchemaRecipeGenerator, SchemaGenerationContext
        
        # Create schema generation context
        context = SchemaGenerationContext(
            user_criteria=input_data.request,
            target_content_type=parsed_request['content_type'],
            sample_html="",  # Would be populated with actual HTML in real implementation
            quality_requirements={
                "completeness": 0.4,
                "accuracy": 0.4,
                "consistency": 0.2
            },
            field_preferences=parsed_request['target_data']
        )
        
        # Generate schema recipe
        generator = SchemaRecipeGenerator()
        
        # For now, create a basic schema recipe since we don't have HTML content
        # In a real implementation, this would use the actual website HTML
        schema_recipe = self._create_basic_schema_recipe(parsed_request, input_data)
        
        return schema_recipe
    
    def _create_basic_schema_recipe(
        self, 
        parsed_request: Dict[str, Any], 
        input_data: AtomicScraperAgentInputSchema
    ) -> 'SchemaRecipe':
        """Create a basic schema recipe based on parsed request."""
        from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
        
        # Determine fields based on target data
        fields = {}
        
        # Always include basic fields
        fields['title'] = FieldDefinition(
            field_type='string',
            description='Title or name of the item',
            extraction_selector='h1, h2, h3, .title, .name',
            required=True,
            quality_weight=0.9,
            post_processing=['trim', 'clean']
        )
        
        fields['description'] = FieldDefinition(
            field_type='string',
            description='Description or summary of the item',
            extraction_selector='p, .description, .summary, .content',
            required=False,
            quality_weight=0.7,
            post_processing=['trim', 'clean']
        )
        
        fields['url'] = FieldDefinition(
            field_type='string',
            description='Link to more information',
            extraction_selector='a[href]',
            required=False,
            quality_weight=0.5,
            post_processing=['trim']
        )
        
        # Add fields based on target data
        if 'markets' in parsed_request['target_data']:
            fields['location'] = FieldDefinition(
                field_type='string',
                description='Market location or address',
                extraction_selector='.location, .address, .venue',
                required=False,
                quality_weight=0.8,
                post_processing=['trim', 'clean']
            )
            
            fields['operating_hours'] = FieldDefinition(
                field_type='string',
                description='Market operating hours',
                extraction_selector='.hours, .time, .schedule',
                required=False,
                quality_weight=0.7,
                post_processing=['trim', 'clean']
            )
        
        if 'prices' in parsed_request['target_data']:
            fields['price'] = FieldDefinition(
                field_type='string',
                description='Price or cost information',
                extraction_selector='.price, .cost, .fee, .amount',
                required=False,
                quality_weight=0.8,
                post_processing=['trim', 'clean', 'extract_numbers']
            )
        
        if 'dates' in parsed_request['target_data']:
            fields['date'] = FieldDefinition(
                field_type='string',
                description='Date or time information',
                extraction_selector='.date, .time, time, .published',
                required=False,
                quality_weight=0.7,
                post_processing=['trim', 'clean']
            )
        
        if 'contacts' in parsed_request['target_data']:
            fields['contact'] = FieldDefinition(
                field_type='string',
                description='Contact information',
                extraction_selector='.contact, .phone, .email, .tel',
                required=False,
                quality_weight=0.8,
                post_processing=['trim', 'clean']
            )
        
        # Create schema name
        keywords = parsed_request['keywords'][:2] if parsed_request['keywords'] else ['data']
        schema_name = '_'.join(keywords) + '_schema'
        
        return SchemaRecipe(
            name=schema_name,
            description=f"Schema for extracting {parsed_request['content_type']} data based on: {input_data.request}",
            fields=fields,
            validation_rules=['normalize_whitespace', 'allow_partial_data'],
            quality_weights={
                "completeness": 0.4,
                "accuracy": 0.4,
                "consistency": 0.2
            },
            version="1.0"
        )
    
    def _generate_scraping_plan(
        self, 
        strategy: ScrapingStrategy, 
        schema_recipe: 'SchemaRecipe', 
        parsed_request: Dict[str, Any]
    ) -> str:
        """Generate human-readable scraping plan."""
        plan_parts = []
        
        # Introduction
        plan_parts.append(f"## Scraping Plan for {parsed_request['content_type'].title()} Data")
        plan_parts.append("")
        
        # Strategy overview
        plan_parts.append("### Strategy Overview")
        plan_parts.append(f"- **Scrape Type**: {strategy.scrape_type}")
        plan_parts.append(f"- **Target Selectors**: {', '.join(strategy.target_selectors[:3])}")
        if strategy.pagination_strategy:
            plan_parts.append(f"- **Pagination**: {strategy.pagination_strategy}")
        plan_parts.append(f"- **Max Pages**: {strategy.max_pages}")
        plan_parts.append(f"- **Request Delay**: {strategy.request_delay}s")
        plan_parts.append("")
        
        # Data fields
        plan_parts.append("### Data Fields to Extract")
        for field_name, field_def in schema_recipe.fields.items():
            required_text = " (Required)" if field_def.required else ""
            plan_parts.append(f"- **{field_name.title()}**{required_text}: {field_def.description}")
        plan_parts.append("")
        
        # Extraction approach
        plan_parts.append("### Extraction Approach")
        plan_parts.append(f"1. Navigate to the target website")
        plan_parts.append(f"2. Identify content using selectors: {', '.join(strategy.target_selectors[:2])}")
        plan_parts.append(f"3. Extract data fields using CSS selectors")
        if strategy.pagination_strategy:
            plan_parts.append(f"4. Handle pagination using {strategy.pagination_strategy} strategy")
        plan_parts.append(f"5. Apply quality filtering (minimum score: {strategy.extraction_rules.get('min_quality', 'N/A')})")
        plan_parts.append("")
        
        # Quality measures
        plan_parts.append("### Quality Measures")
        plan_parts.append("- Data validation and cleaning")
        plan_parts.append("- Duplicate removal")
        plan_parts.append("- Quality scoring based on completeness and accuracy")
        
        return "\n".join(plan_parts)
    
    def _generate_reasoning(
        self, 
        analysis: 'WebsiteStructureAnalysis', 
        strategy: ScrapingStrategy, 
        schema_recipe: 'SchemaRecipe', 
        parsed_request: Dict[str, Any]
    ) -> str:
        """Generate comprehensive reasoning explanation for the decisions made."""
        reasoning_parts = []
        
        reasoning_parts.append("## Decision Reasoning & Analysis")
        reasoning_parts.append("")
        
        # Request analysis reasoning
        reasoning_parts.append("### Request Analysis")
        reasoning_parts.append("**User Intent Interpretation:**")
        reasoning_parts.append(f"- Content type identified: '{parsed_request['content_type']}'")
        reasoning_parts.append(f"- Target data types: {', '.join(parsed_request['target_data']) if parsed_request['target_data'] else 'general content'}")
        reasoning_parts.append(f"- Key terms extracted: {', '.join(parsed_request['keywords'][:5]) if parsed_request['keywords'] else 'none specific'}")
        
        if parsed_request['temporal_filters']:
            reasoning_parts.append(f"- Temporal filters detected: {', '.join(parsed_request['temporal_filters'])}")
        if parsed_request['location_filters']:
            reasoning_parts.append(f"- Location filters detected: {', '.join(parsed_request['location_filters'])}")
        
        reasoning_parts.append("")
        
        # Website analysis reasoning
        reasoning_parts.append("### Website Analysis")
        reasoning_parts.append("**Structure Assessment:**")
        if 'error' not in analysis.metadata:
            reasoning_parts.append(f"- Successfully analyzed website: {analysis.url}")
            reasoning_parts.append(f"- Page title: {getattr(analysis, 'title', 'Unknown')}")
            if hasattr(analysis, 'content_patterns') and analysis.content_patterns:
                reasoning_parts.append(f"- Content patterns identified: {len(analysis.content_patterns)} patterns")
                for i, pattern in enumerate(analysis.content_patterns[:3]):
                    reasoning_parts.append(f"  - Pattern {i+1}: {pattern.get('type', 'unknown')} content")
            else:
                reasoning_parts.append("- Limited content patterns detected, using generic approach")
        else:
            reasoning_parts.append(f"- Website analysis failed: {analysis.metadata.get('error', 'Unknown error')}")
            reasoning_parts.append("- Falling back to common web patterns and best practices")
        
        reasoning_parts.append("")
        
        # Strategy reasoning
        reasoning_parts.append("### Strategy Selection")
        reasoning_parts.append(f"**Selected '{strategy.scrape_type}' strategy because:**")
        
        strategy_reasoning = self._get_strategy_reasoning(strategy, parsed_request, analysis)
        for reason in strategy_reasoning:
            reasoning_parts.append(f"- {reason}")
        
        reasoning_parts.append("")
        reasoning_parts.append("**Configuration Details:**")
        reasoning_parts.append(f"- Max pages: {strategy.max_pages} (balances thoroughness with efficiency)")
        reasoning_parts.append(f"- Request delay: {strategy.request_delay}s (respectful crawling)")
        
        if strategy.pagination_strategy:
            reasoning_parts.append(f"- Pagination: {strategy.pagination_strategy} (handles multi-page content)")
        
        reasoning_parts.append("")
        
        # Selector reasoning
        reasoning_parts.append("### Selector Strategy")
        reasoning_parts.append("**Target selectors chosen based on:**")
        selector_reasoning = self._get_selector_reasoning(strategy, parsed_request)
        for reason in selector_reasoning:
            reasoning_parts.append(f"- {reason}")
        
        reasoning_parts.append("")
        reasoning_parts.append("**Selector Details:**")
        for i, selector in enumerate(strategy.target_selectors[:3]):
            reasoning_parts.append(f"- Selector {i+1}: `{selector}` - {self._explain_selector(selector)}")
        
        reasoning_parts.append("")
        
        # Schema reasoning
        reasoning_parts.append("### Schema Design")
        reasoning_parts.append("**Field selection rationale:**")
        schema_reasoning = self._get_schema_reasoning(schema_recipe, parsed_request)
        for reason in schema_reasoning:
            reasoning_parts.append(f"- {reason}")
        
        reasoning_parts.append("")
        reasoning_parts.append("**Field Details:**")
        for field_name, field_def in list(schema_recipe.fields.items())[:5]:  # Show first 5 fields
            priority = "High" if field_def.required else "Medium" if field_def.quality_weight > 0.7 else "Low"
            reasoning_parts.append(f"- **{field_name}** ({priority} priority): {field_def.description}")
            reasoning_parts.append(f"  - Selector: `{field_def.extraction_selector}`")
            reasoning_parts.append(f"  - Quality weight: {field_def.quality_weight}")
        
        reasoning_parts.append("")
        
        # Quality reasoning
        reasoning_parts.append("### Quality Assurance")
        reasoning_parts.append("**Quality measures implemented:**")
        quality_reasoning = self._get_quality_reasoning(schema_recipe, strategy)
        for reason in quality_reasoning:
            reasoning_parts.append(f"- {reason}")
        
        reasoning_parts.append("")
        
        # Risk assessment
        reasoning_parts.append("### Risk Assessment")
        risks = self._assess_risks(analysis, strategy, schema_recipe)
        if risks:
            reasoning_parts.append("**Potential challenges identified:**")
            for risk in risks:
                reasoning_parts.append(f"- {risk}")
        else:
            reasoning_parts.append("**No significant risks identified** - strategy appears robust")
        
        reasoning_parts.append("")
        
        # Recommendations
        reasoning_parts.append("### Recommendations")
        recommendations = self._generate_recommendations(analysis, strategy, schema_recipe, parsed_request)
        for rec in recommendations:
            reasoning_parts.append(f"- {rec}")
        
        return "\n".join(reasoning_parts)
    
    def _get_strategy_reasoning(
        self, 
        strategy: ScrapingStrategy, 
        parsed_request: Dict[str, Any], 
        analysis: 'WebsiteStructureAnalysis'
    ) -> List[str]:
        """Get specific reasoning for strategy selection."""
        reasons = []
        
        if strategy.scrape_type == 'list':
            reasons.append("Request indicates multiple items need to be extracted")
            reasons.append("List strategy optimal for bulk data collection")
            if parsed_request['content_type'] == 'list':
                reasons.append("User explicitly requested list-type content")
            if hasattr(analysis, 'content_patterns'):
                reasons.append("Website structure suggests repeating content patterns")
        
        elif strategy.scrape_type == 'detail':
            reasons.append("Request focuses on detailed information extraction")
            reasons.append("Detail strategy provides comprehensive data capture")
            if parsed_request['content_type'] == 'detail':
                reasons.append("User explicitly requested detailed information")
        
        elif strategy.scrape_type == 'search':
            reasons.append("Request appears to be search-oriented")
            reasons.append("Search strategy handles result pages effectively")
            if 'search' in parsed_request['keywords']:
                reasons.append("Search terms detected in user request")
        
        elif strategy.scrape_type == 'sitemap':
            reasons.append("Sitemap strategy chosen for comprehensive site coverage")
            reasons.append("Efficient for discovering all available content")
        
        return reasons
    
    def _get_selector_reasoning(
        self, 
        strategy: ScrapingStrategy, 
        parsed_request: Dict[str, Any]
    ) -> List[str]:
        """Get reasoning for selector choices."""
        reasons = []
        
        reasons.append("Common HTML patterns for the identified content type")
        reasons.append("Semantic HTML elements that typically contain target data")
        reasons.append("CSS classes commonly used for content organization")
        
        if parsed_request['target_data']:
            reasons.append(f"Selectors optimized for {', '.join(parsed_request['target_data'])} content")
        
        reasons.append("Fallback selectors included for robustness")
        reasons.append("Progressive specificity from generic to specific selectors")
        
        return reasons
    
    def _get_schema_reasoning(
        self, 
        schema_recipe: 'SchemaRecipe', 
        parsed_request: Dict[str, Any]
    ) -> List[str]:
        """Get reasoning for schema design choices."""
        reasons = []
        
        required_count = sum(1 for field in schema_recipe.fields.values() if field.required)
        total_count = len(schema_recipe.fields)
        
        reasons.append(f"Schema includes {total_count} fields with {required_count} required fields")
        reasons.append("Field selection based on user criteria and content type analysis")
        
        if parsed_request['target_data']:
            reasons.append(f"Specialized fields added for: {', '.join(parsed_request['target_data'])}")
        
        reasons.append("Quality weights assigned based on field importance and reliability")
        reasons.append("Post-processing steps included for data cleaning and validation")
        reasons.append("Flexible schema allows for partial data extraction")
        
        return reasons
    
    def _get_quality_reasoning(
        self, 
        schema_recipe: 'SchemaRecipe', 
        strategy: ScrapingStrategy
    ) -> List[str]:
        """Get reasoning for quality assurance measures."""
        reasons = []
        
        reasons.append("Required fields ensure minimum data completeness")
        reasons.append("Quality weights prioritize critical information")
        reasons.append("Post-processing steps clean and normalize extracted data")
        reasons.append("Validation rules prevent invalid data from being stored")
        
        if hasattr(strategy, 'content_filters') and strategy.content_filters:
            reasons.append("Content filters remove irrelevant or low-quality data")
        
        reasons.append("Quality scoring enables filtering of substandard results")
        reasons.append("Multiple selector fallbacks improve extraction reliability")
        
        return reasons
    
    def _explain_selector(self, selector: str) -> str:
        """Provide human-readable explanation of CSS selector."""
        explanations = {
            'div': 'Generic container elements',
            'article': 'Semantic article content',
            'li': 'List item elements',
            'h1': 'Main headings',
            'h2': 'Secondary headings',
            'h3': 'Tertiary headings',
            'p': 'Paragraph text',
            'a': 'Link elements',
            '.title': 'Elements with title class',
            '.content': 'Elements with content class',
            '.item': 'Elements with item class',
            '.product': 'Elements with product class',
            '.price': 'Elements with price class',
            '.date': 'Elements with date class'
        }
        
        # Simple selector explanation
        for pattern, explanation in explanations.items():
            if pattern in selector:
                return explanation
        
        return 'Custom selector for specific content'
    
    def _assess_risks(
        self, 
        analysis: 'WebsiteStructureAnalysis', 
        strategy: ScrapingStrategy, 
        schema_recipe: 'SchemaRecipe'
    ) -> List[str]:
        """Assess potential risks and challenges."""
        risks = []
        
        # Website analysis risks
        if 'error' in analysis.metadata:
            risks.append("Website analysis failed - selectors may not be optimal")
        
        # Strategy risks
        if not strategy.target_selectors:
            risks.append("No specific target selectors - may extract irrelevant content")
        
        if strategy.scrape_type == 'list' and not strategy.pagination_strategy:
            risks.append("List scraping without pagination may miss content")
        
        # Schema risks
        required_fields = sum(1 for field in schema_recipe.fields.values() if field.required)
        if required_fields == 0:
            risks.append("No required fields - may result in empty extractions")
        
        if len(schema_recipe.fields) > 10:
            risks.append("Large number of fields may impact extraction performance")
        
        # Selector risks
        generic_selectors = ['div', 'span', 'p']
        if any(sel in generic_selectors for sel in strategy.target_selectors):
            risks.append("Generic selectors may extract unintended content")
        
        return risks
    
    def _generate_recommendations(
        self, 
        analysis: 'WebsiteStructureAnalysis', 
        strategy: ScrapingStrategy, 
        schema_recipe: 'SchemaRecipe', 
        parsed_request: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # General recommendations
        recommendations.append("Test the strategy on a small sample before full execution")
        recommendations.append("Monitor quality scores and adjust thresholds as needed")
        
        # Strategy-specific recommendations
        if strategy.scrape_type == 'list':
            recommendations.append("Consider enabling pagination if more results are needed")
            recommendations.append("Adjust max_pages based on content volume requirements")
        
        # Quality recommendations
        avg_quality_weight = sum(field.quality_weight for field in schema_recipe.fields.values()) / len(schema_recipe.fields)
        if avg_quality_weight < 0.6:
            recommendations.append("Consider increasing quality weights for critical fields")
        
        # Performance recommendations
        if strategy.request_delay < 1.0:
            recommendations.append("Consider increasing request delay for more respectful crawling")
        
        if len(strategy.target_selectors) > 5:
            recommendations.append("Consider reducing number of target selectors for better performance")
        
        # Data recommendations
        if parsed_request['target_data']:
            recommendations.append(f"Validate extracted {', '.join(parsed_request['target_data'])} data for accuracy")
        
        recommendations.append("Review extracted samples to refine selectors if needed")
        recommendations.append("Consider adding fallback selectors for improved reliability")
        
        return recommendations
    
    def _calculate_confidence(
        self, 
        analysis: 'WebsiteStructureAnalysis', 
        strategy: ScrapingStrategy, 
        schema_recipe: 'SchemaRecipe'
    ) -> float:
        """Calculate comprehensive confidence score for the generated plan."""
        confidence_components = {}
        
        # Website analysis confidence (25% weight)
        if 'error' not in analysis.metadata:
            confidence_components['website_analysis'] = 0.85  # Successfully analyzed website
        else:
            confidence_components['website_analysis'] = 0.25  # Failed to analyze website
        
        # Strategy confidence (30% weight)
        strategy_score = self._calculate_strategy_confidence(strategy)
        confidence_components['strategy'] = strategy_score
        
        # Schema confidence (25% weight)
        schema_score = self._calculate_schema_confidence(schema_recipe)
        confidence_components['schema'] = schema_score
        
        # Selector confidence (20% weight)
        selector_score = self._calculate_selector_confidence(strategy)
        confidence_components['selectors'] = selector_score
        
        # Calculate weighted confidence score
        weights = {
            'website_analysis': 0.25,
            'strategy': 0.30,
            'schema': 0.25,
            'selectors': 0.20
        }
        
        weighted_confidence = sum(
            confidence_components[component] * weights[component]
            for component in confidence_components
        )
        
        # Apply confidence modifiers
        final_confidence = self._apply_confidence_modifiers(
            weighted_confidence, analysis, strategy, schema_recipe
        )
        
        return min(1.0, max(0.0, final_confidence))
    
    def _calculate_strategy_confidence(self, strategy: ScrapingStrategy) -> float:
        """Calculate confidence in the strategy selection."""
        score = 0.5  # Base score
        
        # Strategy type appropriateness
        if strategy.scrape_type in ['list', 'detail', 'search']:
            score += 0.2  # Common, well-supported strategies
        
        # Configuration completeness
        if strategy.target_selectors:
            score += 0.15
        if strategy.pagination_strategy:
            score += 0.1
        if strategy.max_pages > 1:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_schema_confidence(self, schema_recipe: 'SchemaRecipe') -> float:
        """Calculate confidence in the schema design."""
        score = 0.3  # Base score
        
        # Field coverage
        field_count = len(schema_recipe.fields)
        if field_count >= 5:
            score += 0.3
        elif field_count >= 3:
            score += 0.2
        elif field_count >= 2:
            score += 0.1
        
        # Required fields presence
        required_fields = sum(1 for field in schema_recipe.fields.values() if field.required)
        if required_fields > 0:
            score += 0.2
        
        # Quality weights distribution
        avg_quality_weight = sum(field.quality_weight for field in schema_recipe.fields.values()) / len(schema_recipe.fields)
        if avg_quality_weight > 0.7:
            score += 0.15
        elif avg_quality_weight > 0.5:
            score += 0.1
        
        # Post-processing coverage
        fields_with_processing = sum(1 for field in schema_recipe.fields.values() if field.post_processing)
        if fields_with_processing > 0:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_selector_confidence(self, strategy: ScrapingStrategy) -> float:
        """Calculate confidence in the selector choices."""
        score = 0.2  # Base score
        
        if not strategy.target_selectors:
            return score
        
        # Selector specificity
        specific_selectors = sum(1 for sel in strategy.target_selectors 
                               if any(char in sel for char in ['.', '#', '[']))
        if specific_selectors > 0:
            score += 0.3
        
        # Selector diversity
        if len(strategy.target_selectors) > 1:
            score += 0.2
        
        # Semantic selectors
        semantic_selectors = sum(1 for sel in strategy.target_selectors 
                               if any(tag in sel for tag in ['article', 'section', 'main', 'header']))
        if semantic_selectors > 0:
            score += 0.15
        
        # Fallback selectors
        generic_selectors = sum(1 for sel in strategy.target_selectors 
                              if sel in ['div', 'span', 'p'])
        if generic_selectors > 0 and len(strategy.target_selectors) > generic_selectors:
            score += 0.15  # Has both specific and generic selectors
        
        return min(1.0, score)
    
    def _apply_confidence_modifiers(
        self, 
        base_confidence: float, 
        analysis: 'WebsiteStructureAnalysis', 
        strategy: ScrapingStrategy, 
        schema_recipe: 'SchemaRecipe'
    ) -> float:
        """Apply modifiers to adjust confidence based on risk factors."""
        confidence = base_confidence
        
        # Risk-based modifiers
        risks = self._assess_risks(analysis, strategy, schema_recipe)
        risk_penalty = len(risks) * 0.05  # 5% penalty per risk
        confidence -= risk_penalty
        
        # Complexity modifiers
        if len(schema_recipe.fields) > 8:
            confidence -= 0.05  # Complex schemas are riskier
        
        if strategy.max_pages > 10:
            confidence -= 0.03  # Many pages increase failure risk
        
        # Quality modifiers
        high_quality_fields = sum(1 for field in schema_recipe.fields.values() 
                                if field.quality_weight > 0.8)
        if high_quality_fields > 0:
            confidence += 0.05  # High-quality fields increase confidence
        
        return confidence
    
    def _handle_error(self, error_message: str, input_data: AtomicScraperAgentInputSchema) -> AtomicScraperAgentOutputSchema:
        """Handle errors gracefully by returning a basic response."""
        return AtomicScraperAgentOutputSchema(
            scraping_plan=f"Error occurred while generating scraping plan: {error_message}",
            strategy={
                "scrape_type": "list",
                "target_selectors": ["div", "article", "li"],
                "extraction_rules": {"title": "h1, h2, h3"},
                "max_pages": 1,
                "request_delay": 1.0
            },
            schema_recipe={
                "name": "error_schema",
                "description": "Basic schema due to error",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Title of the item",
                        "extraction_selector": "h1, h2, h3",
                        "required": True
                    }
                }
            },
            reasoning=f"An error occurred during plan generation: {error_message}. Providing basic fallback strategy.",
            confidence=0.2
        )