#!/usr/bin/env python3
"""
Demo script to list available tools from MCP servers.

This script demonstrates how to:
1. Connect to an MCP server using STDIO transport
2. Connect to an MCP server using SSE transport
3. List available tools from both transports
4. Call each available tool with appropriate input
"""

import asyncio
import random
import json
import datetime
from contextlib import AsyncExitStack
from typing import Dict, Any

# Import MCP client libraries
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

# Rich library for pretty output
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax


class MCPClient:
    """A simple client that can connect to MCP servers using either STDIO or SSE transport."""

    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.transport_type = None  # Will be set to 'stdio' or 'sse'

    async def connect_to_stdio_server(self, server_script_path: str):
        """Connect to an MCP server via STDIO transport.

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        try:
            # Determine script type (Python or JavaScript)
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")

            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")

            command = "python" if is_python else "node"

            # Set up STDIO transport
            server_params = StdioServerParameters(command=command, args=[server_script_path], env=None)

            # Connect to the server
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport

            # Initialize the session
            self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            await self.session.initialize()
            self.transport_type = "stdio"

        except Exception as e:
            await self.cleanup()
            raise e

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server via SSE transport.

        Args:
            server_url: URL of the SSE server (e.g., http://localhost:6969)
        """
        try:
            # Initialize SSE transport with the correct endpoint
            sse_transport = await self.exit_stack.enter_async_context(sse_client(f"{server_url}/sse"))
            read_stream, write_stream = sse_transport

            # Initialize the session
            self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            await self.session.initialize()
            self.transport_type = "sse"

        except Exception as e:
            await self.cleanup()
            raise e

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a tool with the given arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            The result of the tool call
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        return await self.session.call_tool(name=tool_name, arguments=arguments)

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.exit_stack.aclose()
            self.session = None
            self.transport_type = None


def generate_input_for_tool(tool_name: str, input_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate appropriate input based on the tool name and input schema.

    This function creates sensible inputs for different tool types.

    Args:
        tool_name: The name of the tool
        input_schema: The JSON schema of the tool input

    Returns:
        A dictionary with values matching the schema
    """
    result = {}

    # Special handling for known tool types
    if tool_name == "AddNumbers":
        result = {"number1": random.randint(1, 100), "number2": random.randint(1, 100)}
    elif tool_name == "DateDifference":
        # Generate two dates with a reasonable difference
        today = datetime.date.today()
        days_diff = random.randint(1, 30)
        date1 = today - datetime.timedelta(days=days_diff)
        date2 = today
        result = {"date1": date1.isoformat(), "date2": date2.isoformat()}
    elif tool_name == "ReverseString":
        words = ["hello", "world", "testing", "reverse", "string", "tool"]
        result = {"text_to_reverse": random.choice(words)}
    elif tool_name == "RandomNumber":
        min_val = random.randint(0, 50)
        max_val = random.randint(min_val + 10, min_val + 100)
        result = {"min_value": min_val, "max_value": max_val}
    elif tool_name == "CurrentTime":
        # This tool doesn't need any input
        result = {}
    else:
        # Generic handling for unknown tools
        if "properties" in input_schema:
            for prop_name, prop_schema in input_schema["properties"].items():
                prop_type = prop_schema.get("type")

                if prop_type == "string":
                    result[prop_name] = f"random_string_{random.randint(1, 1000)}"
                elif prop_type == "number" or prop_type == "integer":
                    result[prop_name] = random.randint(1, 100)
                elif prop_type == "boolean":
                    result[prop_name] = random.choice([True, False])
                elif prop_type == "array":
                    result[prop_name] = []
                    if random.choice([True, False]):
                        item_type = prop_schema.get("items", {}).get("type", "string")
                        if item_type == "string":
                            result[prop_name].append(f"item_{random.randint(1, 100)}")
                        elif item_type == "number" or item_type == "integer":
                            result[prop_name].append(random.randint(1, 100))
                elif prop_type == "object":
                    result[prop_name] = {}

    return result


def format_parameter_info(schema: Dict[str, Any]) -> str:
    """Format parameter information including descriptions.

    Args:
        schema: The JSON schema of a tool input

    Returns:
        A formatted string with parameter information
    """
    result = []

    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            prop_type = prop_schema.get("type", "unknown")
            description = prop_schema.get("description", "No description")
            default = prop_schema.get("default", "required")

            param_info = f"{prop_name} ({prop_type})"
            if default != "required":
                param_info += f" = {default}"
            param_info += f": {description}"

            result.append(param_info)

    return "\n".join(result) if result else "No parameters"


async def test_tools_with_client(client: MCPClient, console: Console, connection_info: str):
    """Test all tools with the provided client.

    Args:
        client: The initialized MCP client
        console: Rich console for output
        connection_info: Info about the connection for display
    """
    # List available tools from the server
    console.print(f"\n[bold green]Available Tools ({connection_info}):[/bold green]")
    response = await client.session.list_tools()

    # Create a table to display the tools
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool Name")
    table.add_column("Description")
    table.add_column("Parameters")

    # Add each tool to the table
    for tool in response.tools:
        parameters = format_parameter_info(tool.inputSchema)

        table.add_row(tool.name, tool.description or "No description available", parameters)

    console.print(table)

    # Call each available tool with appropriate input
    for tool in response.tools:
        console.print(f"\n[bold yellow]Calling tool ({connection_info}): {tool.name}[/bold yellow]")

        # Generate appropriate input based on the tool
        input_args = generate_input_for_tool(tool.name, tool.inputSchema)

        # Display the input we're using
        console.print("[bold cyan]Input arguments:[/bold cyan]")
        syntax = Syntax(json.dumps(input_args, indent=2), "json")
        console.print(syntax)

        # Call the tool
        result = await client.call_tool(tool.name, input_args)

        # Display the result
        console.print("[bold green]Result:[/bold green]")
        if hasattr(result, "content"):
            for content_item in result.content:
                if content_item.type == "text":
                    console.print(content_item.text)
                else:
                    console.print(f"Content type: {content_item.type}")
        else:
            # Try to format as JSON if possible
            try:
                if isinstance(result, dict) or isinstance(result, list):
                    console.print(Syntax(json.dumps(result, indent=2), "json"))
                else:
                    console.print(str(result))
            except Exception:
                console.print(str(result))


async def list_server_tools():
    """Connect to MCP servers using both STDIO and SSE in sequence and list available tools."""
    console = Console()
    client = MCPClient()

    # Define the paths/URLs for both types of servers
    stdio_server_path = "example_mcp_server/server_stdio.py"  # Path to STDIO server
    sse_server_url = "http://localhost:6969"  # SSE server URL (default port)

    try:
        # 1. First test STDIO transport
        console.print("\n[bold blue]===== Testing STDIO Transport =====")
        console.print("[bold blue]Connecting to MCP server via STDIO...[/bold blue]")

        # Connect to the STDIO server
        await client.connect_to_stdio_server(stdio_server_path)

        # Test the tools available through STDIO
        await test_tools_with_client(client, console, "STDIO transport")

        # Clean up STDIO connection before moving to SSE
        await client.cleanup()

        # 2. Then test SSE transport
        console.print("\n[bold blue]===== Testing SSE Transport =====")
        console.print("[bold blue]Connecting to MCP server via SSE...[/bold blue]")

        # Connect to the SSE server
        await client.connect_to_sse_server(sse_server_url)

        # Test the tools available through SSE
        await test_tools_with_client(client, console, "SSE transport")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    finally:
        # Clean up resources
        await client.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(list_server_tools())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
