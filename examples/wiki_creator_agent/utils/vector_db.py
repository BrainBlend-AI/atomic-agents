import openai
import faiss
import numpy as np
from typing import List, Dict
from tqdm import tqdm


class InMemFaiss:
    def __init__(self, openai_api_key):
        openai.api_key = openai_api_key
        self.index = faiss.IndexFlatL2(1536)
        self.texts = []
        self.metadata = []

    def split_text(self, text, chunk_size=1750, overlap=250):
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i : i + chunk_size].strip()
            chunks.append(chunk)
        return chunks

    def generate_embeddings(self, texts):
        embeddings = []
        batch_size = 1000  # Adjust this based on your needs and API limits

        for i in tqdm(range(0, len(texts), batch_size)):
            batch = texts[i : i + batch_size]
            try:
                response = openai.embeddings.create(input=batch, model="text-embedding-3-small")
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size}: {e}")
                # Handle the error appropriately, e.g., retry or skip

        return np.array(embeddings).astype("float32")

    async def ingest_documents(self, documents: Dict[str, str]):
        all_chunks = []
        all_metadata = []

        for url, content in documents.items():
            if len(content) == 0:
                continue
            chunks = self.split_text(content)
            all_chunks.extend(chunks)
            all_metadata.extend([{"url": url}] * len(chunks))

        embeddings = self.generate_embeddings(all_chunks)
        self.index.add(embeddings)
        self.texts.extend(all_chunks)
        self.metadata.extend(all_metadata)

    def retrieve_chunks(self, query, top_k=5):
        query_embedding = self.generate_embeddings([query])
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.texts[idx] for idx in indices[0]]
