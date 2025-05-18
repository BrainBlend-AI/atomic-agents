import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool.webpage_scraper import (  # noqa: E402
    WebpageScraperTool,
    WebpageScraperToolInputSchema,
    WebpageScraperToolOutputSchema,
    WebpageScraperToolConfig,
    WebpageMetadata,
)


@pytest.fixture
def mock_requests_get():
    with patch("tool.webpage_scraper.requests.get") as mock_get:
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="author" content="Test Author">
                <meta name="description" content="Test Description">
                <meta property="og:site_name" content="Test Site">
            </head>
            <body>
                <main>
                    <h1>Test Heading</h1>
                    <p>Test paragraph with <a href="https://example.com">link</a>.</p>
                </main>
            </body>
        </html>
        """
        mock_response.content = mock_response.text.encode("utf-8")
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        # Configure the mock
        mock_get.return_value = mock_response
        yield mock_get


def test_webpage_scraper_tool_basic(mock_requests_get):
    # Initialize the tool
    scraper_tool = WebpageScraperTool(WebpageScraperToolConfig())
    input_schema = WebpageScraperToolInputSchema(url="https://example.com")
    
    # Run the tool
    result = scraper_tool.run(input_schema)
    
    # Assertions
    assert isinstance(result, WebpageScraperToolOutputSchema)
    assert "Test Heading" in result.content
    assert "Test paragraph" in result.content
    assert "link" in result.content
    assert result.metadata.title == "Test Page"
    assert result.metadata.author == "Test Author"
    assert result.metadata.description == "Test Description"
    assert result.metadata.site_name == "Test Site"
    assert result.metadata.domain == "example.com"
    assert result.error is None


def test_webpage_scraper_tool_without_links(mock_requests_get):
    # Initialize the tool
    scraper_tool = WebpageScraperTool(WebpageScraperToolConfig())
    input_schema = WebpageScraperToolInputSchema(url="https://example.com", include_links=False)
    
    # Run the tool
    result = scraper_tool.run(input_schema)
    
    # Assertions
    assert isinstance(result, WebpageScraperToolOutputSchema)
    assert "Test paragraph with link" in result.content
    assert "https://example.com" not in result.content  # Link URL should not be included


def test_webpage_scraper_tool_http_error(mock_requests_get):
    # Configure mock to raise an exception
    mock_requests_get.return_value.raise_for_status.side_effect = Exception("404 Client Error")
    
    # Initialize the tool
    scraper_tool = WebpageScraperTool(WebpageScraperToolConfig())
    input_schema = WebpageScraperToolInputSchema(url="https://example.com/not-found")
    
    # Run the tool
    result = scraper_tool.run(input_schema)
    
    # Assertions
    assert isinstance(result, WebpageScraperToolOutputSchema)
    assert result.content == ""  # Content should be empty
    assert result.metadata.title == "Error retrieving page"
    assert result.metadata.domain == "example.com"
    assert "404 Client Error" in result.error


def test_webpage_scraper_tool_content_too_large(mock_requests_get):
    # Configure mock content to exceed max length
    max_length = 1_000_000
    mock_requests_get.return_value.content = b"a" * (max_length + 1)
    
    # Initialize the tool
    scraper_tool = WebpageScraperTool(WebpageScraperToolConfig(max_content_length=max_length))
    input_schema = WebpageScraperToolInputSchema(url="https://example.com/large-page")
    
    # Run the tool
    result = scraper_tool.run(input_schema)
    
    # Assertions
    assert isinstance(result, WebpageScraperToolOutputSchema)
    assert "exceeds maximum" in result.error


def test_webpage_scraper_tool_extract_metadata():
    # Initialize the tool
    scraper_tool = WebpageScraperTool(WebpageScraperToolConfig())
    
    # Create a minimal soup object with metadata
    soup = MagicMock()
    
    # Create individual mock tags with get methods
    author_tag = MagicMock()
    author_tag.get.return_value = "Author Name"
    
    description_tag = MagicMock()
    description_tag.get.return_value = "Page Description"
    
    site_name_tag = MagicMock()
    site_name_tag.get.return_value = "Site Name"
    
    # Configure find method to return the right mock based on arguments
    def mock_find(tag, attrs=None):
        if tag == "meta" and attrs == {"name": "author"}:
            return author_tag
        elif tag == "meta" and attrs == {"name": "description"}:
            return description_tag
        elif tag == "meta" and attrs == {"property": "og:site_name"}:
            return site_name_tag
        return None
        
    soup.find.side_effect = mock_find
    
    doc = MagicMock()
    doc.title.return_value = "Page Title"
    
    # Call the method directly
    metadata = scraper_tool._extract_metadata(soup, doc, "https://example.org/page")
    
    # Assertions
    assert metadata.title == "Page Title"
    assert metadata.author == "Author Name"
    assert metadata.description == "Page Description"
    assert metadata.site_name == "Site Name"
    assert metadata.domain == "example.org"


def test_webpage_scraper_tool_clean_markdown():
    # Initialize the tool
    scraper_tool = WebpageScraperTool(WebpageScraperToolConfig())
    
    # Input markdown with excess whitespace
    dirty_markdown = """
    # Title
    
    
    
    Paragraph with trailing spaces    
    
    
    * List item 1    
    * List item 2
    
    
    """
    
    # Clean the markdown
    cleaned = scraper_tool._clean_markdown(dirty_markdown)
    
    # Assertions
    assert cleaned.count("\n\n\n") == 0  # No triple newlines
    assert "spaces    \n" not in cleaned  # No trailing spaces
    assert cleaned.endswith("\n")  # Ends with newline


if __name__ == "__main__":
    pytest.main([__file__])