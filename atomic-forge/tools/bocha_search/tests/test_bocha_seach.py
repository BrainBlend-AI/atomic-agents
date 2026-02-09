import os
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool.bocha_search import (  # noqa: E402
    BoChaSearchTool,
    BoChaSearchToolInputSchema,
    BoChaSearchToolConfig,
    BoChaSearchToolOutputSchema,
    # BoChaSearchResultItemSchema,
)


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp.ClientSession for all tests"""
    with patch("tool.bocha_search.aiohttp.ClientSession") as mock_session_class:
        mock_session = MagicMock()

        # Default mock response
        mock_response = SimpleNamespace(
            status=200,
            json=AsyncMock(
                return_value={
                    "data": {
                        "webPages": {
                            "value": [
                                {
                                    "name": "Mock Title",
                                    "url": "https://example.com",
                                    "snippet": "Mock content",
                                }
                            ]
                        }
                    }
                }
            ),
        )
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        yield mock_session


@pytest.mark.asyncio
async def test_bocha_search_tool_missing_fields(mock_aiohttp_session):
    """Test that results missing required fields are skipped"""
    mock_api_key = "KEY"
    mock_query = "test query"
    mock_response_data = {
        "data": {
            "webPages": {
                "value": [
                    {"name": "Missing URL", "snippet": "Content"},
                    {"url": "https://example.com", "snippet": "Content"},
                    {"name": "Valid Result", "url": "https://example.com/valid", "snippet": "Valid content"},
                ]
            }
        }
    }

    mock_aiohttp_session.post.return_value.__aenter__.return_value.json.return_value = mock_response_data

    tool = BoChaSearchTool(BoChaSearchToolConfig(api_key=mock_api_key))
    input_schema = BoChaSearchToolInputSchema(queries=[mock_query])

    result: BoChaSearchToolOutputSchema = await tool.run_async(input_schema)

    assert len(result.results) == 1
    assert result.results[0].name == "Valid Result"


def test_bocha_search_tool_sync_run(mock_aiohttp_session):
    """Test the synchronous run method"""
    mock_api_key = "KEY"
    mock_query = "sync query"
    mock_response_data = {
        "data": {"webPages": {"value": [{"name": "Sync Result", "url": "https://example.com", "snippet": "Sync content"}]}}
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_response_data
    mock_aiohttp_session.post.return_value.__aenter__.return_value = mock_response

    tool = BoChaSearchTool(BoChaSearchToolConfig(api_key=mock_api_key))
    input_schema = BoChaSearchToolInputSchema(queries=[mock_query])
    result = tool.run(input_schema)

    assert len(result.results) == 1
    assert result.results[0].name == "Sync Result"


@pytest.mark.asyncio
async def test_bocha_search_tool_max_results(mock_aiohttp_session):
    """Test max_results parameter"""
    mock_api_key = "KEY"
    mock_query = "max results query"

    mock_response_data = {
        "data": {
            "webPages": {
                "value": [
                    {"name": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"Content {i}"} for i in range(10)
                ]
            }
        }
    }

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_response_data
    mock_aiohttp_session.post.return_value.__aenter__.return_value = mock_response

    tool = BoChaSearchTool(BoChaSearchToolConfig(api_key=mock_api_key, count=10))
    input_schema = BoChaSearchToolInputSchema(queries=[mock_query])

    # Test limiting to 5 results
    result = await tool.run_async(input_schema, max_results=5)
    assert len(result.results) == 5

    # Test default count from config
    mock_aiohttp_session.post.reset_mock()
    result2 = await tool.run_async(input_schema)
    assert len(result2.results) == 10


@pytest.mark.asyncio
async def test_bocha_search_tool_no_results(mock_aiohttp_session):
    """Test behavior when no results returned"""
    mock_api_key = "KEY"
    mock_query = "empty query"

    mock_response_data = {"data": {"webPages": {"value": []}}}
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = mock_response_data
    mock_aiohttp_session.post.return_value.__aenter__.return_value = mock_response

    tool = BoChaSearchTool(BoChaSearchToolConfig(api_key=mock_api_key))
    input_schema = BoChaSearchToolInputSchema(queries=[mock_query])
    result = await tool.run_async(input_schema)

    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_bocha_search_tool_http_error(mock_aiohttp_session):
    """Test that HTTP errors raise an exception"""
    mock_api_key = "KEY"
    mock_query = "error query"

    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.reason = "Internal Server Error"
    mock_response.text = AsyncMock(return_value="Server error")
    mock_aiohttp_session.post.return_value.__aenter__.return_value = mock_response

    tool = BoChaSearchTool(BoChaSearchToolConfig(api_key=mock_api_key))
    input_schema = BoChaSearchToolInputSchema(queries=[mock_query])

    with pytest.raises(Exception) as excinfo:
        await tool.run_async(input_schema)

    assert "Failed to fetch search results" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main([__file__])
