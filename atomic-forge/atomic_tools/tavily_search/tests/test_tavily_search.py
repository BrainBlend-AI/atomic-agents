from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from tavily_search import TavilySearchTool, TavilySearchToolConfig, TavilySearchToolInputSchema


@pytest.fixture
def mock_config():
    return TavilySearchToolConfig(api_key="test_api_key", max_results=5)


@pytest.fixture
def tool(mock_config):
    return TavilySearchTool(config=mock_config)


class TestTavilySearchTool:
    @pytest.mark.asyncio
    async def test_fetch_search_results_respects_max_results_override(self, tool):
        """Regression test: max_results override must propagate to the API call, not be ignored."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "results": [
                    {"title": f"Result {i}", "url": f"http://example.com/{i}", "content": "...", "score": 1.0 - i * 0.1}
                    for i in range(5)
                ],
                "answer": "test answer",
            }
        )
        mock_response.reason = "OK"
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        result = await tool._fetch_search_results(mock_session, "test query", max_results=2)

        # The key assertion: the API must have been called with max_results=2, not self.max_results=5
        call_args = mock_session.post.call_args
        json_data = call_args.kwargs["json"]
        assert json_data["max_results"] == 2, "max_results override was ignored in API call"

    @pytest.mark.asyncio
    async def test_run_async_respects_max_results_override(self, tool):
        """Runtime max_results override must reach the API and limit result count."""
        mock_session = AsyncMock()

        async def mock_post(*args, **kwargs):
            max_override = kwargs["json"]["max_results"]
            return AsyncMock(
                status=200,
                reason="OK",
                json=AsyncMock(
                    return_value={
                        "results": [
                            {"title": f"Result {i}", "url": f"http://example.com/{i}", "content": "...", "score": 1.0}
                            for i in range(max_override + 3)  # Return MORE than requested
                        ],
                        "answer": "test answer",
                    }
                ),
            )

        mock_session.post = mock_post
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        params = TavilySearchToolInputSchema(queries=["test query"])
        output = await tool.run_async(params, max_results=2)

        # Should have exactly 2 results since we requested 2, even though API returned 5
        assert len(output.results) == 2
        for call in mock_session.post.call_args_list:
            assert call.kwargs["json"]["max_results"] == 2

    @pytest.mark.asyncio
    async def test_run_async_uses_default_when_no_override(self, tool):
        """When no override is passed, self.max_results should be used."""
        mock_session = AsyncMock()

        async def mock_post(*args, **kwargs):
            return AsyncMock(
                status=200,
                reason="OK",
                json=AsyncMock(
                    return_value={
                        "results": [
                            {"title": f"Result {i}", "url": f"http://example.com/{i}", "content": "...", "score": 1.0}
                            for i in range(5)
                        ],
                        "answer": "test answer",
                    }
                ),
            )

        mock_session.post = mock_post
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        params = TavilySearchToolInputSchema(queries=["test query"])
        output = await tool.run_async(params)  # No max_results override

        for call in mock_session.post.call_args_list:
            assert call.kwargs["json"]["max_results"] == 5  # Should use config default (5)

    def test_init_defaults(self):
        """Default config should set max_results to 5."""
        tool = TavilySearchTool()
        assert tool.max_results == 5
        assert tool.search_depth == "basic"

    def test_config_respects_custom_max_results(self):
        """Config should accept and store custom max_results."""
        config = TavilySearchToolConfig(max_results=10)
        tool = TavilySearchTool(config=config)
        assert tool.max_results == 10
