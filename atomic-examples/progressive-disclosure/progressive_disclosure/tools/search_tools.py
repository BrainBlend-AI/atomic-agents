"""Tool for searching available MCP tools.

This tool enables the Tool Finder Agent to search through the registry
of available tools without loading their full schemas into context.
"""

from typing import Dict, List, Optional
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig
from progressive_disclosure.registry.tool_registry import ToolRegistry


################
# INPUT SCHEMA #
################
class SearchToolsInputSchema(BaseIOSchema):
    """Search for available tools that match a query.

    Use this tool to find relevant MCP tools for a given task.
    The search looks at tool names, descriptions, and keywords.
    """

    search_query: str = Field(
        ...,
        description="Search query to find relevant tools. Can include keywords describing the desired functionality.",
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return. Use fewer for focused tasks, more for exploratory searches.",
        ge=1,
        le=20,
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional category filter (e.g., 'math', 'search', 'file', 'data', 'web', 'text').",
    )


#################
# OUTPUT SCHEMA #
#################
class SearchToolsOutputSchema(BaseIOSchema):
    """Results from searching available tools."""

    matched_tools: List[str] = Field(
        ...,
        description="List of tool names that matched the search query, ordered by relevance.",
    )
    tool_descriptions: Dict[str, str] = Field(
        ...,
        description="Mapping of tool name to description for each matched tool.",
    )
    total_tools_available: int = Field(
        ...,
        description="Total number of tools available in the registry.",
    )
    search_query_used: str = Field(
        ...,
        description="The search query that was used.",
    )


#################
# CONFIGURATION #
#################
class SearchToolsConfig(BaseToolConfig):
    """Configuration for the SearchToolsTool."""

    registry: Optional[ToolRegistry] = None

    model_config = {"arbitrary_types_allowed": True}


#####################
# MAIN TOOL & LOGIC #
#####################
class SearchToolsTool(BaseTool[SearchToolsInputSchema, SearchToolsOutputSchema]):
    """Tool for searching available MCP tools by query.

    This is a key component of the progressive disclosure pattern,
    allowing the Tool Finder Agent to discover relevant tools without
    having all tool schemas in its context window.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register_from_mcp(mcp_definitions)
        >>> tool = SearchToolsTool(SearchToolsConfig(registry=registry))
        >>> result = tool.run(SearchToolsInputSchema(search_query="calculate math"))
        >>> print(result.matched_tools)
        ['AddNumbers', 'SubtractNumbers', 'MultiplyNumbers']
    """

    input_schema = SearchToolsInputSchema
    output_schema = SearchToolsOutputSchema

    def __init__(self, config: SearchToolsConfig = SearchToolsConfig()):
        """Initialize the SearchToolsTool.

        Args:
            config: Configuration containing the tool registry.
        """
        super().__init__(config)
        self._registry = config.registry

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry."""
        if self._registry is None:
            raise ValueError("Tool registry not configured. Pass a registry via SearchToolsConfig.")
        return self._registry

    def run(self, params: SearchToolsInputSchema) -> SearchToolsOutputSchema:
        """Execute the search and return matching tools.

        Args:
            params: Search parameters including query and optional filters.

        Returns:
            SearchToolsOutputSchema containing matched tools and their descriptions.
        """
        results = self.registry.search(
            query=params.search_query,
            max_results=params.max_results,
            category=params.category,
        )

        return SearchToolsOutputSchema(
            matched_tools=[tool.name for tool in results],
            tool_descriptions={tool.name: tool.description for tool in results},
            total_tools_available=len(self.registry),
            search_query_used=params.search_query,
        )


class ListAllToolsInputSchema(BaseIOSchema):
    """List all available tools in the registry.

    Use this to get an overview of all tools when you need to understand
    the full capabilities available.
    """

    include_categories: bool = Field(
        default=True,
        description="Whether to include category information for each tool.",
    )


class ListAllToolsOutputSchema(BaseIOSchema):
    """List of all available tools."""

    tools: List[Dict[str, str]] = Field(
        ...,
        description="List of tools with their name, description, and optionally category.",
    )
    total_count: int = Field(
        ...,
        description="Total number of tools available.",
    )
    categories_found: List[str] = Field(
        ...,
        description="List of unique categories found among the tools.",
    )


class ListAllToolsTool(BaseTool[ListAllToolsInputSchema, ListAllToolsOutputSchema]):
    """Tool for listing all available tools.

    Useful when the Tool Finder Agent needs to see the complete
    set of available capabilities.
    """

    input_schema = ListAllToolsInputSchema
    output_schema = ListAllToolsOutputSchema

    def __init__(self, config: SearchToolsConfig = SearchToolsConfig()):
        """Initialize the ListAllToolsTool.

        Args:
            config: Configuration containing the tool registry.
        """
        super().__init__(config)
        self._registry = config.registry

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry."""
        if self._registry is None:
            raise ValueError("Tool registry not configured. Pass a registry via SearchToolsConfig.")
        return self._registry

    def run(self, params: ListAllToolsInputSchema) -> ListAllToolsOutputSchema:
        """List all available tools.

        Args:
            params: Parameters for listing tools.

        Returns:
            ListAllToolsOutputSchema containing all tools.
        """
        all_tools = self.registry.get_all_metadata()
        categories = set()

        tools_list = []
        for tool in all_tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
            }
            if params.include_categories and tool.category:
                tool_info["category"] = tool.category
                categories.add(tool.category)
            tools_list.append(tool_info)

        return ListAllToolsOutputSchema(
            tools=tools_list,
            total_count=len(all_tools),
            categories_found=sorted(list(categories)),
        )


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from progressive_disclosure.registry.tool_registry import ToolMetadata

    # Create a test registry
    registry = ToolRegistry()
    registry.register(
        ToolMetadata(
            name="AddNumbers",
            description="Add two numbers together",
            keywords=["add", "sum", "plus", "arithmetic"],
            category="math",
        )
    )
    registry.register(
        ToolMetadata(
            name="SubtractNumbers",
            description="Subtract one number from another",
            keywords=["subtract", "minus", "difference", "arithmetic"],
            category="math",
        )
    )
    registry.register(
        ToolMetadata(
            name="SearchWeb",
            description="Search the web for information",
            keywords=["search", "web", "query", "find"],
            category="search",
        )
    )

    # Test search
    search_tool = SearchToolsTool(SearchToolsConfig(registry=registry))
    result = search_tool.run(SearchToolsInputSchema(search_query="add numbers math"))
    print("Search results:")
    print(f"  Matched: {result.matched_tools}")
    print(f"  Descriptions: {result.tool_descriptions}")

    # Test list all
    list_tool = ListAllToolsTool(SearchToolsConfig(registry=registry))
    all_result = list_tool.run(ListAllToolsInputSchema())
    print(f"\nAll tools ({all_result.total_count}):")
    for tool in all_result.tools:
        print(f"  - {tool['name']}: {tool['description']}")
