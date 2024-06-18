from pydantic import BaseModel, Field

from atomic_agents.agents.base_chat_agent import BaseAgentIO

class WebDocumentMetadata(BaseModel):
    url: str
    title: str = Field(default='')
    description: str = Field(default='')
    keywords: str = Field(default='')
    author: str = Field(default='')
    
class WebDocument(BaseAgentIO):
    content: str
    metadata: WebDocumentMetadata = Field(default_factory=WebDocumentMetadata)

