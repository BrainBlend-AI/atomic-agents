import aiohttp
import asyncio
from bs4 import BeautifulSoup
from readability import Document
import html2text
from typing import List, Dict
import trafilatura


class ContentScraper:
    @staticmethod
    async def scrape_urls(urls: List[str]) -> Dict[str, str]:
        async def fetch_url(session: aiohttp.ClientSession, url: str) -> tuple:
            try:
                async with session.get(url, timeout=30) as response:  # Added timeout
                    html_content = await response.text()

                    # Try trafilatura first
                    extracted_content = trafilatura.extract(html_content)

                    if not extracted_content:
                        # If trafilatura fails, fall back to readability
                        doc = Document(html_content)
                        extracted_content = doc.summary()

                    # Clean up the extracted content
                    soup = BeautifulSoup(extracted_content, "html.parser")
                    for script in soup(["script", "style"]):
                        script.decompose()
                    cleaned_content = soup.get_text()

                    # Convert to markdown
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    markdown_content = h.handle(cleaned_content)

                    return url, markdown_content.strip()
            except Exception as e:
                return url, f"Error scraping {url}: {str(e)}"

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)

        return dict(results)
