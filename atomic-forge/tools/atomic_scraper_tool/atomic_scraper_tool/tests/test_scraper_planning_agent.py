"""
Unit tests for the AtomicScraperPlanningAgent.

Tests agent initialization, schema validation, and basic request handling.
"""

import pytest
from unittest.mock import Mock, MagicMock
import instructor
from atomic_agents.agents.base_agent import BaseAgentConfig

from atomic_scraper_tool.agents.scraper_planning_agent import (
    AtomicScraperPlanningAgent,
    AtomicScraperAgentInputSchema,
    AtomicScraperAgentOutputSchema,
    AtomicScrapingContextProvider
)


class TestAtomicScrapingContextProvider:
    """Test the scraping context provider."""
    
    def test_context_provider_initialization(self):
        """Test that context provider initializes correctly."""
        provider = AtomicScrapingContextProvider()
        assert provider is not None
        assert provider.title == "Atomic Scraper Capabilities"
    
    def test_get_info_returns_string(self):
        """Test that get_info returns a non-empty string."""
        provider = AtomicScrapingContextProvider()
        info = provider.get_info()
        
        assert isinstance(info, str)
        assert len(info) > 0
        assert "expert website scraping planning agent" in info
    
    def test_get_info_contains_required_sections(self):
        """Test that get_info contains all required sections."""
        provider = AtomicScrapingContextProvider()
        info = provider.get_info()
        
        required_sections = [
            "Scraping Types Available",
            "Strategy Components",
            "Schema Recipe Generation",
            "Best Practices"
        ]
        
        for section in required_sections:
            assert section in info
    
    def test_get_info_contains_scraping_types(self):
        """Test that get_info contains all scraping types."""
        provider = AtomicScrapingContextProvider()
        info = provider.get_info()
        
        scraping_types = ["list", "detail", "search", "sitemap"]
        for scrape_type in scraping_types:
            assert scrape_type in info


class TestAtomicScraperAgentInputSchema:
    """Test the input schema for the scraper agent."""
    
    def test_valid_input_schema(self):
        """Test creating a valid input schema."""
        input_data = AtomicScraperAgentInputSchema(
            request="scrape Saturday markets",
            target_url="https://example.com",
            max_results=20,
            quality_threshold=75.0
        )
        
        assert input_data.request == "scrape Saturday markets"
        assert input_data.target_url == "https://example.com"
        assert input_data.max_results == 20
        assert input_data.quality_threshold == 75.0
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        input_data = AtomicScraperAgentInputSchema(
            request="test request",
            target_url="https://example.com"
        )
        
        assert input_data.max_results == 10
        assert input_data.quality_threshold == 50.0
    
    def test_max_results_validation(self):
        """Test max_results validation constraints."""
        # Test minimum constraint
        with pytest.raises(ValueError):
            AtomicScraperAgentInputSchema(
                request="test",
                target_url="https://example.com",
                max_results=0
            )
        
        # Test maximum constraint
        with pytest.raises(ValueError):
            AtomicScraperAgentInputSchema(
                request="test",
                target_url="https://example.com",
                max_results=1001
            )
        
        # Test valid values
        valid_input = AtomicScraperAgentInputSchema(
            request="test",
            target_url="https://example.com",
            max_results=500
        )
        assert valid_input.max_results == 500
    
    def test_quality_threshold_validation(self):
        """Test quality_threshold validation constraints."""
        # Test minimum constraint
        with pytest.raises(ValueError):
            AtomicScraperAgentInputSchema(
                request="test",
                target_url="https://example.com",
                quality_threshold=-1.0
            )
        
        # Test maximum constraint
        with pytest.raises(ValueError):
            AtomicScraperAgentInputSchema(
                request="test",
                target_url="https://example.com",
                quality_threshold=101.0
            )
        
        # Test valid values
        valid_input = AtomicScraperAgentInputSchema(
            request="test",
            target_url="https://example.com",
            quality_threshold=85.5
        )
        assert valid_input.quality_threshold == 85.5
    
    def test_required_fields(self):
        """Test that required fields are enforced."""
        # Missing request
        with pytest.raises(ValueError):
            AtomicScraperAgentInputSchema(target_url="https://example.com")
        
        # Missing target_url
        with pytest.raises(ValueError):
            AtomicScraperAgentInputSchema(request="test request")


class TestAtomicScraperAgentOutputSchema:
    """Test the output schema for the scraper agent."""
    
    def test_valid_output_schema(self):
        """Test creating a valid output schema."""
        output_data = AtomicScraperAgentOutputSchema(
            scraping_plan="Plan to scrape markets data",
            strategy={"scrape_type": "list", "target_selectors": [".market-item"]},
            schema_recipe={"name": "markets", "fields": {}},
            reasoning="Based on website analysis, using list scraping",
            confidence=0.85
        )
        
        assert output_data.scraping_plan == "Plan to scrape markets data"
        assert output_data.strategy["scrape_type"] == "list"
        assert output_data.schema_recipe["name"] == "markets"
        assert output_data.reasoning == "Based on website analysis, using list scraping"
        assert output_data.confidence == 0.85
    
    def test_confidence_validation(self):
        """Test confidence validation constraints."""
        # Test minimum constraint
        with pytest.raises(ValueError):
            AtomicScraperAgentOutputSchema(
                scraping_plan="test",
                strategy={},
                schema_recipe={},
                reasoning="test",
                confidence=-0.1
            )
        
        # Test maximum constraint
        with pytest.raises(ValueError):
            AtomicScraperAgentOutputSchema(
                scraping_plan="test",
                strategy={},
                schema_recipe={},
                reasoning="test",
                confidence=1.1
            )
        
        # Test valid values
        valid_output = AtomicScraperAgentOutputSchema(
            scraping_plan="test",
            strategy={},
            schema_recipe={},
            reasoning="test",
            confidence=0.75
        )
        assert valid_output.confidence == 0.75
    
    def test_required_fields(self):
        """Test that all fields are required."""
        required_fields = ["scraping_plan", "strategy", "schema_recipe", "reasoning", "confidence"]
        
        for field in required_fields:
            kwargs = {
                "scraping_plan": "test",
                "strategy": {},
                "schema_recipe": {},
                "reasoning": "test",
                "confidence": 0.5
            }
            del kwargs[field]
            
            with pytest.raises(ValueError):
                AtomicScraperAgentOutputSchema(**kwargs)


class TestAtomicScraperPlanningAgent:
    """Test the AtomicScraperPlanningAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock client
        self.mock_client = Mock(spec=instructor.client.Instructor)
        
        # Create agent config
        self.config = BaseAgentConfig(
            client=self.mock_client,
            model="gpt-4o-mini"
        )
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = AtomicScraperPlanningAgent(self.config)
        
        assert agent is not None
        assert agent.input_schema == AtomicScraperAgentInputSchema
        assert agent.output_schema == AtomicScraperAgentOutputSchema
        assert agent.client == self.mock_client
        assert agent.model == "gpt-4o-mini"
    
    def test_agent_has_system_prompt_generator(self):
        """Test that agent has system prompt generator with context."""
        agent = AtomicScraperPlanningAgent(self.config)
        
        assert agent.system_prompt_generator is not None
        assert "scraping_context" in agent.system_prompt_generator.context_providers
        
        # Test that context provider is the right type
        context_provider = agent.system_prompt_generator.context_providers["scraping_context"]
        assert isinstance(context_provider, AtomicScrapingContextProvider)
    
    def test_system_prompt_generation(self):
        """Test that system prompt is generated correctly."""
        agent = AtomicScraperPlanningAgent(self.config)
        
        system_prompt = agent.system_prompt_generator.generate_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "Atomic Scraper Capabilities" in system_prompt
    
    def test_agent_memory_initialization(self):
        """Test that agent memory is initialized."""
        agent = AtomicScraperPlanningAgent(self.config)
        
        assert agent.memory is not None
        assert hasattr(agent.memory, 'get_history')
        assert hasattr(agent.memory, 'add_message')
    
    def test_run_method_basic_execution(self):
        """Test that run method executes and returns valid output."""
        agent = AtomicScraperPlanningAgent(self.config)
        
        input_data = AtomicScraperAgentInputSchema(
            request="scrape Saturday markets",
            target_url="https://example.com"
        )
        
        # The run method should execute without raising NotImplementedError
        result = agent.run(input_data)
        
        # Verify the result is a valid output schema
        assert isinstance(result, AtomicScraperAgentOutputSchema)
        assert isinstance(result.scraping_plan, str)
        assert isinstance(result.strategy, dict)
        assert isinstance(result.schema_recipe, dict)
        assert isinstance(result.reasoning, str)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_agent_config_update(self):
        """Test that agent config is properly updated."""
        original_input_schema = self.config.input_schema
        original_output_schema = self.config.output_schema
        original_system_prompt_generator = self.config.system_prompt_generator
        
        agent = AtomicScraperPlanningAgent(self.config)
        
        # Config should be updated with our schemas
        assert self.config.input_schema == AtomicScraperAgentInputSchema
        assert self.config.output_schema == AtomicScraperAgentOutputSchema
        assert self.config.system_prompt_generator is not None
        assert self.config.system_prompt_generator != original_system_prompt_generator
    
    def test_agent_with_custom_model(self):
        """Test agent initialization with custom model."""
        custom_config = BaseAgentConfig(
            client=self.mock_client,
            model="gpt-4"
        )
        
        agent = AtomicScraperPlanningAgent(custom_config)
        
        assert agent.model == "gpt-4"
    
    def test_agent_context_provider_methods(self):
        """Test agent context provider management methods."""
        agent = AtomicScraperPlanningAgent(self.config)
        
        # Test getting context provider
        context_provider = agent.get_context_provider("scraping_context")
        assert isinstance(context_provider, AtomicScrapingContextProvider)
        
        # Test getting non-existent provider raises error
        with pytest.raises(KeyError):
            agent.get_context_provider("non_existent")
        
        # Test registering new provider
        new_provider = AtomicScrapingContextProvider()
        agent.register_context_provider("test_provider", new_provider)
        
        retrieved_provider = agent.get_context_provider("test_provider")
        assert retrieved_provider == new_provider
        
        # Test unregistering provider
        agent.unregister_context_provider("test_provider")
        
        with pytest.raises(KeyError):
            agent.get_context_provider("test_provider")
        
        # Test unregistering non-existent provider raises error
        with pytest.raises(KeyError):
            agent.unregister_context_provider("non_existent")


class TestRequestParsingAndStrategyCoordination:
    """Test request parsing and strategy coordination functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock client
        self.mock_client = Mock(spec=instructor.client.Instructor)
        
        # Create agent config
        self.config = BaseAgentConfig(
            client=self.mock_client,
            model="gpt-4o-mini"
        )
        
        self.agent = AtomicScraperPlanningAgent(self.config)
    
    def test_parse_natural_language_request_basic(self):
        """Test basic natural language request parsing."""
        request = "scrape Saturday markets"
        parsed = self.agent._parse_natural_language_request(request)
        
        assert parsed['content_type'] == 'list'
        assert 'markets' in parsed['target_data']
        assert 'saturday' in parsed['temporal_filters']
        assert 'saturday' in parsed['keywords']
        assert 'markets' in parsed['keywords']
    
    def test_parse_natural_language_request_detail(self):
        """Test parsing request for detailed information."""
        request = "get detailed information about this product"
        parsed = self.agent._parse_natural_language_request(request)
        
        assert parsed['content_type'] == 'detail'
        assert 'products' in parsed['target_data']
        assert 'detailed' in parsed['keywords']
        assert 'information' in parsed['keywords']
    
    def test_parse_natural_language_request_search(self):
        """Test parsing search-type request."""
        request = "find search results for articles"
        parsed = self.agent._parse_natural_language_request(request)
        
        assert parsed['content_type'] == 'search'
        assert 'articles' in parsed['target_data']
        # 'find' is filtered out as a stop word, so check for other keywords
        assert 'search' in parsed['keywords']
        assert 'results' in parsed['keywords']
    
    def test_parse_natural_language_request_multiple_data_types(self):
        """Test parsing request with multiple data types."""
        request = "scrape market prices and contact information"
        parsed = self.agent._parse_natural_language_request(request)
        
        assert 'markets' in parsed['target_data']
        assert 'prices' in parsed['target_data']
        assert 'contacts' in parsed['target_data']
    
    def test_parse_natural_language_request_location_filters(self):
        """Test parsing request with location filters."""
        request = "find Cape Town markets"
        parsed = self.agent._parse_natural_language_request(request)
        
        assert 'cape town' in parsed['location_filters']
        assert 'markets' in parsed['target_data']
    
    def test_create_basic_schema_recipe_markets(self):
        """Test creating schema recipe for markets."""
        parsed_request = {
            'content_type': 'list',
            'target_data': ['markets', 'locations', 'dates'],
            'keywords': ['saturday', 'markets']
        }
        
        input_data = AtomicScraperAgentInputSchema(
            request="scrape Saturday markets",
            target_url="https://example.com"
        )
        
        schema_recipe = self.agent._create_basic_schema_recipe(parsed_request, input_data)
        
        assert schema_recipe.name == 'saturday_markets_schema'
        assert 'title' in schema_recipe.fields
        assert 'location' in schema_recipe.fields
        assert schema_recipe.fields['title'].required == True
        assert schema_recipe.fields['location'].required == False
    
    def test_create_basic_schema_recipe_products(self):
        """Test creating schema recipe for products."""
        parsed_request = {
            'content_type': 'list',
            'target_data': ['products', 'prices'],
            'keywords': ['product', 'prices']
        }
        
        input_data = AtomicScraperAgentInputSchema(
            request="scrape product prices",
            target_url="https://example.com"
        )
        
        schema_recipe = self.agent._create_basic_schema_recipe(parsed_request, input_data)
        
        assert 'price' in schema_recipe.fields
        assert schema_recipe.fields['price'].extraction_selector == '.price, .cost, .fee, .amount'
        assert 'extract_numbers' in schema_recipe.fields['price'].post_processing
    
    def test_generate_scraping_plan(self):
        """Test generating human-readable scraping plan."""
        from atomic_scraper_tool.models.base_models import ScrapingStrategy
        from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
        
        strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['.market-item', '.listing'],
            pagination_strategy='next_link',
            max_pages=5,
            request_delay=1.5
        )
        
        fields = {
            'title': FieldDefinition(
                field_type='string',
                description='Market name',
                extraction_selector='h2',
                required=True
            ),
            'location': FieldDefinition(
                field_type='string',
                description='Market location',
                extraction_selector='.location',
                required=False
            )
        }
        
        schema_recipe = SchemaRecipe(
            name='test_schema',
            description='Test schema',
            fields=fields
        )
        
        parsed_request = {'content_type': 'list'}
        
        plan = self.agent._generate_scraping_plan(strategy, schema_recipe, parsed_request)
        
        assert 'Scraping Plan for List Data' in plan
        assert 'list' in plan
        assert '.market-item, .listing' in plan
        assert 'next_link' in plan
        assert '**Max Pages**: 5' in plan
        assert '**Request Delay**: 1.5s' in plan
        assert '**Title** (Required)' in plan
        assert '**Location**' in plan
    
    def test_generate_reasoning(self):
        """Test generating reasoning explanation."""
        from atomic_scraper_tool.models.base_models import ScrapingStrategy
        from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
        from atomic_scraper_tool.analysis.website_analyzer import WebsiteStructureAnalysis
        
        analysis = WebsiteStructureAnalysis(
            url='https://example.com',
            title='Test Site',
            metadata={}
        )
        
        strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['.item']
        )
        
        schema_recipe = SchemaRecipe(
            name='test_schema',
            description='Test schema',
            fields={'title': FieldDefinition(
                field_type='string',
                description='Title',
                extraction_selector='h1'
            )}
        )
        
        parsed_request = {
            'keywords': ['test', 'data'],
            'target_data': ['items']
        }
        
        reasoning = self.agent._generate_reasoning(analysis, strategy, schema_recipe, parsed_request)
        
        assert 'Decision Reasoning' in reasoning
        assert 'Strategy Selection' in reasoning
        assert 'list' in reasoning
        assert 'Selector Selection' in reasoning
        assert 'Schema Design' in reasoning
        assert 'Quality Considerations' in reasoning
    
    def test_calculate_confidence_high(self):
        """Test confidence calculation with good inputs."""
        from atomic_scraper_tool.models.base_models import ScrapingStrategy
        from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
        from atomic_scraper_tool.analysis.website_analyzer import WebsiteStructureAnalysis
        
        analysis = WebsiteStructureAnalysis(
            url='https://example.com',
            title='Test Site',
            metadata={}  # No error
        )
        
        strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['.item', '.listing']  # Has selectors
        )
        
        fields = {
            'title': FieldDefinition(
                field_type='string',
                description='Title',
                extraction_selector='h1',
                required=True  # Has required field
            ),
            'description': FieldDefinition(
                field_type='string',
                description='Description',
                extraction_selector='p'
            ),
            'price': FieldDefinition(
                field_type='string',
                description='Price',
                extraction_selector='.price'
            )
        }
        
        schema_recipe = SchemaRecipe(
            name='test_schema',
            description='Test schema',
            fields=fields  # 3 fields = good coverage
        )
        
        confidence = self.agent._calculate_confidence(analysis, strategy, schema_recipe)
        
        assert confidence > 0.7  # Should be high confidence
    
    def test_calculate_confidence_low(self):
        """Test confidence calculation with poor inputs."""
        from atomic_scraper_tool.models.base_models import ScrapingStrategy
        from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
        from atomic_scraper_tool.analysis.website_analyzer import WebsiteStructureAnalysis
        
        analysis = WebsiteStructureAnalysis(
            url='https://example.com',
            title='Test Site',
            metadata={'error': 'Failed to fetch'}  # Has error
        )
        
        strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['div']  # Minimal selector to pass validation
        )
        
        fields = {
            'title': FieldDefinition(
                field_type='string',
                description='Title',
                extraction_selector='h1',
                required=False  # No required fields
            )
        }
        
        schema_recipe = SchemaRecipe(
            name='test_schema',
            description='Test schema',
            fields=fields  # Only 1 field = poor coverage
        )
        
        confidence = self.agent._calculate_confidence(analysis, strategy, schema_recipe)
        
        assert confidence < 0.6  # Should be low confidence
    
    def test_handle_error(self):
        """Test error handling."""
        input_data = AtomicScraperAgentInputSchema(
            request="test request",
            target_url="https://example.com"
        )
        
        result = self.agent._handle_error("Test error message", input_data)
        
        assert isinstance(result, AtomicScraperAgentOutputSchema)
        assert "Error occurred while generating scraping plan" in result.scraping_plan
        assert "Test error message" in result.scraping_plan
        assert result.confidence == 0.2
        assert result.strategy['scrape_type'] == 'list'
        assert result.schema_recipe['name'] == 'error_schema'
    
    @pytest.mark.parametrize("user_request,expected_content_type", [
        ("scrape all items", "list"),
        ("get detailed information", "detail"),
        ("find search results", "search"),
        ("extract multiple products", "list"),
        ("show specific article", "detail")
    ])
    def test_content_type_detection(self, user_request, expected_content_type):
        """Test content type detection from various requests."""
        parsed = self.agent._parse_natural_language_request(user_request)
        assert parsed['content_type'] == expected_content_type
    
    @pytest.mark.parametrize("user_request,expected_data_types", [
        ("scrape market prices", ["markets", "prices"]),
        ("get contact information", ["contacts"]),
        ("find article dates", ["articles", "dates"]),
        ("extract product locations", ["products", "locations"]),
        ("scrape event schedules", ["events", "dates"])
    ])
    def test_data_type_extraction(self, user_request, expected_data_types):
        """Test data type extraction from various requests."""
        parsed = self.agent._parse_natural_language_request(user_request)
        for data_type in expected_data_types:
            assert data_type in parsed['target_data']


if __name__ == "__main__":
    pytest.main([__file__])