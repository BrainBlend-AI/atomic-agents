"""Service layer for managing tools."""
from typing import Dict, List, Any, Type, cast, Optional
import json
from mcp.server.fastmcp import FastMCP
from example_mcp_server.interfaces.tool import Tool, ToolResponse, BaseToolInput, ToolContent
from pydantic import Field


class ToolService:
    """Service for managing and executing tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def register_tools(self, tools: List[Tool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, tool_name: str) -> Tool:
        """Get a tool by name."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")
        return self._tools[tool_name]

    async def execute_tool(self, tool_name: str, input_data: Dict[str, Any]) -> ToolResponse:
        """Execute a tool by name with given arguments.

        Args:
            tool_name: The name of the tool to execute
            input_data: Dictionary of input arguments for the tool

        Returns:
            The tool's response containing the execution results

        Raises:
            ValueError: If the tool is not found
            ValidationError: If the input data is invalid
        """
        tool = self.get_tool(tool_name)

        # Convert input dictionary to the tool's input model
        input_model = tool.input_model(**input_data)

        # Execute the tool with validated input
        return await tool.execute(input_model)

    def _process_tool_content(self, content: ToolContent) -> Any:
        """Process a ToolContent object based on its type.

        Args:
            content: The ToolContent to process

        Returns:
            The appropriate representation of the content based on its type
        """
        if content.type == "text":
            return content.text
        elif content.type == "json" and content.json_data is not None:
            return content.json_data
        else:
            # Default to returning whatever is available
            return content.text or content.json_data or {}

    def _serialize_response(self, response: ToolResponse) -> Any:
        """Serialize a ToolResponse to return to the client.

        This handles the actual response serialization based on content types.

        Args:
            response: The ToolResponse to serialize

        Returns:
            The serialized response
        """
        if not response.content:
            return {}

        # If there's only one content item, return it directly
        if len(response.content) == 1:
            return self._process_tool_content(response.content[0])

        # If there are multiple content items, return them as a list
        return [self._process_tool_content(content) for content in response.content]

    def register_mcp_handlers(self, mcp: FastMCP) -> None:
        """Register all tools as MCP handlers."""
        for tool in self._tools.values():
            # Get the tool's schema
            schema = tool.input_model.model_json_schema()
            properties = schema.get("properties", {})

            # Create a function signature that matches the schema with parameter descriptions
            params = []

            for name, info in properties.items():
                type_hint = "str"  # Default to str
                if info.get("type") == "integer":
                    type_hint = "int"
                elif info.get("type") == "number":
                    type_hint = "float"
                elif info.get("type") == "boolean":
                    type_hint = "bool"

                default = info.get("default", "...")
                description = info.get("description", "")

                # Create parameter string for function definition with Field for descriptions
                if default == "...":
                    params.append(f"{name}: {type_hint} = Field(description='{description}')")
                else:
                    params.append(f"{name}: {type_hint} = Field(description='{description}', default={repr(default)})")

            # Create the function definition
            fn_def = f"async def {tool.name}({', '.join(params)}):\n"
            fn_def += f'    """{tool.description}"""\n'
            fn_def += "    result = await self.execute_tool(tool.name, locals())\n"
            fn_def += "    return self._serialize_response(result)"

            # Create the function
            namespace = {"self": self, "tool": tool, "Field": Field}
            exec(fn_def, namespace)
            handler = namespace[tool.name]

            # Register the handler
            mcp.tool(
                name=tool.name,
                description=tool.description
            )(handler)