from pydantic import BaseModel, Field

class WebDocumentMetadata(BaseModel):
    url: str
    title: str = Field(default='')
    description: str = Field(default='')
    keywords: str = Field(default='')
    author: str = Field(default='')

class VectorDBDocumentMetadata(WebDocumentMetadata):
    document_part: int = Field(default=1)
    document_total_parts: int = Field(default=1)
    
class Document(BaseModel):
    content: str
    metadata: WebDocumentMetadata | VectorDBDocumentMetadata = Field(default_factory=WebDocumentMetadata)

