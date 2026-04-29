from unittest.mock import AsyncMock, patch

import pytest

from tool.hackernews_search import (
    HackerNewsItem,
    HackerNewsSearchTool,
    HackerNewsSearchToolConfig,
    HackerNewsSearchToolInputSchema,
    HackerNewsSearchToolOutputSchema,
)


SAMPLE_HITS = [
    {
        "objectID": "12345",
        "title": "Show HN: Atomic Agents",
        "url": "https://example.com/atomic",
        "author": "alice",
        "points": 250,
        "num_comments": 42,
        "created_at": "2026-04-01T12:00:00Z",
    },
    {
        "objectID": "67890",
        "story_title": "MCP Server Roundup",
        "story_url": "https://example.com/mcp",
        "comment_text": "Best discussion on this so far.",
        "author": "bob",
        "points": None,
        "num_comments": None,
        "created_at": "2026-04-15T09:30:00Z",
        "parent_id": 67889,
        "story_id": 67889,
    },
]


@pytest.fixture
def tool():
    return HackerNewsSearchTool(config=HackerNewsSearchToolConfig())


def test_to_item_story(tool):
    item = HackerNewsSearchTool._to_item(SAMPLE_HITS[0], "atomic")
    assert isinstance(item, HackerNewsItem)
    assert item.object_id == "12345"
    assert item.title == "Show HN: Atomic Agents"
    assert item.url == "https://example.com/atomic"
    assert item.hn_url == "https://news.ycombinator.com/item?id=12345"
    assert item.points == 250
    assert item.num_comments == 42


def test_to_item_comment(tool):
    """Comments come back with story_title/story_url and parent/story ids."""
    item = HackerNewsSearchTool._to_item(SAMPLE_HITS[1], "MCP")
    assert item.title == "MCP Server Roundup"  # falls back to story_title
    assert item.url == "https://example.com/mcp"
    assert item.comment_text == "Best discussion on this so far."
    assert item.parent_id == "67889"
    assert item.story_id == "67889"


@pytest.mark.asyncio
async def test_run_async_uses_correct_endpoint(tool):
    """Sort by date should hit search_by_date; relevance hits search."""
    captured: list[str] = []

    async def fake_get_text(self, session, query, tags, sort_by, max_results, numeric_filters):
        endpoint = "search_by_date" if sort_by == "date" else "search"
        captured.append(endpoint)
        return [HackerNewsSearchTool._to_item(SAMPLE_HITS[0], query)]

    with patch.object(HackerNewsSearchTool, "_fetch", fake_get_text):
        await tool.run_async(HackerNewsSearchToolInputSchema(queries=["a"], sort_by="date"))
        await tool.run_async(HackerNewsSearchToolInputSchema(queries=["b"], sort_by="relevance"))
    assert captured == ["search_by_date", "search"]


@pytest.mark.asyncio
async def test_run_async_aggregates_results(tool):
    async def fake_fetch(self, session, query, *_):
        return [HackerNewsSearchTool._to_item(hit, query) for hit in SAMPLE_HITS]

    with patch.object(HackerNewsSearchTool, "_fetch", fake_fetch):
        out = await tool.run_async(HackerNewsSearchToolInputSchema(queries=["q1", "q2"]))

    assert isinstance(out, HackerNewsSearchToolOutputSchema)
    assert len(out.results) == 4
    assert {r.query for r in out.results} == {"q1", "q2"}


@pytest.mark.asyncio
async def test_run_async_skips_failing_query(tool):
    async def fake_fetch(self, session, query, *_):
        if query == "bad":
            raise Exception("rate limited")
        return [HackerNewsSearchTool._to_item(SAMPLE_HITS[0], query)]

    with patch.object(HackerNewsSearchTool, "_fetch", fake_fetch):
        out = await tool.run_async(HackerNewsSearchToolInputSchema(queries=["bad", "good"]))

    assert len(out.results) == 1
    assert out.results[0].query == "good"


def test_run_invokes_run_async(tool):
    sentinel = HackerNewsSearchToolOutputSchema(results=[])
    with patch.object(HackerNewsSearchTool, "run_async", AsyncMock(return_value=sentinel)):
        out = tool.run(HackerNewsSearchToolInputSchema(queries=["x"]))
    assert out is sentinel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
