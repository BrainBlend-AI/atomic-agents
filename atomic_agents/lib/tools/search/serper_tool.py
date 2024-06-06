import os
import requests
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from rich.console import Console
import openai
import instructor

from atomic_agents.lib.tools.base import BaseTool

################
# INPUT SCHEMA #
################
class SerperSearchToolSchema(BaseModel):
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
class SerperSearchResultSchema(BaseModel):
    url: str
    title: str
    content: Optional[str] = None
    position: Optional[int] = None

class SerperSearchToolOutputSchema(BaseModel):
    results: List[SerperSearchResultSchema]

##############
# TOOL LOGIC #
##############
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

    def __init__(self, api_key: str, max_results: int = 10, **kwargs):
        """
        Initializes the SerperSearchTool.

        Args:
            api_key (str): The API key for the Serper API.
            max_results (int): The maximum number of search results to return.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        self.max_results = max_results

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
        response_model=SerperSearchTool.input_schema,
        messages=[{"role": "user", "content": "I want to compare transformers architecture with mamba."}],
    )

    rich_console.print(f"Search queries: {result.queries}")

    # Print the result
    output = SerperSearchTool(api_key=os.getenv('SERPER_API_KEY'), max_results=15).run(result)
    for i, result in enumerate(output.results):
        rich_console.print(f"{i}. Title: {result.title}, URL: {result.url}")
