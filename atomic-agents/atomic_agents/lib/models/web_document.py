from pydantic import Field

from atomic_agents.agents.base_agent import BaseIOSchema


class WebDocumentMetadata(BaseIOSchema):
    """Schema that describes the metadata of a web document."""

    url: str
    title: str = Field(default="")
    description: str = Field(default="")
    keywords: str = Field(default="")
    author: str = Field(default="")


class WebDocument(BaseIOSchema):
    """Schema that represents the content and metadata of a web document."""

    content: str
    metadata: WebDocumentMetadata = Field(default_factory=lambda: WebDocumentMetadata(url=""))
