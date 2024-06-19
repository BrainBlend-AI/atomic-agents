import os
import openai
import faiss
import numpy as np
import html2text
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import markdownify

class InMemFaiss:
    def __init__(self, openai_api_key):
        openai.api_key = openai_api_key
        self.index = faiss.IndexFlatL2(1536)
        self.texts = []
        self.metadata = []

    async def download_content(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            html_content = await page.content()
            await browser.close()
        
        # Clean HTML content
        cleaned_html = self.clean_html(html_content)
        
        # Convert cleaned HTML to Markdown
        markdown_content = markdownify.markdownify(cleaned_html, heading_style="ATX")
        return markdown_content

    def clean_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Example cleaning: remove script and style tags
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # Additional cleaning can be done here
        cleaned_html = str(soup)
        return cleaned_html

    def split_text(self, text, chunk_size=1000, overlap=250):
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size].strip()
            chunks.append(chunk)
        return chunks

    async def generate_embeddings(self, texts):
        embeddings = []
        for text in texts:
            response = await openai.Embedding.create(input=text, model="text-embedding-3-small")
            embeddings.append(response['data'][0]['embedding'])
        return np.array(embeddings).astype('float32')

    async def ingest_urls(self, urls):
        tasks = [self.process_url(url) for url in urls]
        await asyncio.gather(*tasks)

    async def process_url(self, url):
        try:
            url = str(url)
            content = await self.download_content(url)
            chunks = self.split_text(content)
            embeddings = await self.generate_embeddings(chunks)
            self.index.add(embeddings)
            self.texts.extend(chunks)
            self.metadata.extend([{"url": url}] * len(chunks))
        except Exception as e:
            print(f"Failed to ingest URL {url}: {e}")

    async def retrieve_chunks(self, query, top_k=5):
        query_embedding = await self.generate_embeddings([query])
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.texts[idx] for idx in indices[0]]