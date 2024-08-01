import pytest
from unittest.mock import patch, MagicMock
from atomic_agents.lib.tools.content_scraping_tool import (
    ContentScrapingTool,
    ContentScrapingToolInputSchema,
    ContentScrapingToolOutputSchema,
    ContentScrapingToolConfig,
)
from atomic_agents.lib.tools.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.utils.scraping.pdf_to_markdown import PdfToMarkdownConverter
from atomic_agents.lib.utils.scraping.url_to_markdown import UrlToMarkdownConverter


def test_content_scraping_tool_initialization():
    tool = ContentScrapingTool()
    assert isinstance(tool, BaseTool)
    assert tool.tool_name == "ContentScrapingToolInputSchema"
    assert "Tool for scraping web pages or PDFs" in tool.tool_description


def test_content_scraping_tool_with_custom_config():
    config = ContentScrapingToolConfig(title="Custom Scraper", description="Custom description")
    tool = ContentScrapingTool(config=config)
    assert tool.tool_name == "Custom Scraper"
    assert tool.tool_description == "Custom description"


def test_content_scraping_tool_input_schema():
    tool = ContentScrapingTool()
    assert tool.input_schema == ContentScrapingToolInputSchema


def test_content_scraping_tool_output_schema():
    tool = ContentScrapingTool()
    assert tool.output_schema == ContentScrapingToolOutputSchema


@pytest.mark.parametrize(
    "content_type, expected_converter",
    [
        ("application/pdf", PdfToMarkdownConverter),
        ("text/html", UrlToMarkdownConverter),
    ],
)
@patch("atomic_agents.lib.tools.content_scraping_tool.requests.head")
def test_content_scraping_tool_run(mock_head, content_type, expected_converter):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": content_type}
    mock_head.return_value = mock_response

    mock_document = MagicMock()
    mock_document.content = "Mocked content"
    mock_document.metadata.model_dump.return_value = {"key": "value"}

    with patch.object(expected_converter, "convert", return_value=mock_document):
        tool = ContentScrapingTool()
        result = tool.run(ContentScrapingToolInputSchema(url="https://example.com"))

    assert isinstance(result, ContentScrapingToolOutputSchema)
    assert result.content == "Mocked content"
    assert result.metadata == {"key": "value"}


@patch("atomic_agents.lib.tools.content_scraping_tool.requests.head")
def test_content_scraping_tool_run_unknown_content_type(mock_head):
    mock_response = MagicMock()
    mock_response.headers = {"Content-Type": "unknown/type"}
    mock_head.return_value = mock_response

    mock_document = MagicMock()
    mock_document.content = "Mocked content"
    mock_document.metadata.model_dump.return_value = {"key": "value"}

    with patch.object(UrlToMarkdownConverter, "convert", return_value=mock_document):
        tool = ContentScrapingTool()
        result = tool.run(ContentScrapingToolInputSchema(url="https://example.com"))

    assert isinstance(result, ContentScrapingToolOutputSchema)
    assert result.content == "Mocked content"
    assert result.metadata == {"key": "value"}


def test_content_scraping_tool_schema_fields():
    schema = ContentScrapingToolInputSchema(url="https://example.com")
    assert schema.url == "https://example.com"


def test_content_scraping_tool_output_schema_fields():
    output = ContentScrapingToolOutputSchema(content="Test content", metadata={"key": "value"})
    assert output.content == "Test content"
    assert output.metadata == {"key": "value"}


def test_content_scraping_tool_config_is_pydantic_model():
    assert issubclass(ContentScrapingToolConfig, BaseToolConfig)


def test_content_scraping_tool_config_optional_fields():
    config = ContentScrapingToolConfig()
    assert hasattr(config, "title")
    assert hasattr(config, "description")
