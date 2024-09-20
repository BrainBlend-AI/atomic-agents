import json
import os
from typing import List, Optional

import requests
from pydantic import Field
from rich.console import Console

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.tools.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class SerperToolInputSchema(BaseIOSchema):
    """
    Tool for searching for information, news, references, and other content using the Serper API.
    Returns a list of search results with a short description or content snippet and URLs for further exploration.
    """

    queries: List[str] = Field(..., description="List of search queries.")


####################
# OUTPUT SCHEMA(S) #
####################
class SerperResultSchema(BaseIOSchema):
    url: str
    title: str
    content: Optional[str] = None
    position: Optional[int] = None


class SerperToolOutputSchema(BaseIOSchema):
    results: List[SerperResultSchema]


##############
# TOOL LOGIC #
##############
class SerperToolConfig(BaseToolConfig):
    api_key: str = ""
    max_results: int = 10


class SerperTool(BaseTool):
    """
    Tool for performing searches using the Serper API based on the provided queries.

    Attributes:
        input_schema (SerperToolInputSchema): The schema for the input data.
        output_schema (SerperToolOutputSchema): The schema for the output data.
        api_key (str): The API key for the Serper API.
        max_results (int): The maximum number of search results to return.
    """

    input_schema = SerperToolInputSchema
    output_schema = SerperToolOutputSchema

    def __init__(self, config: SerperToolConfig = SerperToolConfig()):
        """
        Initializes the SerperTool.

        Args:
            config (SerperToolConfig):
                Configuration for the tool, including API key, max results, and optional title and description overrides.
        """
        super().__init__(config)
        self.api_key = config.api_key
        self.max_results = config.max_results

    def run(self, params: SerperToolInputSchema, max_results: Optional[int] = None) -> SerperToolOutputSchema:
        """
        Runs the SerperTool with the given parameters.

        Args:
            params (SerperToolInputSchema): The input parameters for the tool, adhering to the input schema.
            max_results (Optional[int]): The maximum number of search results to return.

        Returns:
            SerperToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the API key is not provided.
            Exception: If the request to Serper API fails.
        """
        all_results = []

        for query in params.queries:
            # Prepare the query payload
            payload = json.dumps({"q": query})

            # Make the POST request
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
            response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)

            # Check if the request was successful
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch search results for query '{query}': {response.status_code} {response.reason}"
                )

            results = response.json().get("organic", [])
            all_results.extend(results)

        # Sort the combined results by position in ascending order
        sorted_results = sorted(all_results, key=lambda x: x.get("position", float("inf")))

        # Remove duplicates while preserving order
        seen_urls = set()
        unique_results = []
        for result in sorted_results:
            if "snippet" not in result or "title" not in result or "link" not in result:
                continue
            if result["link"] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result["link"])

        filtered_results = unique_results[: max_results or self.max_results]

        # Convert to output schema format
        output_results = [
            SerperResultSchema(
                url=result["link"],
                title=result["title"],
                content=result.get("snippet"),
                position=result.get("position"),
            )
            for result in filtered_results
        ]

        return SerperToolOutputSchema(results=output_results)


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    search_tool_instance = SerperTool(config=SerperToolConfig(api_key=os.getenv("SERPER_API_KEY"), max_results=5))

    search_input = SerperTool.input_schema(queries=["Python programming", "Machine learning", "Quantum computing"])

    output = search_tool_instance.run(search_input)

    rich_console.print(output)
