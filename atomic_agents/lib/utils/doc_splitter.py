from typing import List
from atomic_agents.lib.models.web_document import Document, VectorDBDocumentMetadata

def split_document(document: Document, max_length=1000) -> List[Document]:
    if len(document.content) <= max_length:
        return [Document(content=document.content, metadata=VectorDBDocumentMetadata(**document.metadata.model_dump(), document_part=1, document_total_parts=1))]

    parts = []
    current_part = ''
    for line in document.content.splitlines(keepends=True):
        if len(current_part) + len(line) <= max_length:
            current_part += line
        else:
            parts.append(current_part)
            current_part = line

    if current_part:
        parts.append(current_part)

    total_parts = len(parts)
    return [
        Document(
            content=part.strip(),
            metadata=VectorDBDocumentMetadata(**document.metadata.model_dump(), document_part=i+1, document_total_parts=total_parts)
        )
        for i, part in enumerate(parts)
    ]