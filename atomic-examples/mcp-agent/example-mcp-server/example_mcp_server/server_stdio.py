"""example-mcp-server MCP Server implementation."""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

from example_mcp_server.services.tool_service import ToolService
from example_mcp_server.services.resource_service import ResourceService
from example_mcp_server.interfaces.tool import Tool
from example_mcp_server.interfaces.resource import Resource

# from example_mcp_server.tools import HelloWorldTool # Removed
from example_mcp_server.tools import (  # Added imports for new tools
    AddNumbersTool,
    SubtractNumbersTool,
    MultiplyNumbersTool,
    DivideNumbersTool,
)


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    return [
        # HelloWorldTool(), # Removed
        AddNumbersTool(),
        SubtractNumbersTool(),
        MultiplyNumbersTool(),
        DivideNumbersTool(),
        # Add more tools here as you create them
    ]


def get_available_resources() -> List[Resource]:
    """Get list of all available resources."""
    return [
        # Add more resources here as you create them
    ]


def main():
    """Entry point for the server."""
    mcp = FastMCP("example-mcp-server")
    tool_service = ToolService()
    resource_service = ResourceService()

    # Register all tools and their MCP handlers
    tool_service.register_tools(get_available_tools())
    tool_service.register_mcp_handlers(mcp)

    # Register all resources and their MCP handlers
    resource_service.register_resources(get_available_resources())
    resource_service.register_mcp_handlers(mcp)

    mcp.run()


if __name__ == "__main__":
    main()
