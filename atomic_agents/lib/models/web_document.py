from pydantic import BaseModel, Field

from atomic_agents.agents.base_agent import BaseIOSchema


class WebDocumentMetadata(BaseModel):
    url: str
    title: str = Field(default="")
    description: str = Field(default="")
    keywords: str = Field(default="")
    author: str = Field(default="")


class WebDocument(BaseIOSchema):
    content: str
    metadata: WebDocumentMetadata = Field(default_factory=lambda: WebDocumentMetadata(url=""))
