"""example-mcp-server MCP Server HTTP Stream Transport."""

from typing import List
import argparse

import uvicorn
from starlette.middleware.cors import CORSMiddleware

from mcp.server.fastmcp import FastMCP

from example_mcp_server.services.tool_service import ToolService
from example_mcp_server.services.resource_service import ResourceService
from example_mcp_server.services.prompt_service import PromptService
from example_mcp_server.interfaces.tool import Tool
from example_mcp_server.interfaces.resource import Resource
from example_mcp_server.interfaces.prompt import Prompt
from example_mcp_server.tools import (
    AddNumbersTool,
    SubtractNumbersTool,
    MultiplyNumbersTool,
    DivideNumbersTool,
    BatchCalculatorTool,
)
from example_mcp_server.resources.sample_resources import TestWeatherResource
from example_mcp_server.prompts.sample_prompts import GreetingPrompt


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    return [
        AddNumbersTool(),
        SubtractNumbersTool(),
        MultiplyNumbersTool(),
        DivideNumbersTool(),
        BatchCalculatorTool(),
    ]


def get_available_resources() -> List[Resource]:
    """Get list of all available resources."""
    return [
        TestWeatherResource(),
        # Add more resources here as you create them
    ]


def get_available_prompts() -> List[Prompt]:
    """Get list of all available prompts."""
    return [
        GreetingPrompt(),
        # Add more prompts here as you create them
    ]


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP("example-mcp-server")
    tool_service = ToolService()
    resource_service = ResourceService()
    prompt_service = PromptService()

    # Register all tools and their MCP handlers
    tool_service.register_tools(get_available_tools())
    tool_service.register_mcp_handlers(mcp)

    # Register all resources and their MCP handlers
    resource_service.register_resources(get_available_resources())
    resource_service.register_mcp_handlers(mcp)

    # Register all prompts and their MCP handlers
    prompt_service.register_prompts(get_available_prompts())
    prompt_service.register_mcp_handlers(mcp)

    return mcp


def create_http_app():
    """Create a FastMCP HTTP app with CORS middleware."""
    mcp_server = create_mcp_server()

    # Use FastMCP directly as the app instead of mounting it
    # This avoids the task group initialization issue
    # See: https://github.com/modelcontextprotocol/python-sdk/issues/732
    app = mcp_server.streamable_http_app()  # type: ignore[attr-defined]

    # Apply CORS middleware manually
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    return app


def main():
    """Entry point for the HTTP Stream Transport server."""
    parser = argparse.ArgumentParser(description="Run MCP HTTP Stream server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6969, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    app = create_http_app()
    print(f"MCP HTTP Stream Server starting on {args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
