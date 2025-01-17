# Tavily Search Tool

## Overview
The Tavily Search Tool is a powerful utility within the Atomic Agents ecosystem that allows you to perform searches using Tavily, a search engine built for AI Agents. This tool enables you to fetch search results from Tavily.

## Prerequisites and Dependencies
- Python 3.9 or later
- atomic-agents (See [here](/README.md) for installation instructions)
- pydantic
- requests

## Installation
You can install the tool using any of the following options:

1. Using the CLI tool that comes with Atomic Agents. Simply run `atomic` and select the tool from the list of available tools. After doing so you will be asked for a target directory to download the tool into.
2. Good old fashioned copy/paste: Just like any other tool inside the Atomic Forge, you can copy the code from this repo directly into your own project, provided you already have atomic-agents installed according to the instructions in the main [README](/README.md).

## Configuration

### Parameters

- `api_url` (str): The api key of the Tavily user.
- `max_results` (int, optional): The maximum number of search results to return. Defaults to `10`.

### Example

```python
config = TavilySearchToolConfig(
    api_key="my-api-key",
    max_results=5
)
```

## Input & Output Structure

### Input Schema
- `queries` (List[str]): List of search queries.

### Output Schema
- `results` (List[TavilySearchResultItemSchema]): List of search result items.

Each `TavilySearchResultItemSchema` contains:
- `title` (str): The title of the search result.
- `url` (str): The URL of the search result.
- `content` (Optional[str]): The content snippet of the search result.
- `score` (float): The score of the search result.
- `raw_content` (Optional[str]): The raw content of the search result.
- `query` (str): The query used to obtain this search result.
- `answer` (Optional[str]): The answer to the query provided by Tavily.

## Usage

Here's an example of how to use the Tavily Search Tool:


```python
import os
from tool.tavily_search import TavilyTool, TavilySearchToolConfig

# Initialize the tool with your Tavily instance URL
config = TavilySearchToolConfig(api_key=os.getenv("TAVILY_API_KEY"), max_results=5)
search_tool = TavilyTool(config=config)

# Define input data
input_data = TavilyTool.input_schema(
    queries=["Python programming", "Machine learning"],
)

# Perform the search
result = search_tool.run(input_data)
print(result)
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes with clear messages.
4. Open a pull request detailing your changes.

Please ensure you follow the project's coding standards and include tests for any new features or bug fixes.

## License

This project is licensed under the same license as the main Atomic Agents project. See the [LICENSE](/LICENSE) file in the repository root for more details.
