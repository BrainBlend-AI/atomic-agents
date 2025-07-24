"""Module for fetching tool definitions from MCP endpoints."""

import logging
import shlex
from contextlib import AsyncExitStack
from typing import List, NamedTuple, Optional, Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

# Try to import streamable_http_client - this may vary depending on the MCP library version
try:
    from mcp.client.streamable_http import streamable_http_client
    HAS_STREAMABLE_HTTP = True
except ImportError:
    try:
        # Alternative import path
        from mcp.client.streamablehttp import streamable_http_client
        HAS_STREAMABLE_HTTP = True
    except ImportError:
        HAS_STREAMABLE_HTTP = False
        streamable_http_client = None

logger = logging.getLogger(__name__)


class MCPToolDefinition(NamedTuple):
    """Definition of an MCP tool."""

    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]


class ToolDefinitionService:
    """Service for fetching tool definitions from MCP endpoints."""

    def __init__(
        self, 
        endpoint: Optional[str] = None, 
        use_stdio: bool = False, 
        working_directory: Optional[str] = None,
        use_streamable_http: bool = False,
        streamable_http_headers: Optional[dict] = None,
    ):
        """
        Initialize the service.

        Args:
            endpoint: URL of the MCP server (for SSE/StreamableHTTP) or command string (for STDIO)
            use_stdio: Whether to use STDIO transport
            working_directory: Optional working directory to use when running STDIO commands
            use_streamable_http: Whether to use StreamableHTTP transport
            streamable_http_headers: Optional headers to send with StreamableHTTP requests
        """
        self.endpoint = endpoint
        self.use_stdio = use_stdio
        self.working_directory = working_directory
        self.use_streamable_http = use_streamable_http
        self.streamable_http_headers = streamable_http_headers or {}

        # Validate configuration
        transport_count = sum([use_stdio, use_streamable_http])
        if transport_count > 1:
            raise ValueError("Only one of `use_stdio` or `use_streamable_http` can be True.")
        
        # Check if streamable HTTP is available when requested
        if use_streamable_http and not HAS_STREAMABLE_HTTP:
            raise ValueError(
                "StreamableHTTP transport requested but `mcp.client.streamable_http` or "
                "`mcp.client.streamablehttp` is not available. Please ensure you have a compatible "
                "version of the MCP library that supports StreamableHTTP transport."
            )

    async def fetch_definitions(self) -> List[MCPToolDefinition]:
        """
        Fetch tool definitions from the configured endpoint.

        Returns:
            List of tool definitions

        Raises:
            ConnectionError: If connection to the MCP server fails
            ValueError: If the STDIO command string is empty
            RuntimeError: For other unexpected errors
        """
        if not self.endpoint:
            raise ValueError("Endpoint is required")

        definitions = []
        stack = AsyncExitStack()
        try:
            if self.use_stdio:
                # Split the command string into the command and its arguments
                command_parts = shlex.split(self.endpoint)
                if not command_parts:
                    raise ValueError("STDIO command string cannot be empty.")
                command = command_parts[0]
                args = command_parts[1:]
                logger.info(f"Attempting STDIO connection with command='{command}', args={args}")
                server_params = StdioServerParameters(command=command, args=args, env=None, cwd=self.working_directory)
                stdio_transport = await stack.enter_async_context(stdio_client(server_params))
                read_stream, write_stream = stdio_transport
            elif self.use_streamable_http:
                logger.info(f"Attempting StreamableHTTP connection to {self.endpoint}")
                streamable_http_transport = await stack.enter_async_context(
                    streamable_http_client(self.endpoint, headers=self.streamable_http_headers)
                )
                read_stream, write_stream = streamable_http_transport
            else:
                sse_endpoint = f"{self.endpoint}/sse"
                logger.info(f"Attempting SSE connection to {sse_endpoint}")
                sse_transport = await stack.enter_async_context(sse_client(sse_endpoint))
                read_stream, write_stream = sse_transport

            session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
            definitions = await self.fetch_definitions_from_session(session)

        except ConnectionError as e:
            logger.error(f"Error fetching MCP tool definitions from {self.endpoint}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching MCP tool definitions from {self.endpoint}: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during tool definition fetching: {e}") from e
        finally:
            await stack.aclose()

        return definitions

    @staticmethod
    async def fetch_definitions_from_session(session: ClientSession) -> List[MCPToolDefinition]:
        """
        Fetch tool definitions from an existing session.

        Args:
            session: MCP client session

        Returns:
            List of tool definitions

        Raises:
            Exception: If listing tools fails
        """
        definitions: List[MCPToolDefinition] = []
        try:
            # `initialize` is idempotent – calling it twice is safe and
            # ensures the session is ready.
            await session.initialize()
            response = await session.list_tools()
            for mcp_tool in response.tools:
                definitions.append(
                    MCPToolDefinition(
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        input_schema=mcp_tool.inputSchema or {"type": "object", "properties": {}},
                    )
                )

            if not definitions:
                logger.warning("No tool definitions found on MCP server")

        except Exception as e:
            logger.error("Failed to list tools via MCP session: %s", e, exc_info=True)
            raise

        return definitions
