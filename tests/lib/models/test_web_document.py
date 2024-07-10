import pytest
from pydantic import ValidationError
from atomic_agents.lib.models.web_document import WebDocumentMetadata, WebDocument
from atomic_agents.agents.base_agent import BaseAgentIO

def test_web_document_metadata_creation():
    metadata = WebDocumentMetadata(url="https://example.com")
    assert metadata.url == "https://example.com"
    assert metadata.title == ""
    assert metadata.description == ""
    assert metadata.keywords == ""
    assert metadata.author == ""

def test_web_document_metadata_full():
    metadata = WebDocumentMetadata(
        url="https://example.com",
        title="Example Title",
        description="Example Description",
        keywords="example, test, keywords",
        author="John Doe"
    )
    assert metadata.url == "https://example.com"
    assert metadata.title == "Example Title"
    assert metadata.description == "Example Description"
    assert metadata.keywords == "example, test, keywords"
    assert metadata.author == "John Doe"

def test_web_document_metadata_url_required():
    with pytest.raises(ValidationError):
        WebDocumentMetadata()

def test_web_document_creation():
    doc = WebDocument(content="This is the content")
    assert doc.content == "This is the content"
    assert isinstance(doc.metadata, WebDocumentMetadata)
    assert doc.metadata.url == ""

def test_web_document_with_metadata():
    metadata = WebDocumentMetadata(url="https://example.com", title="Example")
    doc = WebDocument(content="This is the content", metadata=metadata)
    assert doc.content == "This is the content"
    assert doc.metadata.url == "https://example.com"
    assert doc.metadata.title == "Example"

def test_web_document_content_required():
    with pytest.raises(ValidationError):
        WebDocument()

def test_web_document_inheritance():
    doc = WebDocument(content="This is the content")
    assert isinstance(doc, WebDocument)
    assert isinstance(doc, BaseAgentIO)

def test_web_document_metadata_serialization():
    metadata = WebDocumentMetadata(url="https://example.com", title="Example")
    assert metadata.model_dump() == {
        "url": "https://example.com",
        "title": "Example",
        "description": "",
        "keywords": "",
        "author": ""
    }

def test_web_document_serialization():
    metadata = WebDocumentMetadata(url="https://example.com", title="Example")
    doc = WebDocument(content="This is the content", metadata=metadata)
    assert doc.model_dump() == {
        "content": "This is the content",
        "metadata": {
            "url": "https://example.com",
            "title": "Example",
            "description": "",
            "keywords": "",
            "author": ""
        }
    }

def test_web_document_default_metadata():
    doc = WebDocument(content="This is the content")
    assert doc.metadata.url == ""
    assert doc.metadata.title == ""
    assert doc.metadata.description == ""
    assert doc.metadata.keywords == ""
    assert doc.metadata.author == ""