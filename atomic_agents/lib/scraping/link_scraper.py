import asyncio
import logging
from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
from typing import Set, List

import aiohttp
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

class InternalLinkScraper:
    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed_url = urlparse(url)
        scheme = "https" if parsed_url.scheme == "http" else parsed_url.scheme
        path = parsed_url.path.rstrip("/")
        return urlunparse(parsed_url._replace(scheme=scheme, path=path))

    @staticmethod
    async def _get_internal_links(session: aiohttp.ClientSession, url: str, visited: Set[str], queue: deque, continue_on_error: bool = True):
        try:
            logging.info(f"Processing {url}")
            async with session.get(url) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    if href and not href.startswith("#"):
                        href = InternalLinkScraper._normalize_url(urljoin(url, href))
                        parsed_href = urlparse(href)
                        parsed_base = urlparse(url)
                        
                        if parsed_href.netloc == parsed_base.netloc and href not in visited:
                            queue.append(href)
                            
        except Exception as e:
            logging.error(f"Failed to process {url}: {str(e)}")
            if not continue_on_error:
                raise e

    @staticmethod
    async def scrape_internal_links(start_url: str, continue_on_error: bool = True, max_workers: int = 10) -> List[str]:
        visited = set()
        queue = deque([InternalLinkScraper._normalize_url(start_url)])
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            while queue or tasks:
                while queue and len(tasks) < max_workers:
                    url = queue.popleft()
                    if url not in visited:
                        task = asyncio.create_task(InternalLinkScraper._get_internal_links(session, url, visited, queue, continue_on_error))
                        tasks.append(task)
                        visited.add(url)
                
                if tasks:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
                    for task in done:
                        try:
                            await task
                        except Exception as e:
                            logging.error(f"Error processing task: {str(e)}")

        return list(visited)

if __name__ == "__main__":
    from time import time
    start_time = time()
    url = "https://brainblendai.com"
    internal_links = asyncio.run(InternalLinkScraper.scrape_internal_links(url))
    scrape_time = time() - start_time
    print('SCRAPING STATS')
    print('============')
    print(f"Scraped {len(internal_links)} internal links from {url} in {scrape_time:.2f} seconds")
    print(internal_links)