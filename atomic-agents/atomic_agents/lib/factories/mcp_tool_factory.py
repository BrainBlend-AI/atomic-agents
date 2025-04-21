import asyncio
import logging
from typing import Any, List, Type, Optional, Union, Tuple, cast
from contextlib import AsyncExitStack
import shlex

from pydantic import create_model, Field, BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool
from atomic_agents.lib.factories.schema_transformer import SchemaTransformer
from atomic_agents.lib.factories.tool_definition_service import ToolDefinitionService, MCPToolDefinition

logger = logging.getLogger(__name__)


class MCPToolOutputSchema(BaseIOSchema):
    """Generic output schema for dynamically generated MCP tools."""

    result: Any = Field(..., description="The result returned by the MCP tool.")


class MCPToolFactory:
    """Factory for creating MCP tool classes."""

    def __init__(
        self,
        mcp_endpoint: Optional[str] = None,
        use_stdio: bool = False,
        client_session: Optional[ClientSession] = None,
        event_loop: Optional[asyncio.AbstractEventLoop] = None,
        working_directory: Optional[str] = None,
    ):
        """
        Initialize the factory.

        Args:
            mcp_endpoint: URL of the MCP server (for SSE) or the full command to run the server (for STDIO)
            use_stdio: If True, use STDIO transport instead of SSE
            client_session: Optional pre-initialized ClientSession for reuse
            event_loop: Optional event loop for running asynchronous operations
            working_directory: Optional working directory to use when running STDIO commands
        """
        self.mcp_endpoint = mcp_endpoint
        self.use_stdio = use_stdio
        self.client_session = client_session
        self.event_loop = event_loop
        self.schema_transformer = SchemaTransformer()
        self.working_directory = working_directory

        # Validate configuration
        if client_session is not None and event_loop is None:
            raise ValueError("When `client_session` is provided an `event_loop` must also be supplied.")
        if not mcp_endpoint and client_session is None:
            raise ValueError("`mcp_endpoint` must be provided when no `client_session` is supplied.")

    def create_tools(self) -> List[Type[BaseTool]]:
        """
        Create tool classes from the configured endpoint or session.

        Returns:
            List of dynamically generated BaseTool subclasses
        """
        tool_definitions = self._fetch_tool_definitions()
        if not tool_definitions:
            return []

        return self._create_tool_classes(tool_definitions)

    def _fetch_tool_definitions(self) -> List[MCPToolDefinition]:
        """
        Fetch tool definitions using the appropriate method.

        Returns:
            List of tool definitions
        """
        if self.client_session is not None:
            # Use existing session
            async def _gather_defs():
                return await ToolDefinitionService.fetch_definitions_from_session(self.client_session)  # pragma: no cover

            return cast(asyncio.AbstractEventLoop, self.event_loop).run_until_complete(_gather_defs())  # pragma: no cover
        else:
            # Create new connection
            service = ToolDefinitionService(self.mcp_endpoint, self.use_stdio, self.working_directory)
            return asyncio.run(service.fetch_definitions())

    def _create_tool_classes(self, tool_definitions: List[MCPToolDefinition]) -> List[Type[BaseTool]]:
        """
        Create tool classes from definitions.

        Args:
            tool_definitions: List of tool definitions

        Returns:
            List of dynamically generated BaseTool subclasses
        """
        generated_tools = []

        for definition in tool_definitions:
            try:
                tool_name = definition.name
                tool_description = definition.description or f"Dynamically generated tool for MCP tool: {tool_name}"
                input_schema_dict = definition.input_schema

                # Create input schema
                InputSchema = self.schema_transformer.create_model_from_schema(
                    input_schema_dict,
                    f"{tool_name}InputSchema",
                    tool_name,
                    f"Input schema for {tool_name}",
                )

                # Create output schema
                OutputSchema = type(
                    f"{tool_name}OutputSchema", (MCPToolOutputSchema,), {"__doc__": f"Output schema for {tool_name}"}
                )

                # Create run method
                def run_tool_sync(self, params: InputSchema) -> OutputSchema:  # type: ignore
                    bound_tool_name = self.mcp_tool_name
                    bound_mcp_endpoint = self.mcp_endpoint  # May be None when using external session
                    bound_use_stdio = self.use_stdio
                    persistent_session: Optional[ClientSession] = getattr(self, "_client_session", None)
                    loop: Optional[asyncio.AbstractEventLoop] = getattr(self, "_event_loop", None)
                    bound_working_directory = getattr(self, "working_directory", None)

                    # Get arguments, excluding tool_name
                    arguments = params.model_dump(exclude={"tool_name"}, exclude_none=True)

                    async def _connect_and_call():
                        stack = AsyncExitStack()
                        try:
                            if bound_use_stdio:
                                # Split the command string into the command and its arguments
                                command_parts = shlex.split(bound_mcp_endpoint)
                                if not command_parts:
                                    raise ValueError("STDIO command string cannot be empty.")
                                command = command_parts[0]
                                args = command_parts[1:]
                                logger.debug(f"Executing tool '{bound_tool_name}' via STDIO: command='{command}', args={args}")
                                server_params = StdioServerParameters(
                                    command=command, args=args, env=None, cwd=bound_working_directory
                                )
                                stdio_transport = await stack.enter_async_context(stdio_client(server_params))
                                read_stream, write_stream = stdio_transport
                            else:
                                sse_endpoint = f"{bound_mcp_endpoint}/sse"
                                logger.debug(f"Executing tool '{bound_tool_name}' via SSE: endpoint={sse_endpoint}")
                                sse_transport = await stack.enter_async_context(sse_client(sse_endpoint))
                                read_stream, write_stream = sse_transport

                            session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
                            await session.initialize()

                            # Ensure arguments is a dict, even if empty
                            call_args = arguments if isinstance(arguments, dict) else {}
                            tool_result = await session.call_tool(name=bound_tool_name, arguments=call_args)
                            return tool_result
                        finally:
                            await stack.aclose()

                    async def _call_with_persistent_session():
                        # Ensure arguments is a dict, even if empty
                        call_args = arguments if isinstance(arguments, dict) else {}
                        return await persistent_session.call_tool(name=bound_tool_name, arguments=call_args)

                    try:
                        if persistent_session is not None:
                            # Use the always‑on session/loop supplied at construction time.
                            tool_result = cast(asyncio.AbstractEventLoop, loop).run_until_complete(
                                _call_with_persistent_session()
                            )
                        else:
                            # Legacy behaviour – open a fresh connection per invocation.
                            tool_result = asyncio.run(_connect_and_call())

                        # Process the result
                        if isinstance(tool_result, BaseModel) and hasattr(tool_result, "content"):
                            actual_result_content = tool_result.content
                        elif isinstance(tool_result, dict) and "content" in tool_result:
                            actual_result_content = tool_result["content"]
                        else:
                            actual_result_content = tool_result

                        return OutputSchema(result=actual_result_content)

                    except Exception as e:
                        logger.error(f"Error executing MCP tool '{bound_tool_name}': {e}", exc_info=True)
                        raise RuntimeError(f"Failed to execute MCP tool '{bound_tool_name}': {e}") from e

                # Create the tool class
                tool_class = type(
                    tool_name,
                    (BaseTool,),
                    {
                        "input_schema": InputSchema,
                        "output_schema": OutputSchema,
                        "run": run_tool_sync,
                        "__doc__": tool_description,
                        "mcp_tool_name": tool_name,
                        "mcp_endpoint": self.mcp_endpoint,
                        "use_stdio": self.use_stdio,
                        "_client_session": self.client_session,
                        "_event_loop": self.event_loop,
                        "working_directory": self.working_directory,
                    },
                )

                generated_tools.append(tool_class)

            except Exception as e:
                logger.error(f"Error generating class for tool '{definition.name}': {e}", exc_info=True)
                continue

        return generated_tools

    def create_orchestrator_schema(self, tools: List[Type[BaseTool]]) -> Optional[Type[BaseIOSchema]]:
        """
        Create an orchestrator schema for the given tools.

        Args:
            tools: List of tool classes

        Returns:
            Orchestrator schema or None if no tools provided
        """
        if not tools:
            logger.warning("No tools provided to create orchestrator schema")
            return None

        tool_schemas = [ToolClass.input_schema for ToolClass in tools]

        # Create a Union of all tool input schemas
        ToolParameterUnion = Union[tuple(tool_schemas)]

        # Dynamically create the output schema
        orchestrator_schema = create_model(
            "MCPOrchestratorOutputSchema",
            __doc__="Output schema for the MCP Orchestrator Agent. Contains the parameters for the selected tool.",
            __base__=BaseIOSchema,
            tool_parameters=(
                ToolParameterUnion,
                Field(
                    ...,
                    description="The parameters for the selected tool, matching its specific schema (which includes the 'tool_name').",
                ),
            ),
        )

        return orchestrator_schema


# Public API functions
def fetch_mcp_tools(
    mcp_endpoint: Optional[str] = None,
    use_stdio: bool = False,
    *,
    client_session: Optional[ClientSession] = None,
    event_loop: Optional[asyncio.AbstractEventLoop] = None,
    working_directory: Optional[str] = None,
) -> List[Type[BaseTool]]:
    """
    Connects to an MCP server via SSE or STDIO, discovers tool definitions, and dynamically generates
    synchronous Atomic Agents compatible BaseTool subclasses for each tool.
    Each generated tool will establish its own connection when its `run` method is called.

    Args:
        mcp_endpoint: URL of the MCP server (for SSE) or the full command string to run the server (for STDIO).
        use_stdio: If True, use STDIO transport instead of SSE.
        client_session: Optional pre-initialized ClientSession for reuse.
        event_loop: Optional event loop for running asynchronous operations.
        working_directory: Optional working directory to use when running STDIO commands.
    """
    factory = MCPToolFactory(mcp_endpoint, use_stdio, client_session, event_loop, working_directory)
    return factory.create_tools()


def create_mcp_orchestrator_schema(tools: List[Type[BaseTool]]) -> Optional[Type[BaseIOSchema]]:
    """
    Creates a schema for the MCP Orchestrator's output using the Union of all tool input schemas.

    Args:
        tools: List of dynamically generated MCP tool classes

    Returns:
        A Pydantic model class to be used as the output schema for an orchestrator agent
    """
    # Bypass constructor validation since orchestrator schema does not require endpoint or session
    factory = object.__new__(MCPToolFactory)
    return MCPToolFactory.create_orchestrator_schema(factory, tools)


def fetch_mcp_tools_with_schema(
    mcp_endpoint: Optional[str] = None,
    use_stdio: bool = False,
    *,
    client_session: Optional[ClientSession] = None,
    event_loop: Optional[asyncio.AbstractEventLoop] = None,
    working_directory: Optional[str] = None,
) -> Tuple[List[Type[BaseTool]], Optional[Type[BaseIOSchema]]]:
    """
    Fetches MCP tools and creates an orchestrator schema for them. Returns both as a tuple.

    Args:
        mcp_endpoint: URL of the MCP server (for SSE) or the full command string to run the server (for STDIO).
        use_stdio: If True, use STDIO transport instead of SSE.
        client_session: Optional pre-initialized ClientSession for reuse.
        event_loop: Optional event loop for running asynchronous operations.
        working_directory: Optional working directory to use when running STDIO commands.

    Returns:
        A tuple containing:
        - List of dynamically generated tool classes
        - Orchestrator output schema with Union of tool input schemas, or None if no tools found.
    """
    factory = MCPToolFactory(mcp_endpoint, use_stdio, client_session, event_loop, working_directory)
    tools = factory.create_tools()
    if not tools:
        return [], None

    orchestrator_schema = factory.create_orchestrator_schema(tools)
    return tools, orchestrator_schema
