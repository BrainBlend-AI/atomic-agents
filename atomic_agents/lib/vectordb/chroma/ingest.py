import asyncio
import os
from typing import List
from pydantic import HttpUrl
from atomic_agents.lib.diff_file_contents import diff_file_contents
from atomic_agents.lib.scraping.link_scraper import InternalLinkScraper
from atomic_agents.lib.scraping.url_to_markdown import UrlToMarkdownConverter
from atomic_agents.lib.utils.doc_splitter import split_document
from atomic_agents.lib.utils.document_to_string import document_to_string
from atomic_agents.lib.models.web_document import Document, VectorDBDocumentMetadata
from atomic_agents.lib.vectordb.chroma.manager import ChromaDBDocumentManager

def scrape_and_clean_urls(urls: List[HttpUrl], db_path='chromadb_tmp', collection_name = None, do_diff=True) -> List[Document]:
    try:
        web_documents = []
        for url in urls:
            try:
                document = UrlToMarkdownConverter.convert(str(url))
                web_documents.append(document)
                print(f"Scraped URL: {url}")
            except Exception as e:
                print(f"Error converting URL to markdown: {e}")
                pass
            
        if do_diff:
            cleaned_contents = diff_file_contents([doc.content.split('\n') for doc in web_documents])
        else:
            cleaned_contents = [doc.content.split('\n') for doc in web_documents]
        cleaned_documents = []
        for content, metadata in zip(cleaned_contents, [doc.metadata for doc in web_documents]):
            cleaned_documents.append(Document(content='\n'.join(content).strip(), metadata=metadata))

        # Ensure the URL is parsed correctly to get the host
        db = ChromaDBDocumentManager(db_path, collection_name=collection_name or urls[0].host)
        db.process_documents(cleaned_documents)

        return cleaned_documents
    except Exception as e:
        print(f"Error scraping and cleaning URLs: {e}")
        return []

if __name__ == "__main__":
    # Example usage
    url = "https://brainblendai.com"
    internal_links = asyncio.run(InternalLinkScraper.scrape_internal_links(url))
    documents = scrape_and_clean_urls(internal_links, collection_name='brainblendai')
    for doc in documents:
        print(document_to_string(doc))