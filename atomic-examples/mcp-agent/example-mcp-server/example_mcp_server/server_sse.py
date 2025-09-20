"""example-mcp-server MCP Server implementation with SSE transport."""

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from typing import List
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from example_mcp_server.services.tool_service import ToolService
from example_mcp_server.services.resource_service import ResourceService
from example_mcp_server.services.prompt_service import PromptService
from example_mcp_server.interfaces.tool import Tool
from example_mcp_server.interfaces.resource import Resource
from example_mcp_server.interfaces.prompt import Prompt
from example_mcp_server.tools import AddNumbersTool, SubtractNumbersTool, MultiplyNumbersTool, DivideNumbersTool
from example_mcp_server.resources.sample_resources import TestWeatherResource
from example_mcp_server.prompts.sample_prompts import GreetingPrompt


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    return [
        AddNumbersTool(),
        SubtractNumbersTool(),
        MultiplyNumbersTool(),
        DivideNumbersTool(),
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


def create_starlette_app(mcp_server: Server) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
        return Response("SSE connection closed", status_code=200)

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    ]

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        middleware=middleware,
    )


# Initialize FastMCP server with SSE
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

# Get the MCP server
mcp_server = mcp._mcp_server  # noqa: WPS437

# Create the Starlette app
app = create_starlette_app(mcp_server)

# Export the app
__all__ = ["app"]


def main():
    """Entry point for the server."""
    import argparse

    parser = argparse.ArgumentParser(description="Run MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6969, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Run the server with auto-reload if enabled
    uvicorn.run(
        "example_mcp_server.server_sse:app",  # Use the app from server_sse.py directly
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=["example_mcp_server"],  # Watch this directory for changes
        timeout_graceful_shutdown=5,  # Add timeout
    )


if __name__ == "__main__":
    main()
