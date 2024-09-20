import pytest
import requests
from unittest.mock import patch, Mock, mock_open
from io import BytesIO
from atomic_agents.lib.utils.scraping.pdf_to_markdown import PdfToMarkdownConverter
from atomic_agents.lib.models.web_document import WebDocument, WebDocumentMetadata
from PyPDF2.errors import PdfReadError

# Sample PDF content (mock)
SAMPLE_PDF_CONTENT = b"""%PDF-1.3
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 51 >>
stream
BT /F1 12 Tf 72 712 Td (Sample PDF content) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000198 00000 n 
trailer << /Size 5 /Root 1 0 R >>
startxref
298
%%EOF"""


@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        response = Mock()
        response.content = SAMPLE_PDF_CONTENT
        response.raise_for_status.return_value = None
        mock_get.return_value = response
        yield mock_get

@pytest.fixture
def mock_pdf_reader():
    with patch('PyPDF2.PdfReader') as MockPdfReader:
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF content"
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        MockPdfReader.return_value = mock_reader
        yield MockPdfReader

def test_fetch_pdf_content(mock_requests_get):
    url = "https://example.com/sample.pdf"
    content = PdfToMarkdownConverter._fetch_pdf_content(url)
    
    mock_requests_get.assert_called_once_with(url)
    assert isinstance(content, BytesIO)
    assert content.getvalue() == SAMPLE_PDF_CONTENT

def test_fetch_pdf_content_error(mock_requests_get):
    mock_requests_get.return_value.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    
    with pytest.raises(requests.HTTPError):
        PdfToMarkdownConverter._fetch_pdf_content("https://example.com/nonexistent.pdf")

def test_read_pdf():
    file = BytesIO(SAMPLE_PDF_CONTENT)
    
    mock_page = Mock()
    mock_page.extract_text.return_value = "Sample PDF content"
    
    mock_reader = Mock()
    mock_reader.pages = [mock_page]
    
    with patch('atomic_agents.lib.utils.scraping.pdf_to_markdown.PdfReader', return_value=mock_reader) as mock_pdf_reader:
        content = PdfToMarkdownConverter._read_pdf(file)
        
        mock_pdf_reader.assert_called_once_with(file)
        assert content == "Sample PDF content"


def test_convert_to_markdown():
    html_content = "<h1>Title</h1><p>This is a paragraph.</p><p>Another paragraph.</p>"
    markdown = PdfToMarkdownConverter._convert_to_markdown(html_content)
    
    expected_markdown = "# Title\n\nThis is a paragraph.\n\nAnother paragraph."
    assert markdown.strip() == expected_markdown.strip()

@patch('atomic_agents.lib.utils.scraping.pdf_to_markdown.PdfToMarkdownConverter._fetch_pdf_content')
@patch('atomic_agents.lib.utils.scraping.pdf_to_markdown.PdfToMarkdownConverter._read_pdf')
@patch('atomic_agents.lib.utils.scraping.pdf_to_markdown.PdfToMarkdownConverter._convert_to_markdown')
def test_convert_from_url(mock_convert, mock_read, mock_fetch):
    url = "https://example.com/sample.pdf"
    mock_fetch.return_value = BytesIO(SAMPLE_PDF_CONTENT)
    mock_read.return_value = "Sample PDF content"
    mock_convert.return_value = "# Sample PDF content"
    
    result = PdfToMarkdownConverter.convert(url=url)
    
    assert isinstance(result, WebDocument)
    assert result.content == "# Sample PDF content"
    assert isinstance(result.metadata, WebDocumentMetadata)
    assert result.metadata.url == url

@patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_PDF_CONTENT)
@patch('atomic_agents.lib.utils.scraping.pdf_to_markdown.PdfToMarkdownConverter._read_pdf')
@patch('atomic_agents.lib.utils.scraping.pdf_to_markdown.PdfToMarkdownConverter._convert_to_markdown')
def test_convert_from_file(mock_convert, mock_read, mock_file):
    file_path = "/path/to/sample.pdf"
    mock_read.return_value = "Sample PDF content"
    mock_convert.return_value = "# Sample PDF content"
    
    result = PdfToMarkdownConverter.convert(file_path=file_path)
    
    assert isinstance(result, WebDocument)
    assert result.content == "# Sample PDF content"
    assert isinstance(result.metadata, WebDocumentMetadata)
    assert result.metadata.url == file_path

def test_convert_no_input():
    with pytest.raises(ValueError, match="Either url or file_path must be provided"):
        PdfToMarkdownConverter.convert()