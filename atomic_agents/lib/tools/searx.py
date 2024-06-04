import os
import requests
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from rich.console import Console
import openai
import instructor

from atomic_agents.lib.tools.base import BaseTool

################
# INPUT SCHEMA #
################
class SearxNGSearchToolSchema(BaseModel):
    queries: List[str] = Field(..., description="List of search queries.")
    category: Optional[Literal["general", "news", "social_media"]] = Field(None, description="Category of the search queries.")

    class Config:
        title = "SearxNGSearchTool"
        description = "Tool for searching for information, news, references, and other content on the SearxNG. Returns a list of search results with a short description or content snippet and URLs for further exploration."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class SearxNGSearchResultSchema(BaseModel):
    url: str
    title: str
    content: Optional[str] = None
    category: Optional[str] = None

class SearxNGSearchToolOutputSchema(BaseModel):
    results: List[SearxNGSearchResultSchema]

##############
# TOOL LOGIC #
##############
class SearxNGSearchTool(BaseTool):
    input_schema = SearxNGSearchToolSchema
    output_schema = SearxNGSearchToolOutputSchema
    
    def __init__(self, tool_description_override: Optional[str] = None, max_results: int = 10):
        super().__init__(tool_description_override)
        self.max_results = max_results

    def run(self, params: SearxNGSearchToolSchema, max_results: Optional[int] = None) -> SearxNGSearchToolOutputSchema:
        SEARXNG_BASE_URL = os.getenv('SEARXNG_BASE_URL')
        if not SEARXNG_BASE_URL:
            raise ValueError("SEARXNG_BASE_URL environment variable not set")

        all_results = []

        for query in params.queries:
            # Prepare the query parameters
            query_params = {
                'q': query,
                'safesearch': '0',
                'format': 'json',
                'language': 'en',
                'engines': 'bing,duckduckgo,google,startpage,yandex',
            }
            
            # Add category to query parameters if it is set
            if params.category:
                query_params['categories'] = params.category

            # Make the GET request
            response = requests.get(f"{SEARXNG_BASE_URL}/search", params=query_params)

            # Check if the request was successful
            if response.status_code != 200:
                raise Exception(f"Failed to fetch search results for query '{query}': {response.status_code} {response.reason}")

            results = response.json().get('results', [])
            all_results.extend(results)

        # Sort the combined results by score in descending order
        sorted_results = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)

        # Remove duplicates while preserving order
        seen_urls = set()
        unique_results = []
        for result in sorted_results:
            if 'content' not in result or 'title' not in result or 'url' not in result:
                continue
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        # Filter results to include only those with the correct category if it is set
        if params.category:
            filtered_results = [result for result in unique_results if result.get('category') == params.category]
        else:
            filtered_results = unique_results

        filtered_results = filtered_results[:max_results or self.max_results]

        return SearxNGSearchToolOutputSchema(results=filtered_results)
    
    
#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    
    # Initialize the client outside
    client = instructor.from_openai(
        openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    )
    
    # Extract structured data from natural language
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=SearxNGSearchTool.input_schema,
        messages=[{"role": "user", "content": "Search for the latest PC gaming news of May 2024 using 3 different queries."}],
    )
    
    rich_console.print(f"Search queries: {result.queries}")
    
    # Print the result
    output = SearxNGSearchTool(max_results=15).run(result)
    for i, result in enumerate(output.results):
        rich_console.print(f"{i}. Title: {result.title}, URL: {result.url}")