import os
import requests
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from rich.console import Console
import openai
import instructor

from atomic_agents.lib.tools.base import BaseTool, BaseToolConfig
from atomic_agents.agents.base_chat_agent import BaseAgentIO

################
# INPUT SCHEMA #
################
class SerperSearchToolSchema(BaseAgentIO):
    queries: List[str] = Field(..., description="List of search queries.")

    class Config:
        title = "SerperSearchTool"
        description = "Tool for searching for information, news, references, and other content using the Serper API. Returns a list of search results with a short description or content snippet and URLs for further exploration."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class SerperSearchResultSchema(BaseAgentIO):
    url: str
    title: str
    content: Optional[str] = None
    position: Optional[int] = None

class SerperSearchToolOutputSchema(BaseAgentIO):
    results: List[SerperSearchResultSchema]

##############
# TOOL LOGIC #
##############
class SerperSearchToolConfig(BaseToolConfig):
    api_key: str = ""
    max_results: int = 10

class SerperSearchTool(BaseTool):
    """
    Tool for performing searches using the Serper API based on the provided queries.

    Attributes:
        input_schema (SerperSearchToolSchema): The schema for the input data.
        output_schema (SerperSearchToolOutputSchema): The schema for the output data.
        api_key (str): The API key for the Serper API.
        max_results (int): The maximum number of search results to return.
    """
    input_schema = SerperSearchToolSchema
    output_schema = SerperSearchToolOutputSchema

    def __init__(self, config: SerperSearchToolConfig = SerperSearchToolConfig()):
        """
        Initializes the SerperSearchTool.

        Args:
            config (SerperSearchToolConfig): Configuration for the tool, including API key, max results, and optional title and description overrides.
        """
        super().__init__(config)
        self.api_key = config.api_key
        self.max_results = config.max_results

    def run(self, params: SerperSearchToolSchema, max_results: Optional[int] = None) -> SerperSearchToolOutputSchema:
        """
        Runs the SerperSearchTool with the given parameters.

        Args:
            params (SerperSearchToolSchema): The input parameters for the tool, adhering to the input schema.
            max_results (Optional[int]): The maximum number of search results to return.

        Returns:
            SerperSearchToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the API key is not provided.
            Exception: If the request to Serper API fails.
        """
        all_results = []

        for query in params.queries:
            # Prepare the query payload
            payload = json.dumps({"q": query})

            # Make the POST request
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)

            # Check if the request was successful
            if response.status_code != 200:
                raise Exception(f"Failed to fetch search results for query '{query}': {response.status_code} {response.reason}")

            results = response.json().get('organic', [])
            all_results.extend(results)

        # Sort the combined results by position in ascending order
        sorted_results = sorted(all_results, key=lambda x: x.get('position', float('inf')))

        # Remove duplicates while preserving order
        seen_urls = set()
        unique_results = []
        for result in sorted_results:
            if 'snippet' not in result or 'title' not in result or 'link' not in result:
                continue
            if result['link'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['link'])

        filtered_results = unique_results[:max_results or self.max_results]

        # Convert to output schema format
        output_results = [
            SerperSearchResultSchema(
                url=result['link'],
                title=result['title'],
                content=result.get('snippet'),
                position=result.get('position')
            )
            for result in filtered_results
        ]

        return SerperSearchToolOutputSchema(results=output_results)

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    search_tool_instance = SerperSearchTool(config=SerperSearchToolConfig(api_key=os.getenv("SERPER_API_KEY"), max_results=5))
    
    search_input = SerperSearchTool.input_schema(queries=["Python programming", "Machine learning", "Quantum computing"])

    output = search_tool_instance.run(search_input)
    
    rich_console.print(output)