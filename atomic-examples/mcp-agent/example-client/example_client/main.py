# pyright: reportInvalidTypeForm=false
"""
Main entry point for the MCP Agent example client.
This file serves as a launcher that can run either the STDIO or SSE transport version of the MCP agent.
"""

import argparse
import sys


def main():
    """Parse command line arguments and launch the appropriate implementation."""
    parser = argparse.ArgumentParser(description="MCP Agent example client")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport method to use for MCP communication (stdio or sse)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        # Import and run STDIO implementation
        try:
            from example_client.main_stdio import main as stdio_main

            stdio_main()
        except ImportError as e:
            print(f"Failed to import STDIO implementation: {e}")
            sys.exit(1)
    else:
        # Import and run SSE implementation
        try:
            from example_client.main_sse import main as sse_main

            sse_main()
        except ImportError as e:
            print(f"Failed to import SSE implementation: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
