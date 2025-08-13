"""
Unit tests for reasoning and explanation generation in the scraper planning agent.

Tests the enhanced reasoning capabilities added in task 6.3.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from atomic_scraper_tool.agents.scraper_planning_agent import AtomicScraperPlanningAgent, AtomicScraperAgentInputSchema
from atomic_scraper_tool.models.base_models import ScrapingStrategy
from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition
from atomic_agents.agents.base_agent import BaseAgentConfig


class TestReasoningGeneration:
    """Test cases for reasoning and explanation generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock config with all required attributes
        self.mock_config = Mock()
        self.mock_config.client = Mock()
        self.mock_config.model = "test-model"
        self.mock_config.memory = None
        self.mock_config.system_prompt_generator = None
        self.mock_config.input_schema = None
        self.mock_config.output_schema = None
        self.mock_config.system_role = None
        self.mock_config.model_api_parameters = {}
        self.mock_config.temperature = None
        
        # Create agent instance
        self.agent = AtomicScraperPlanningAgent(self.mock_config)
        
        # Create test data
        self.test_parsed_request = {
            'content_type': 'list',
            'target_data': ['markets', 'prices', 'locations'],
            'keywords': ['farmers', 'market', 'cape', 'town'],
            'temporal_filters': ['saturday'],
            'location_filters': ['cape town']
        }
        
        self.test_strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['.market-item', '.listing', 'article'],
            pagination_strategy='next_link',
            max_pages=5,
            request_delay=1.5,
            extraction_rules={'title': 'h2', 'price': '.price'}
        )
        
        self.test_schema_recipe = SchemaRecipe(
            name='farmers_market_schema',
            description='Schema for extracting farmers market data',
            fields={
                'title': FieldDefinition(
                    field_type='string',
                    description='Market name',
                    extraction_selector='h1, h2, .title',
                    required=True,
                    quality_weight=0.9,
                    post_processing=['trim', 'clean']
                ),
                'location': FieldDefinition(
                    field_type='string',
                    description='Market location',
                    extraction_selector='.location, .address',
                    required=False,
                    quality_weight=0.8,
                    post_processing=['trim']
                ),
                'price': FieldDefinition(
                    field_type='string',
                    description='Entry price',
                    extraction_selector='.price, .cost',
                    required=False,
                    quality_weight=0.7,
                    post_processing=['extract_numbers']
                )
            },
            validation_rules=['normalize_whitespace'],
            quality_weights={'completeness': 0.4, 'accuracy': 0.4, 'consistency': 0.2}
        )
        
        # Create mock website analysis
        self.mock_analysis = Mock()
        self.mock_analysis.url = 'https://example.com'
        self.mock_analysis.title = 'Test Website'
        self.mock_analysis.content_patterns = [
            {'type': 'list', 'confidence': 0.8},
            {'type': 'article', 'confidence': 0.6}
        ]
        self.mock_analysis.metadata = {}
    
    def test_generate_reasoning_comprehensive(self):
        """Test comprehensive reasoning generation."""
        reasoning = self.agent._generate_reasoning(
            self.mock_analysis,
            self.test_strategy,
            self.test_schema_recipe,
            self.test_parsed_request
        )
        
        # Check that all major sections are present
        assert "## Decision Reasoning & Analysis" in reasoning
        assert "### Request Analysis" in reasoning
        assert "### Website Analysis" in reasoning
        assert "### Strategy Selection" in reasoning
        assert "### Selector Strategy" in reasoning
        assert "### Schema Design" in reasoning
        assert "### Quality Assurance" in reasoning
        assert "### Risk Assessment" in reasoning
        assert "### Recommendations" in reasoning
        
        # Check specific content
        assert "Content type identified: 'list'" in reasoning
        assert "farmers, market, cape, town" in reasoning
        assert "saturday" in reasoning
        assert "cape town" in reasoning
        assert "Successfully analyzed website" in reasoning
        assert "Selected 'list' strategy because" in reasoning
    
    def test_generate_reasoning_with_website_error(self):
        """Test reasoning generation when website analysis fails."""
        # Set up analysis with error
        error_analysis = Mock()
        error_analysis.url = 'https://example.com'
        error_analysis.metadata = {'error': 'Connection timeout'}
        
        reasoning = self.agent._generate_reasoning(
            error_analysis,
            self.test_strategy,
            self.test_schema_recipe,
            self.test_parsed_request
        )
        
        assert "Website analysis failed: Connection timeout" in reasoning
        assert "Falling back to common web patterns" in reasoning
    
    def test_get_strategy_reasoning_list(self):
        """Test strategy reasoning for list scraping."""
        reasons = self.agent._get_strategy_reasoning(
            self.test_strategy,
            self.test_parsed_request,
            self.mock_analysis
        )
        
        assert len(reasons) > 0
        assert any("multiple items need to be extracted" in reason for reason in reasons)
        assert any("bulk data collection" in reason for reason in reasons)
        assert any("User explicitly requested list-type content" in reason for reason in reasons)
    
    def test_get_strategy_reasoning_detail(self):
        """Test strategy reasoning for detail scraping."""
        detail_strategy = ScrapingStrategy(
            scrape_type='detail',
            target_selectors=['article', '.content']
        )
        
        detail_request = self.test_parsed_request.copy()
        detail_request['content_type'] = 'detail'
        
        reasons = self.agent._get_strategy_reasoning(
            detail_strategy,
            detail_request,
            self.mock_analysis
        )
        
        assert any("detailed information extraction" in reason for reason in reasons)
        assert any("comprehensive data capture" in reason for reason in reasons)
        assert any("User explicitly requested detailed information" in reason for reason in reasons)
    
    def test_get_selector_reasoning(self):
        """Test selector reasoning generation."""
        reasons = self.agent._get_selector_reasoning(
            self.test_strategy,
            self.test_parsed_request
        )
        
        assert len(reasons) > 0
        assert any("Common HTML patterns" in reason for reason in reasons)
        assert any("Semantic HTML elements" in reason for reason in reasons)
        assert any("markets, prices, locations" in reason for reason in reasons)
        assert any("Fallback selectors" in reason for reason in reasons)
    
    def test_get_schema_reasoning(self):
        """Test schema reasoning generation."""
        reasons = self.agent._get_schema_reasoning(
            self.test_schema_recipe,
            self.test_parsed_request
        )
        
        assert len(reasons) > 0
        assert any("3 fields with 1 required fields" in reason for reason in reasons)
        assert any("user criteria and content type analysis" in reason for reason in reasons)
        assert any("markets, prices, locations" in reason for reason in reasons)
        assert any("Quality weights assigned" in reason for reason in reasons)
    
    def test_get_quality_reasoning(self):
        """Test quality reasoning generation."""
        reasons = self.agent._get_quality_reasoning(
            self.test_schema_recipe,
            self.test_strategy
        )
        
        assert len(reasons) > 0
        assert any("Required fields ensure minimum data completeness" in reason for reason in reasons)
        assert any("Quality weights prioritize critical information" in reason for reason in reasons)
        assert any("Post-processing steps clean and normalize" in reason for reason in reasons)
    
    def test_explain_selector(self):
        """Test CSS selector explanation."""
        explanations = {
            'div': 'Generic container elements',
            'article': 'Semantic article content',
            'h1': 'Main headings',
            '.title': 'Elements with title class',
            '.custom-selector': 'Custom selector for specific content'
        }
        
        for selector, expected in explanations.items():
            result = self.agent._explain_selector(selector)
            if selector == '.custom-selector':
                assert result == 'Custom selector for specific content'
            else:
                assert result == expected
    
    def test_assess_risks(self):
        """Test risk assessment functionality."""
        risks = self.agent._assess_risks(
            self.mock_analysis,
            self.test_strategy,
            self.test_schema_recipe
        )
        
        # Should be a list (may be empty for good configurations)
        assert isinstance(risks, list)
    
    def test_assess_risks_with_problems(self):
        """Test risk assessment with problematic configuration."""
        # Create problematic strategy
        bad_strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['div', 'span'],  # Generic selectors
            max_pages=1  # No pagination
        )
        
        # Create schema with no required fields
        bad_schema = SchemaRecipe(
            name='bad_schema',
            description='Bad schema',
            fields={
                'field1': FieldDefinition(
                    field_type='string',
                    description='Field 1',
                    extraction_selector='div',
                    required=False,
                    quality_weight=0.1
                )
            }
        )
        
        # Create analysis with error
        error_analysis = Mock()
        error_analysis.metadata = {'error': 'Failed to analyze'}
        
        risks = self.agent._assess_risks(error_analysis, bad_strategy, bad_schema)
        
        assert len(risks) > 0
        assert any("Website analysis failed" in risk for risk in risks)
        assert any("Generic selectors" in risk for risk in risks)
        assert any("No required fields" in risk for risk in risks)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        recommendations = self.agent._generate_recommendations(
            self.mock_analysis,
            self.test_strategy,
            self.test_schema_recipe,
            self.test_parsed_request
        )
        
        assert len(recommendations) > 0
        assert any("Test the strategy on a small sample" in rec for rec in recommendations)
        assert any("Monitor quality scores" in rec for rec in recommendations)
        assert any("markets, prices, locations" in rec for rec in recommendations)
    
    def test_calculate_confidence_comprehensive(self):
        """Test comprehensive confidence calculation."""
        confidence = self.agent._calculate_confidence(
            self.mock_analysis,
            self.test_strategy,
            self.test_schema_recipe
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably confident with good inputs
    
    def test_calculate_strategy_confidence(self):
        """Test strategy confidence calculation."""
        confidence = self.agent._calculate_strategy_confidence(self.test_strategy)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Good strategy should have decent confidence
    
    def test_calculate_schema_confidence(self):
        """Test schema confidence calculation."""
        confidence = self.agent._calculate_schema_confidence(self.test_schema_recipe)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Good schema should have decent confidence
    
    def test_calculate_selector_confidence(self):
        """Test selector confidence calculation."""
        confidence = self.agent._calculate_selector_confidence(self.test_strategy)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.2  # Should have some confidence with selectors
    
    def test_apply_confidence_modifiers(self):
        """Test confidence modifiers application."""
        base_confidence = 0.8
        
        modified_confidence = self.agent._apply_confidence_modifiers(
            base_confidence,
            self.mock_analysis,
            self.test_strategy,
            self.test_schema_recipe
        )
        
        assert 0.0 <= modified_confidence <= 1.0
        # May be higher or lower than base depending on modifiers
    
    def test_confidence_with_high_risk_scenario(self):
        """Test confidence calculation with high-risk scenario."""
        # Create high-risk configuration
        risky_strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['div'],  # Very generic
            max_pages=20  # Too many pages
        )
        
        large_schema = SchemaRecipe(
            name='large_schema',
            description='Large schema',
            fields={f'field_{i}': FieldDefinition(
                field_type='string',
                description=f'Field {i}',
                extraction_selector='div',
                required=False,
                quality_weight=0.1
            ) for i in range(12)}  # Too many fields
        )
        
        error_analysis = Mock()
        error_analysis.metadata = {'error': 'Analysis failed'}
        
        confidence = self.agent._calculate_confidence(
            error_analysis,
            risky_strategy,
            large_schema
        )
        
        assert confidence < 0.5  # Should have low confidence
    
    def test_reasoning_sections_completeness(self):
        """Test that all reasoning sections contain meaningful content."""
        reasoning = self.agent._generate_reasoning(
            self.mock_analysis,
            self.test_strategy,
            self.test_schema_recipe,
            self.test_parsed_request
        )
        
        # Split into sections
        sections = reasoning.split('###')
        
        # Each section should have substantial content
        for section in sections[1:]:  # Skip the header
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            assert len(lines) >= 2  # Should have at least the title and some content
    
    def test_reasoning_with_minimal_data(self):
        """Test reasoning generation with minimal input data."""
        minimal_request = {
            'content_type': 'list',
            'target_data': [],
            'keywords': [],
            'temporal_filters': [],
            'location_filters': []
        }
        
        minimal_strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['div']
        )
        
        minimal_schema = SchemaRecipe(
            name='minimal_schema',
            description='Minimal schema',
            fields={
                'title': FieldDefinition(
                    field_type='string',
                    description='Title',
                    extraction_selector='h1',
                    required=True
                )
            }
        )
        
        reasoning = self.agent._generate_reasoning(
            self.mock_analysis,
            minimal_strategy,
            minimal_schema,
            minimal_request
        )
        
        # Should still generate comprehensive reasoning
        assert len(reasoning) > 500  # Should be substantial
        assert "general content" in reasoning  # Should handle empty target_data
        assert "none specific" in reasoning  # Should handle empty keywords


class TestConfidenceScoring:
    """Test cases specifically for confidence scoring system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_config.client = Mock()
        self.mock_config.model = "test-model"
        self.mock_config.memory = None
        self.mock_config.system_prompt_generator = None
        self.mock_config.input_schema = None
        self.mock_config.output_schema = None
        self.mock_config.system_role = None
        self.mock_config.model_api_parameters = {}
        self.mock_config.temperature = None
        self.agent = AtomicScraperPlanningAgent(self.mock_config)
    
    def test_confidence_perfect_scenario(self):
        """Test confidence with perfect inputs."""
        perfect_analysis = Mock()
        perfect_analysis.metadata = {}
        perfect_analysis.content_patterns = [{'type': 'list'}]
        
        perfect_strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['.specific-class', '#unique-id', 'article.content'],
            pagination_strategy='next_link',
            max_pages=3
        )
        
        perfect_schema = SchemaRecipe(
            name='perfect_schema',
            description='Perfect schema',
            fields={
                'title': FieldDefinition(
                    field_type='string',
                    description='Title',
                    extraction_selector='h1.title',
                    required=True,
                    quality_weight=0.9,
                    post_processing=['clean']
                ),
                'content': FieldDefinition(
                    field_type='string',
                    description='Content',
                    extraction_selector='.content',
                    required=True,
                    quality_weight=0.8,
                    post_processing=['clean']
                ),
                'date': FieldDefinition(
                    field_type='string',
                    description='Date',
                    extraction_selector='time.published',
                    required=False,
                    quality_weight=0.7
                )
            }
        )
        
        confidence = self.agent._calculate_confidence(
            perfect_analysis,
            perfect_strategy,
            perfect_schema
        )
        
        assert confidence > 0.8  # Should be very confident
    
    def test_confidence_worst_scenario(self):
        """Test confidence with worst-case inputs."""
        bad_analysis = Mock()
        bad_analysis.metadata = {'error': 'Complete failure'}
        
        bad_strategy = ScrapingStrategy(
            scrape_type='list',
            target_selectors=['div'],  # Generic selector
            max_pages=50  # Too many pages
        )
        
        bad_schema = SchemaRecipe(
            name='bad_schema',
            description='Bad schema',
            fields={
                'field1': FieldDefinition(
                    field_type='string',
                    description='Bad field',
                    extraction_selector='div',
                    required=False,
                    quality_weight=0.1
                )
            }
        )
        
        confidence = self.agent._calculate_confidence(
            bad_analysis,
            bad_strategy,
            bad_schema
        )
        
        assert confidence < 0.3  # Should have very low confidence


if __name__ == "__main__":
    pytest.main([__file__])