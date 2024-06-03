import os
from typing import List
import chromadb
import openai
from atomic_agents.lib.utils.doc_splitter import split_document
from atomic_agents.lib.utils.document_to_string import document_to_string
from atomic_agents.lib.models.web_document import Document, VectorDBDocumentMetadata

class ChromaDBDocumentManager:
    def __init__(self, db_path, collection_name):
        self.db = chromadb.PersistentClient(path=db_path)
        self.collection_name = collection_name

    def process_documents(self, documents: List[Document], max_length=1000):
        collection = self.db.get_or_create_collection(self.collection_name)
        for document in documents:
            document_parts = split_document(document, max_length)
            for part in document_parts:
                embedding = self._create_embedding(part.content)
                collection.upsert(
                    ids=[f"{document.metadata.url}_{part.metadata.document_part}_{part.metadata.document_total_parts}"],
                    embeddings=embedding,
                    metadatas=[part.metadata.model_dump()],
                    documents=[part.content]
                )

    def create_collection(self):
        self.db.create_collection(self.collection_name)
        
    def delete_collection(self):
        self.db.delete_collection(self.collection_name)

    def query_documents(self, queries: List[str], n_results: int = 3) -> List[Document]:
        collection = self.db.get_collection(self.collection_name)
        if not collection:
            raise ValueError(f"Collection '{self.collection_name}' not found.")

        embeddings = self._create_embedding(queries)
        
        results = collection.query(
            query_embeddings=embeddings,
            n_results=n_results,
        )
        
        flattened_result_documents = [doc for sublist in results['documents'] for doc in sublist]
        flattened_result_metadatas = [metadata for sublist in results['metadatas'] for metadata in sublist]
        flattened_result_distances = [distance for sublist in results['distances'] for distance in sublist]
        
        # Sort all lists by distance
        results = sorted(zip(flattened_result_documents, flattened_result_metadatas, flattened_result_distances), key=lambda x: x[2])

        # Deduplicate results
        deduplicated_results = []
        seen_content = set()
        for content, metadata, distance in results:
            if content not in seen_content:
                deduplicated_results.append((content, metadata))
                seen_content.add(content)

        results = {
            'documents': [content for content, metadata in deduplicated_results],
            'metadatas': [metadata for content, metadata in deduplicated_results]
        }

        # Construct Document objects from the results
        documents = []
        for content, metadata in list(zip(results['documents'], results['metadatas']))[:n_results]:
            document = Document(content=content, metadata=VectorDBDocumentMetadata(**metadata))
            documents.append(document)

        return documents

    def _create_embedding(self, content):
        embedding_client = os.getenv('EMBEDDING_CLIENT')
        
        if embedding_client == 'openai':
            openai_api_key = os.getenv('OPENAI_API_KEY')
            embedding_client = openai.OpenAI(api_key=openai_api_key)
            response = embedding_client.embeddings.create(
                input=content,
                model="text-embedding-3-small"
            )
        elif embedding_client == 'local':
            local_host = os.getenv('LOCAL_CLIENT_HOST')
            embedding_client = openai.OpenAI(base_url=local_host, api_key='N/A')
            response = embedding_client.embeddings.create(
                input=content,
                model="N/A"
            )
        else:
            raise ValueError("Unsupported embedding client. Choose 'openai' or 'local'.")

        return [response.data[i].embedding for i in range(len(response.data))]

    @staticmethod
    def document_to_string(doc: Document) -> str:
        return document_to_string(doc)
    
if __name__ == '__main__':
    db = ChromaDBDocumentManager(db_path='chromadb_persist', collection_name='brainblendai.com')
    documents = db.query_documents(["What is the best AI assistant?", "What does describeit do?" ,"What is the best AI assistant?"], n_results=3)
    for doc in documents:
        print(doc.metadata.url)