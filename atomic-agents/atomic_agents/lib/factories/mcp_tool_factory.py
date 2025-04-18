import asyncio
import typing
import logging
import json
import random
import datetime
from typing import Any, Dict, List, Type, Optional, Union, NamedTuple, Tuple, Literal
from contextlib import AsyncExitStack

from pydantic import create_model, Field, BaseModel

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool

logger = logging.getLogger(__name__)

JSON_TYPE_MAP = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


class MCPToolOutputSchema(BaseIOSchema):
    """Generic output schema for dynamically generated MCP tools."""

    result: Any = Field(..., description="The result returned by the MCP tool.")


def _json_schema_to_pydantic_field(prop_schema: Dict[str, Any], required: bool) -> tuple:
    json_type = prop_schema.get("type")
    description = prop_schema.get("description")
    default = prop_schema.get("default")
    python_type: Any = Any
    if json_type in JSON_TYPE_MAP:
        python_type = JSON_TYPE_MAP[json_type]
        if json_type == "array":
            items_schema = prop_schema.get("items", {})
            item_type_str = items_schema.get("type")
            if item_type_str in JSON_TYPE_MAP:
                python_type = List[JSON_TYPE_MAP[item_type_str]]
            else:
                python_type = List[Any]
        elif json_type == "object":
            python_type = Dict[str, Any]
    field_kwargs = {"description": description}
    if required:
        field_kwargs["default"] = ...
    elif default is not None:
        field_kwargs["default"] = default
    else:
        python_type = Optional[python_type]
        field_kwargs["default"] = None
    return (python_type, Field(**field_kwargs))


def json_schema_to_pydantic_model(
    schema: Dict[str, Any],
    model_name: str,
    tool_name_literal: str,
    docstring: Optional[str] = None,
) -> Type[BaseIOSchema]:
    """
    Dynamically creates a Pydantic model subclassing BaseIOSchema from a JSON schema dictionary.
    Includes a 'tool_name' field with a Literal type matching the provided tool name.
    """
    fields = {}
    required_fields = set(schema.get("required", []))
    properties = schema.get("properties")
    if properties:
        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required_fields
            fields[prop_name] = _json_schema_to_pydantic_field(prop_schema, is_required)
    elif schema.get("type") == "object" and not properties:
        pass
    elif schema:
        logger.warning(
            f"Schema for {model_name} is not a typical object with properties. Fields might be empty beyond tool_name."
        )

    fields["tool_name"] = (
        Literal[tool_name_literal],
        Field(..., description=f"Required identifier for the {tool_name_literal} tool."),
    )

    model = create_model(
        model_name,
        __base__=BaseIOSchema,
        __doc__=docstring or f"Dynamically generated Pydantic model for {model_name}",
        **fields,
    )
    return model


class MCPToolDefinition(NamedTuple):
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]


async def _fetch_tool_definitions_async(server_url: str, use_stdio: bool = False) -> List[MCPToolDefinition]:
    definitions = []
    stack = AsyncExitStack()
    try:
        if use_stdio:
            # Determine if it's a Python or JavaScript server
            is_python = server_url.endswith(".py")
            is_js = server_url.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")

            command = "python" if is_python else "node"
            server_params = StdioServerParameters(command=command, args=[server_url], env=None)
            stdio_transport = await stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport
        else:
            sse_transport = await stack.enter_async_context(sse_client(f"{server_url}/sse"))
            read_stream, write_stream = sse_transport

        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
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
            logger.warning(f"No tool definitions found on MCP server at {server_url}")
            return []
        logger.info(f"Successfully retrieved {len(definitions)} tool definitions from {server_url}")
    except ConnectionError as e:
        logger.error(f"Error fetching MCP tool definitions from {server_url}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching MCP tool definitions: {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error during tool definition fetching: {e}") from e
    finally:
        await stack.aclose()
    return definitions


def fetch_mcp_tools(server_url: str, use_stdio: bool = False) -> List[Type[BaseTool]]:
    """
    Connects to an MCP server via SSE or STDIO, discovers tool definitions, and dynamically generates
    synchronous Atomic Agents compatible BaseTool subclasses for each tool.
    Each generated tool will establish its own connection when its `run` method is called.

    Args:
        server_url: URL of the MCP server (for SSE) or path to the server script (for STDIO)
        use_stdio: If True, use STDIO transport instead of SSE
    """
    generated_tools = []
    tool_definitions: List[MCPToolDefinition] = []
    try:
        tool_definitions = asyncio.run(_fetch_tool_definitions_async(server_url, use_stdio))
        if not tool_definitions:
            logger.warning(f"No tool definitions found on MCP server at {server_url}")
            return []
        logger.info(f"Successfully retrieved {len(tool_definitions)} tool definitions from {server_url}")
    except ConnectionError as e:
        logger.error(f"Error fetching MCP tool definitions from {server_url}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching MCP tool definitions: {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error during tool definition fetching: {e}") from e
    for definition in tool_definitions:
        try:
            tool_name = definition.name
            tool_description = definition.description or f"Dynamically generated tool for MCP tool: {tool_name}"
            input_schema_dict = definition.input_schema
            InputSchema = json_schema_to_pydantic_model(
                input_schema_dict,
                f"{tool_name}InputSchema",
                tool_name,
                f"Input schema for {tool_name}",
            )
            OutputSchema = type(
                f"{tool_name}OutputSchema", (MCPToolOutputSchema,), {"__doc__": f"Output schema for {tool_name}"}
            )

            def run_tool_sync(self, params: InputSchema) -> OutputSchema:
                bound_tool_name = self.mcp_tool_name
                bound_server_url = self.server_url
                bound_use_stdio = self.use_stdio
                arguments = params.model_dump(exclude_none=True)

                async def _connect_and_call():
                    stack = AsyncExitStack()
                    try:
                        if bound_use_stdio:
                            is_python = bound_server_url.endswith(".py")
                            is_js = bound_server_url.endswith(".js")
                            if not (is_python or is_js):
                                raise ValueError("Server script must be a .py or .js file")

                            command = "python" if is_python else "node"
                            server_params = StdioServerParameters(command=command, args=[bound_server_url], env=None)
                            stdio_transport = await stack.enter_async_context(stdio_client(server_params))
                            read_stream, write_stream = stdio_transport
                        else:
                            sse_transport = await stack.enter_async_context(sse_client(f"{bound_server_url}/sse"))
                            read_stream, write_stream = sse_transport

                        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
                        await session.initialize()
                        tool_result = await session.call_tool(name=bound_tool_name, arguments=arguments)
                        return tool_result
                    finally:
                        await stack.aclose()

                try:
                    tool_result = asyncio.run(_connect_and_call())
                    return OutputSchema(result=tool_result)
                except Exception as e:
                    logger.error(f"Error executing MCP tool '{bound_tool_name}' via connect-per-call: {e}", exc_info=True)
                    raise RuntimeError(f"Failed to execute MCP tool '{bound_tool_name}': {e}") from e

            tool_class = type(
                tool_name,
                (BaseTool,),
                {
                    "input_schema": InputSchema,
                    "output_schema": OutputSchema,
                    "run": run_tool_sync,
                    "__doc__": tool_description,
                    "mcp_tool_name": tool_name,
                    "server_url": server_url,
                    "use_stdio": use_stdio,
                },
            )
            generated_tools.append(tool_class)
        except Exception as e:
            logger.error(f"Error generating class for tool '{definition.name}': {e}", exc_info=True)
            continue
    return generated_tools


def create_mcp_orchestrator_schema(tools: List[Type[BaseTool]]) -> Type[BaseIOSchema]:
    """
    Creates a schema for the MCP Orchestrator's output using the Union of all tool input schemas.

    Args:
        tools: List of dynamically generated MCP tool classes

    Returns:
        A Pydantic model class to be used as the output schema for an orchestrator agent
    """
    if not tools:
        logger.warning("No tools provided to create orchestrator schema")
        return None

    tool_schemas = [ToolClass.input_schema for ToolClass in tools]
    tool_names = [ToolClass.mcp_tool_name for ToolClass in tools]

    # Create a Union of all tool input schemas
    ToolParameterUnion = Union[tuple(tool_schemas)]

    # Dynamically create the output schema
    orchestrator_schema = create_model(
        "MCPOrchestratorOutputSchema",
        __doc__="Output schema for the MCP Orchestrator Agent. Contains the selected tool name and its parameters.",
        __base__=BaseIOSchema,
        tool_name=(str, Field(..., description=f"The name of the selected MCP tool. Must be one of: {tool_names}")),
        tool_parameters=(
            ToolParameterUnion,
            Field(..., description="The parameters for the selected tool, matching its specific schema."),
        ),
    )

    return orchestrator_schema


def fetch_mcp_tools_with_schema(server_url: str, use_stdio: bool = False) -> Tuple[List[Type[BaseTool]], Type[BaseIOSchema]]:
    """
    Fetches MCP tools and creates an orchestrator schema for them. Returns both as a tuple.

    Args:
        server_url: URL of the MCP server (for SSE) or path to the server script (for STDIO)
        use_stdio: If True, use STDIO transport instead of SSE

    Returns:
        A tuple containing:
        - List of dynamically generated tool classes
        - Orchestrator output schema with Union of tool input schemas
    """
    tools = fetch_mcp_tools(server_url, use_stdio)
    if not tools:
        return [], None

    orchestrator_schema = create_mcp_orchestrator_schema(tools)
    return tools, orchestrator_schema


if __name__ == "__main__":
    # Example usage with both SSE and STDIO
    MCP_SERVER_URL = "http://localhost:6969"
    # MCP_STDIO_SERVER_PATH = "atomic-examples/mcp-agent/example-mcp-server/example_mcp_server/server_stdio.py"

    # Moved function definition inside the main block
    def generate_input_for_tool(tool_name: str, input_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate appropriate input based on the tool name and input schema dictionary.
        This function creates sensible inputs for different tool types based on name
        or falls back to generic generation based on the schema types.
        """
        result = {}
        properties = input_schema.get("properties", {})
        if tool_name == "AddNumbers":
            result = {"number1": random.randint(1, 100), "number2": random.randint(1, 100)}
        elif tool_name == "DateDifference":
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
            result = {}
        else:
            if properties:
                for prop_name, prop_schema in properties.items():
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
                            elif item_type == "boolean":
                                result[prop_name].append(random.choice([True, False]))
                    elif prop_type == "object":
                        result[prop_name] = {}
        return result

    # Fetch MCP tools via SSE
    dynamic_tools_sse, orchestrator_schema_sse = fetch_mcp_tools_with_schema(MCP_SERVER_URL)

    # Fetch MCP tools via STDIO
    # dynamic_tools_stdio, orchestrator_schema_stdio = fetch_mcp_tools_with_schema(MCP_STDIO_SERVER_PATH, use_stdio=True)

    # Test individual tools from both transports
    print("\n=== Testing SSE Tools ===")
    for ToolClass in dynamic_tools_sse:
        tool = ToolClass()
        tool_name = tool.mcp_tool_name
        input_schema_dict = tool.input_schema.model_json_schema()
        input_args = generate_input_for_tool(tool_name, input_schema_dict)
        input_data = tool.input_schema(**input_args) if input_args else tool.input_schema()
        print(f"\n--- {tool_name} ---")
        print("Input:", input_data.model_dump())
        output = tool.run(input_data)
        print("Output:", output.result)

    # print("\n=== Testing STDIO Tools ===")
    # for ToolClass in dynamic_tools_stdio:
    #     tool = ToolClass()
    #     tool_name = tool.mcp_tool_name
    #     input_schema_dict = tool.input_schema.model_json_schema()
    #     input_args = generate_input_for_tool(tool_name, input_schema_dict)
    #     input_data = tool.input_schema(**input_args) if input_args else tool.input_schema()
    #     print(f"\n--- {tool_name} ---")
    #     print("Input:", input_data.model_dump())
    #     output = tool.run(input_data)
    #     print("Output:", output.result)

    # Display orchestrator schema
    print("\n=== Orchestrator Schema ===")
    if orchestrator_schema_sse:
        print(f"Schema: {orchestrator_schema_sse.__name__}")
        print(f"Documentation: {orchestrator_schema_sse.__doc__}")
        print("Fields:")
        for field_name, field in orchestrator_schema_sse.model_fields.items():
            print(f"  - {field_name}: {field.annotation}")
    else:
        print("No orchestrator schema generated (no tools found)")

    # if orchestrator_schema_stdio:
    #     print(f"Schema: {orchestrator_schema_stdio.__name__}")
    #     print(f"Documentation: {orchestrator_schema_stdio.__doc__}")
    #     print("Fields:")
    #     for field_name, field in orchestrator_schema_stdio.model_fields.items():
    #         print(f"  - {field_name}: {field.annotation}")
    # else:
    #     print("No orchestrator schema generated (no tools found)")
