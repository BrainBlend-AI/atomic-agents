# SearxNG Search Tool

## Overview
The SearxNG Search Tool is a powerful utility within the Atomic Agents ecosystem that allows you to perform searches using SearxNG, a privacy-respecting metasearch engine. This tool enables you to fetch search results from multiple sources while maintaining user privacy.

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

- `base_url` (str): The base URL of the SearxNG instance. This should include the protocol (e.g., `https://`) and the domain or IP address where SearxNG is hosted.
- `max_results` (int, optional): The maximum number of search results to return. Defaults to `10`.

### Example

```python
config = SearxNGSearchToolConfig(
    base_url="https://searxng.example.com",
    max_results=5
)
```

## Input & Output Structure

### Input Schema
- `queries` (List[str]): List of search queries.
- `category` (Optional[Literal["general", "news", "social_media"]]): Category of the search queries. Defaults to "general".

### Output Schema
- `results` (List[SearxNGSearchResultItemSchema]): List of search result items.
- `category` (Optional[str]): The category of the search results.

Each `SearxNGSearchResultItemSchema` contains:
- `url` (str): The URL of the search result.
- `title` (str): The title of the search result.
- `content` (Optional[str]): The content snippet of the search result.
- `query` (str): The query used to obtain this search result.

## Usage

Here's an example of how to use the SearxNG Search Tool:


```python
import os
from tool.searxng_search import SearxNGTool, SearxNGSearchToolConfig

# Initialize the tool with your SearxNG instance URL
config = SearxNGSearchToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=5)
search_tool = SearxNGTool(config=config)

# Define input data
input_data = SearxNGTool.input_schema(
    queries=["Python programming", "Machine learning", "Artificial intelligence"],
    category="news"
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
