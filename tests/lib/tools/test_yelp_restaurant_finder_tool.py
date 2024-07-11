import pytest
from unittest.mock import patch, Mock
from pydantic import ValidationError

from atomic_agents.lib.tools.yelp_restaurant_finder_tool import (
    YelpSearchTool,
    YelpSearchToolConfig,
    YelpSearchToolSchema,
    YelpSearchToolOutputSchema,
    YelpCategory,
    PriceRange
)
from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.agents.base_agent import BaseAgentIO

# Sample data
SAMPLE_YELP_RESPONSE = {
    "businesses": [
        {
            "name": "Sample Restaurant",
            "url": "https://www.yelp.com/biz/sample-restaurant",
            "rating": 4.5,
            "review_count": 100,
            "location": {"display_address": ["123 Main St", "Sample City, ST 12345"]},
            "display_phone": "+1 (123) 456-7890",
            "categories": [{"title": "Italian"}, {"title": "Pizza"}]
        }
    ]
}

@pytest.fixture
def yelp_search_tool():
    config = YelpSearchToolConfig(api_key="dummy_api_key", max_results=10)
    return YelpSearchTool(config)

def test_yelp_search_tool_initialization(yelp_search_tool):
    assert isinstance(yelp_search_tool, BaseTool)
    assert yelp_search_tool.api_key == "dummy_api_key"
    assert yelp_search_tool.max_results == 10

def test_yelp_search_tool_input_schema():
    assert issubclass(YelpSearchToolSchema, BaseAgentIO)
    assert "location" in YelpSearchToolSchema.model_fields
    assert "term" in YelpSearchToolSchema.model_fields
    assert "categories" in YelpSearchToolSchema.model_fields
    assert "price" in YelpSearchToolSchema.model_fields

def test_yelp_search_tool_output_schema():
    assert issubclass(YelpSearchToolOutputSchema, BaseAgentIO)
    assert "results" in YelpSearchToolOutputSchema.model_fields

@patch('atomic_agents.lib.tools.yelp_restaurant_finder_tool.requests.get')
def test_run_success(mock_get, yelp_search_tool):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_YELP_RESPONSE
    mock_get.return_value = mock_response

    input_data = YelpSearchToolSchema(
        location="Sample City",
        term="pizza",
        categories=[YelpCategory.ITALIAN],
        price=[PriceRange.TWO, PriceRange.THREE]
    )
    result = yelp_search_tool.run(input_data)

    assert isinstance(result, YelpSearchToolOutputSchema)
    assert len(result.results) == 1
    assert result.results[0].name == "Sample Restaurant"
    assert result.results[0].rating == 4.5
    assert result.results[0].review_count == 100
    assert result.results[0].address == "123 Main St, Sample City, ST 12345"
    assert result.results[0].phone == "+1 (123) 456-7890"
    assert result.results[0].categories == ["Italian", "Pizza"]

    mock_get.assert_called_once()
    call_args = mock_get.call_args[1]
    assert call_args['headers'] == {"Authorization": "Bearer dummy_api_key"}
    assert call_args['params']['location'] == "Sample City"
    assert call_args['params']['term'] == "pizza"
    assert call_args['params']['categories'] == "italian"
    assert call_args['params']['price'] == "2,3"

@patch('atomic_agents.lib.tools.yelp_restaurant_finder_tool.requests.get')
def test_run_api_error(mock_get, yelp_search_tool):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.reason = "Bad Request"
    mock_get.return_value = mock_response

    input_data = YelpSearchToolSchema(location="Sample City")

    with pytest.raises(Exception, match="Failed to fetch search results: 400 Bad Request"):
        yelp_search_tool.run(input_data)

@patch('atomic_agents.lib.tools.yelp_restaurant_finder_tool.requests.get')
def test_run_with_all_parameters(mock_get, yelp_search_tool):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_YELP_RESPONSE
    mock_get.return_value = mock_response

    input_data = YelpSearchToolSchema(
        location="Sample City",
        term="pizza",
        categories=[YelpCategory.ITALIAN, YelpCategory.PIZZA],
        price=[PriceRange.TWO, PriceRange.THREE],
        open_now=True,
        sort_by="rating"
    )
    yelp_search_tool.run(input_data)

    mock_get.assert_called_once()
    call_args = mock_get.call_args[1]
    assert call_args['params']['location'] == "Sample City"
    assert call_args['params']['term'] == "pizza"
    assert call_args['params']['categories'] == "italian,pizza"
    assert call_args['params']['price'] == "2,3"
    assert call_args['params']['open_now'] is True
    assert call_args['params']['sort_by'] == "rating"

@patch('atomic_agents.lib.tools.yelp_restaurant_finder_tool.requests.get')
def test_run_no_results(mock_get, yelp_search_tool):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"businesses": []}
    mock_get.return_value = mock_response

    input_data = YelpSearchToolSchema(location="Sample City")
    result = yelp_search_tool.run(input_data)

    assert isinstance(result, YelpSearchToolOutputSchema)
    assert len(result.results) == 0

def test_run_missing_api_key():
    config = YelpSearchToolConfig(api_key="", max_results=10)
    tool = YelpSearchTool(config)
    input_data = YelpSearchToolSchema(location="Sample City")

    with pytest.raises(ValueError, match="API key is required to use the Yelp API."):
        tool.run(input_data)