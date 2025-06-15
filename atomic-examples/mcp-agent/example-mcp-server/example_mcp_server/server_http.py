"""example-mcp-server MCP Server HTTP Stream Transport."""

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import uvicorn
from typing import List
import json

from example_mcp_server.services.tool_service import ToolService
from example_mcp_server.services.resource_service import ResourceService
from example_mcp_server.interfaces.tool import Tool
from example_mcp_server.interfaces.resource import Resource
from example_mcp_server.tools import AddNumbersTool, SubtractNumbersTool, MultiplyNumbersTool, DivideNumbersTool


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
    return []


def create_http_app(mcp_server: Server) -> Starlette:
    """Create a Starlette app supporting HTTP Stream Transport."""
    
    # Create SSE transport for handling the connection
    sse = SseServerTransport("/messages/")
    
    async def handle_mcp(request: Request):
        """Handle MCP requests over HTTP Stream - accepts GET for connection."""
        try:
            # Use SSE transport pattern for HTTP stream
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
                
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0", 
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            return JSONResponse(error_response, status_code=500)

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
            Route("/mcp", handle_mcp, methods=["GET", "POST"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        middleware=middleware,
    )


# Initialize FastMCP server with HTTP transport - same as SSE
mcp = FastMCP("example-mcp-server")
tool_service = ToolService()
resource_service = ResourceService()

# Register all tools and their MCP handlers - same as SSE
tool_service.register_tools(get_available_tools())
tool_service.register_mcp_handlers(mcp)

# Register all resources and their MCP handlers - same as SSE  
resource_service.register_resources(get_available_resources())
resource_service.register_mcp_handlers(mcp)

# Get the MCP server - same as SSE
mcp_server = mcp._mcp_server  # noqa: WPS437

# Create the Starlette app
app = create_http_app(mcp_server)

# Export the app
__all__ = ["app"]


def main():
    """Entry point for the HTTP Stream Transport server."""
    import argparse

    parser = argparse.ArgumentParser(description="Run MCP HTTP Stream server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to"
    )
    parser.add_argument(
        "--port", type=int, default=6969, help="Port to listen on"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    args = parser.parse_args()
    
    print(f"MCP HTTP Stream Server starting on {args.host}:{args.port}")
    
    uvicorn.run(
        "example_mcp_server.server_http:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=["example_mcp_server"],
        timeout_graceful_shutdown=5,
    )


if __name__ == "__main__":
    main()
