"""example-mcp-server MCP Server unified entry point."""

import argparse
import sys
from typing import Literal


def main():
    """Entry point for the server."""
    parser = argparse.ArgumentParser(description="example-mcp-server MCP Server")
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["stdio", "sse"],
        help="Server mode: stdio for standard I/O or sse for HTTP Server-Sent Events",
    )

    # SSE specific arguments
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (SSE mode only)")
    parser.add_argument("--port", type=int, default=6969, help="Port to listen on (SSE mode only)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development (SSE mode only)")

    args = parser.parse_args()

    if args.mode == "stdio":
        # Import and run the stdio server
        from example_mcp_server.server_stdio import main as stdio_main

        stdio_main()
    elif args.mode == "sse":
        # Import and run the SSE server with appropriate arguments
        from example_mcp_server.server_sse import main as sse_main

        sys.argv = [sys.argv[0], "--host", args.host, "--port", str(args.port)]
        if args.reload:
            sys.argv.append("--reload")
        sse_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
