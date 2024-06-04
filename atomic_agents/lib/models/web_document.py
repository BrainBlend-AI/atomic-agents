from pydantic import BaseModel, Field

class WebDocumentMetadata(BaseModel):
    url: str
    title: str = Field(default='')
    description: str = Field(default='')
    keywords: str = Field(default='')
    author: str = Field(default='')
    
class WebDocument(BaseModel):
    content: str
    metadata: WebDocumentMetadata = Field(default_factory=WebDocumentMetadata)

