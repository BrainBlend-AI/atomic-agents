from atomic_agents.lib.models.web_document import Document, VectorDBDocumentMetadata

def document_to_string(document: Document) -> str:
    output = []
    
    # Determine the title or URL for the header
    header_title = document.metadata.title if document.metadata.title else document.metadata.url
    part_info = ""
    
    if isinstance(document.metadata, VectorDBDocumentMetadata):
        part_info = f" (Part {document.metadata.document_part} of {document.metadata.document_total_parts})"
    
    # Add the header with title and part information
    output.append(f"--- [{header_title}]{part_info} ---")
    
    # Add metadata fields except 'title' if it's already in the header
    for field_name, field_value in document.metadata.model_dump().items():
        if field_value and field_name != "title":
            output.append(f"{field_name.replace('_', ' ').title()}: {field_value}")
    
    # Add the content of the document
    output.append("Document Content:")
    output.append(document.content)
    
    # Join all parts with newlines and return
    return "\n".join(output) + "\n"

if __name__ == '__main__':
    # Example usage
    metadata = VectorDBDocumentMetadata(
        url="http://example.com",
        title="Example Document",
        description="An example document stored in VectorDB.",
        keywords="example, sample, document",
        author="John Doe",
        document_part=1,
        document_total_parts=3
    )

    doc = Document(
        content="This is the content of the document.",
        metadata=metadata
    )

    document_str = document_to_string(doc)
    print(document_str)
