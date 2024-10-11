import os
from typing import List, Literal, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from pydantic import Field

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class SearxNGSearchToolInputSchema(BaseIOSchema):
    """
    Schema for input to a tool for searching for information, news, references, and other content using SearxNG.
    Returns a list of search results with a short description or content snippet and URLs for further exploration
    """

    queries: List[str] = Field(..., description="List of search queries.")
    category: Optional[Literal["general", "news", "social_media"]] = Field(
        "general", description="Category of the search queries."
    )


####################
# OUTPUT SCHEMA(S) #
####################
class SearxNGSearchResultItemSchema(BaseIOSchema):
    """This schema represents a single search result item"""

    url: str = Field(..., description="The URL of the search result")
    title: str = Field(..., description="The title of the search result")
    content: Optional[str] = Field(None, description="The content snippet of the search result")
    query: str = Field(..., description="The query used to obtain this search result")


class SearxNGSearchToolOutputSchema(BaseIOSchema):
    """This schema represents the output of the SearxNG search tool."""

    results: List[SearxNGSearchResultItemSchema] = Field(..., description="List of search result items")
    category: Optional[str] = Field(None, description="The category of the search results")


##############
# TOOL LOGIC #
##############
class SearxNGSearchToolConfig(BaseToolConfig):
    base_url: str = ""
    max_results: int = 10


class SearxNGSearchTool(BaseTool):
    """
    Tool for performing searches on SearxNG based on the provided queries and category.

    Attributes:
        input_schema (SearxNGSearchToolInputSchema): The schema for the input data.
        output_schema (SearxNGSearchToolOutputSchema): The schema for the output data.
        max_results (int): The maximum number of search results to return.
        base_url (str): The base URL for the SearxNG instance to use.
    """

    input_schema = SearxNGSearchToolInputSchema
    output_schema = SearxNGSearchToolOutputSchema

    def __init__(self, config: SearxNGSearchToolConfig = SearxNGSearchToolConfig()):
        """
        Initializes the SearxNGTool.

        Args:
            config (SearxNGSearchToolConfig):
                Configuration for the tool, including base URL, max results, and optional title and description overrides.
        """
        super().__init__(config)
        self.base_url = config.base_url
        self.max_results = config.max_results

    async def _fetch_search_results(self, session: aiohttp.ClientSession, query: str, category: Optional[str]) -> List[dict]:
        """
        Fetches search results for a single query asynchronously.

        Args:
            session (aiohttp.ClientSession): The aiohttp session to use for the request.
            query (str): The search query.
            category (Optional[str]): The category of the search query.

        Returns:
            List[dict]: A list of search result dictionaries.

        Raises:
            Exception: If the request to SearxNG fails.
        """
        query_params = {
            "q": query,
            "safesearch": "0",
            "format": "json",
            "language": "en",
            "engines": "bing,duckduckgo,google,startpage,yandex",
        }

        if category:
            query_params["categories"] = category

        async with session.get(f"{self.base_url}/search", params=query_params) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch search results for query '{query}': {response.status} {response.reason}")
            data = await response.json()
            results = data.get("results", [])

            # Add the query to each result
            for result in results:
                result["query"] = query

            return results

    async def run_async(
        self, params: SearxNGSearchToolInputSchema, max_results: Optional[int] = None
    ) -> SearxNGSearchToolOutputSchema:
        """
        Runs the SearxNGTool asynchronously with the given parameters.

        Args:
            params (SearxNGSearchToolInputSchema): The input parameters for the tool, adhering to the input schema.
            max_results (Optional[int]): The maximum number of search results to return.

        Returns:
            SearxNGSearchToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the base URL is not provided.
            Exception: If the request to SearxNG fails.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_search_results(session, query, params.category) for query in params.queries]
            results = await asyncio.gather(*tasks)

        all_results = [item for sublist in results for item in sublist]

        # Sort the combined results by score in descending order
        sorted_results = sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)

        # Remove duplicates while preserving order
        seen_urls = set()
        unique_results = []
        for result in sorted_results:
            if "content" not in result or "title" not in result or "url" not in result or "query" not in result:
                continue
            if result["url"] not in seen_urls:
                unique_results.append(result)
                if "metadata" in result:
                    result["title"] = f"{result['title']} - (Published {result['metadata']})"
                if "publishedDate" in result and result["publishedDate"]:
                    result["title"] = f"{result['title']} - (Published {result['publishedDate']})"
                seen_urls.add(result["url"])

        # Filter results to include only those with the correct category if it is set
        if params.category:
            filtered_results = [result for result in unique_results if result.get("category") == params.category]
        else:
            filtered_results = unique_results

        filtered_results = filtered_results[: max_results or self.max_results]

        return SearxNGSearchToolOutputSchema(
            results=[
                SearxNGSearchResultItemSchema(
                    url=result["url"], title=result["title"], content=result.get("content"), query=result["query"]
                )
                for result in filtered_results
            ],
            category=params.category,
        )

    def run(self, params: SearxNGSearchToolInputSchema, max_results: Optional[int] = None) -> SearxNGSearchToolOutputSchema:
        """
        Runs the SearxNGTool synchronously with the given parameters.

        This method creates an event loop in a separate thread to run the asynchronous operations.

        Args:
            params (SearxNGSearchToolInputSchema): The input parameters for the tool, adhering to the input schema.
            max_results (Optional[int]): The maximum number of search results to return.

        Returns:
            SearxNGSearchToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the base URL is not provided.
            Exception: If the request to SearxNG fails.
        """
        with ThreadPoolExecutor() as executor:
            return executor.submit(asyncio.run, self.run_async(params, max_results)).result()


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from rich.console import Console
    from dotenv import load_dotenv

    load_dotenv()
    rich_console = Console()

    search_tool_instance = SearxNGSearchTool(
        config=SearxNGSearchToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=5)
    )

    search_input = SearxNGSearchTool.input_schema(
        queries=["Python programming", "Machine learning", "Artificial intelligence"],
        category="news",
    )

    output = search_tool_instance.run(search_input)

    rich_console.print(output)
