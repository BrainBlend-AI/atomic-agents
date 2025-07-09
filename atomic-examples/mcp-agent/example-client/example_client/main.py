# pyright: reportInvalidTypeForm=false
"""
Main entry point for the MCP Agent example client.
This file serves as a launcher that can run either the STDIO or SSE transport version of the MCP agent.
"""

import argparse
import sys
from atomic_agents.lib.factories import MCPTransportType


def main():
    """Parse command line arguments and launch the appropriate implementation."""
    parser = argparse.ArgumentParser(description="MCP Agent example client")

    # Get available transport choices from the enum
    transport_choices = [transport.value for transport in MCPTransportType]

    parser.add_argument(
        "--transport",
        choices=transport_choices,
        default=MCPTransportType.STDIO.value,
        help=f"Transport method to use for MCP communication. Available: {', '.join(transport_choices)}",
    )
    args = parser.parse_args()

    # Map transport values to their corresponding main functions
    transport_mapping = {
        MCPTransportType.STDIO.value: ("example_client.main_stdio", "main"),
        MCPTransportType.SSE.value: ("example_client.main_sse", "main"),
        MCPTransportType.HTTP_STREAM.value: ("example_client.main_http", "main"),
    }

    if args.transport in transport_mapping:
        module_name, function_name = transport_mapping[args.transport]
        try:
            module = __import__(module_name, fromlist=[function_name])
            main_func = getattr(module, function_name)
            main_func()
        except ImportError as e:
            print(f"Failed to import {args.transport} implementation: {e}")
            sys.exit(1)
    else:
        print(f"Unknown transport: {args.transport}")
        print(f"Available transports: {', '.join(transport_choices)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
