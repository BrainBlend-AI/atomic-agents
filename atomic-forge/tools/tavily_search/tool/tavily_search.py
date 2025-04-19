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
class TavilySearchToolInputSchema(BaseIOSchema):
    """
    Schema for input to a tool for searching for information, news, references, and other content using Tavily.
    Returns a list of search results with a short description or content snippet and URLs for further exploration
    """

    queries: List[str] = Field(..., description="List of search queries.")


####################
# OUTPUT SCHEMA(S) #
####################
class TavilySearchResultItemSchema(BaseIOSchema):
    """This schema represents a single search result item"""

    title: str = Field(..., description="The title of the search result")
    url: str = Field(..., description="The URL of the search result")
    content: str = Field(None, description="The content snippet of the search result")
    score: float = Field(..., description="The score of the search result")
    raw_content: Optional[str] = Field(None, description="The raw content of the search result")
    query: Optional[str] = Field(..., description="The query used to obtain this search result")
    answer: Optional[str] = Field(..., description="The answer to the query provided by Tavily")


class TavilySearchToolOutputSchema(BaseIOSchema):
    """This schema represents the output of the Tavily search tool."""

    results: List[TavilySearchResultItemSchema] = Field(..., description="List of search result items")


##############
# TOOL LOGIC #
##############
class TavilySearchToolConfig(BaseToolConfig):
    api_key: str = ""
    max_results: int = 5
    search_depth: Literal["basic", "advanced"] = "basic"
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None


class TavilySearchTool(BaseTool[TavilySearchToolInputSchema, TavilySearchToolOutputSchema]):
    """
    Tool for performing searches using the Tavily search API.

    Attributes:
        input_schema (TavilySearchToolInputSchema): The schema for the input data.
        output_schema (TavilySearchToolOutputSchema): The schema for the output data.
        max_results (int): The maximum number of search results to return.
        api_key (str): The API key for the Tavily API.
    """

    def __init__(self, config: TavilySearchToolConfig = TavilySearchToolConfig()):
        """
        Initializes the TavilySearchTool.

        Args:
            config (TavilySearchToolConfig):
                Configuration for the tool, including API key, max results, and optional title and description overrides.
        """
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("TAVILY_API_KEY", "")
        self.max_results = config.max_results
        self.search_depth = config.search_depth
        self.include_domains = config.include_domains
        self.exclude_domains = config.exclude_domains

    async def _fetch_search_results(self, session: aiohttp.ClientSession, query: str) -> List[dict]:
        headers = {
            "accept": "/",
            "content-type": "application/json",
            "origin": "https://app.tavily.com/",
            "referer": "https://app.tavily.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        json_data = {
            "query": query,
            "api_key": self.api_key,
            "search_depth": self.search_depth,
            "include_domains": self.include_domains,
            "exclude_domains": self.exclude_domains,
            "max_results": self.max_results,
        }

        async with session.post("https://api.tavily.com/search", headers=headers, json=json_data) as response:
            if response.status != 200:
                error_message = await response.text()
                raise Exception(
                    f"Failed to fetch search results for query '{query}': {response.status} {response.reason}. Details: {error_message}"
                )
            data = await response.json()
            results = data.get("results", [])

            # Add query information to each result
            for result in results:
                result["query"] = query

            return results

    async def run_async(
        self, params: TavilySearchToolInputSchema, max_results: Optional[int] = None
    ) -> TavilySearchToolOutputSchema:
        async with aiohttp.ClientSession() as session:
            # Fetch results for all queries
            tasks = [self._fetch_search_results(session, query) for query in params.queries]
            raw_results = await asyncio.gather(*tasks)

        # Process results for each query
        processed_results = []
        for query_results in raw_results:
            query_processed = []
            for result in query_results:
                if all(key in result for key in ["title", "url", "content", "score"]):
                    query_processed.append(
                        TavilySearchResultItemSchema(
                            title=result["title"],
                            url=result["url"],
                            content=result.get("content", ""),
                            score=result.get("score", 0),
                            raw_content=result.get("raw_content"),
                            query=result.get("query"),
                        )
                    )
                else:
                    print(f"Skipping result due to missing keys: {result}")

            # Limit results per query
            query_processed = query_processed[: max_results or self.max_results]
            processed_results.extend(query_processed)

        return TavilySearchToolOutputSchema(results=processed_results)

    def run(self, params: TavilySearchToolInputSchema, max_results: Optional[int] = None) -> TavilySearchToolOutputSchema:
        """
        Runs the TavilyTool synchronously with the given parameters.

        This method creates an event loop in a separate thread to run the asynchronous operations.

        Args:
            params (TavilySearchToolInputSchema): The input parameters for the tool, adhering to the input schema.
            max_results (Optional[int]): The maximum number of search results to return.

        Returns:
            TavilySearchToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the base URL is not provided.
            Exception: If the request to Tavily fails.
        """
        with ThreadPoolExecutor() as executor:
            return executor.submit(
                asyncio.run,
                self.run_async(
                    params,
                    max_results,
                ),
            ).result()


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from rich.console import Console

    rich_console = Console()

    search_tool_instance = TavilySearchTool(config=TavilySearchToolConfig(api_key=os.getenv("TAVILY_API_KEY"), max_results=2))

    search_input = TavilySearchTool.input_schema(queries=["Python programming", "Machine learning", "Artificial intelligence"])

    output = search_tool_instance.run(search_input)

    rich_console.print(output)
