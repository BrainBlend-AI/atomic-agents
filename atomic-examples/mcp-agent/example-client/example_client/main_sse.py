# pyright: reportInvalidTypeForm=false
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
import openai
import os
import instructor
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from typing import Union, Type, Dict
from dataclasses import dataclass
import re


# 1. Configuration and environment setup
@dataclass
class MCPConfig:
    """Configuration for the MCP Agent system using SSE transport."""

    mcp_server_url: str = "http://localhost:6969"

    # NOTE: In contrast to other examples, we use gpt-4o and not gpt-4o-mini here.
    # In my tests, gpt-4o-mini was not smart enough to deal with multiple tools like that
    # and at the moment MCP does not yet allow for adding sufficient metadata to
    # clarify tools even more and introduce more constraints.
    openai_model: str = "gpt-4o"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    def __post_init__(self):
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")


config = MCPConfig()
console = Console()
client = instructor.from_openai(openai.OpenAI(api_key=config.openai_api_key))


class FinalResponseSchema(BaseIOSchema):
    """Schema for providing a final text response to the user."""

    response_text: str = Field(..., description="The final text response to the user's query")


# Fetch tools and build ActionUnion statically
tools = fetch_mcp_tools(
    mcp_endpoint=config.mcp_server_url,
    use_stdio=False,
)
if not tools:
    raise RuntimeError("No MCP tools found. Please ensure the MCP server is running and accessible.")

# Build mapping from input_schema to ToolClass
tool_schema_to_class_map: Dict[Type[BaseIOSchema], Type[BaseAgent]] = {
    ToolClass.input_schema: ToolClass for ToolClass in tools if hasattr(ToolClass, "input_schema")
}
# Collect all tool input schemas
tool_input_schemas = tuple(tool_schema_to_class_map.keys())

# Available schemas include all tool input schemas and the final response schema
available_schemas = tool_input_schemas + (FinalResponseSchema,)

# Define the Union of all action schemas
ActionUnion = Union[available_schemas]


# 2. Schema and class definitions
class MCPOrchestratorInputSchema(BaseIOSchema):
    """Input schema for the MCP Orchestrator Agent."""

    query: str = Field(..., description="The user's query to analyze.")


class OrchestratorOutputSchema(BaseIOSchema):
    """Output schema for the orchestrator. Contains reasoning and the chosen action."""

    reasoning: str = Field(
        ..., description="Detailed explanation of why this action was chosen and how it will address the user's query."
    )
    action: ActionUnion = Field(  # type: ignore[reportInvalidTypeForm]
        ..., description="The chosen action: either a tool's input schema instance or a final response schema instance."
    )

    model_config = {"arbitrary_types_allowed": True}


# Helper function to format mathematical expressions for better terminal readability
def format_math_expressions(text):
    """
    Format LaTeX-style math expressions for better readability in the terminal.

    Args:
        text (str): Text containing LaTeX-style math expressions

    Returns:
        str: Text with formatted math expressions
    """
    # Replace \( and \) with formatted brackets
    text = re.sub(r"\\[\(\)]", "", text)

    # Replace LaTeX multiplication symbol with a plain x
    text = text.replace("\\times", "×")

    # Format other common LaTeX symbols
    text = text.replace("\\cdot", "·")
    text = text.replace("\\div", "÷")
    text = text.replace("\\sqrt", "√")
    text = text.replace("\\pi", "π")

    return text


# 3. Main logic and script entry point
def main():
    try:
        console.print("[bold green]Initializing MCP Agent System (SSE mode)...[/bold green]")
        # Display available tools
        table = Table(title="Available MCP Tools", box=None)
        table.add_column("Tool Name", style="cyan")
        table.add_column("Input Schema", style="yellow")
        table.add_column("Description", style="magenta")
        for ToolClass in tools:
            # Fix to handle when input_schema is a property or doesn't have __name__
            if hasattr(ToolClass, "input_schema"):
                if hasattr(ToolClass.input_schema, "__name__"):
                    schema_name = ToolClass.input_schema.__name__
                else:
                    # If it's a property, try to get the type name of the actual class
                    try:
                        schema_instance = ToolClass.input_schema
                        schema_name = schema_instance.__class__.__name__
                    except Exception:
                        schema_name = "Unknown Schema"
            else:
                schema_name = "N/A"
            table.add_row(ToolClass.mcp_tool_name, schema_name, ToolClass.__doc__ or "")
        console.print(table)
        # Create and initialize orchestrator agent
        console.print("[dim]• Creating orchestrator agent...[/dim]")
        memory = AgentMemory()
        orchestrator_agent = BaseAgent[MCPOrchestratorInputSchema, OrchestratorOutputSchema](
            BaseAgentConfig(
                client=client,
                model=config.openai_model,
                memory=memory,
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "You are an MCP Orchestrator Agent, designed to chat with users and",
                        "determine the best way to handle their queries using the available tools.",
                    ],
                    steps=[
                        "1. Use the reasoning field to determine if one or more successive tool calls could be used to handle the user's query.",
                        "2. If so, choose the appropriate tool(s) one at a time and extract all necessary parameters from the query.",
                        "3. If a single tool can not be used to handle the user's query, think about how to break down the query into "
                        "smaller tasks and route them to the appropriate tool(s).",
                        "4. If no sequence of tools could be used, or if you are finished processing the user's query, provide a final "
                        "response to the user.",
                    ],
                    output_instructions=[
                        "1. Always provide a detailed explanation of your decision-making process in the 'reasoning' field.",
                        "2. Choose exactly one action schema (either a tool input or FinalResponseSchema).",
                        "3. Ensure all required parameters for the chosen tool are properly extracted and validated.",
                        "4. Maintain a professional and helpful tone in all responses.",
                        "5. Break down complex queries into sequential tool calls before giving the final answer via `FinalResponseSchema`.",
                    ],
                ),
            )
        )
        console.print("[green]Successfully created orchestrator agent.[/green]")
        # Interactive chat loop
        console.print("[bold green]MCP Agent Interactive Chat (SSE mode). Type 'exit' or 'quit' to leave.[/bold green]")
        while True:
            query = console.input("[bold yellow]You:[/bold yellow] ").strip()
            if query.lower() in {"exit", "quit"}:
                console.print("[bold red]Exiting chat. Goodbye![/bold red]")
                break
            if not query:
                continue  # Ignore empty input
            try:
                # Initial run with user query
                orchestrator_output = orchestrator_agent.run(MCPOrchestratorInputSchema(query=query))

                # Debug output to see what's actually in the output
                console.print(
                    f"[dim]Debug - orchestrator_output type: {type(orchestrator_output)}, fields: {orchestrator_output.model_dump()}"
                )

                # The model is returning a BaseAgentOutputSchema instead of OrchestratorOutputSchema
                # We need to handle this case by creating a FinalResponseSchema directly
                if hasattr(orchestrator_output, "chat_message") and not hasattr(orchestrator_output, "action"):
                    console.print("[yellow]Note: Converting BaseAgentOutputSchema to FinalResponseSchema[/yellow]")
                    action_instance = FinalResponseSchema(response_text=orchestrator_output.chat_message)
                    reasoning = "Response generated directly from chat model"
                # Handle the original expected format if it exists
                elif hasattr(orchestrator_output, "action"):
                    action_instance = orchestrator_output.action
                    reasoning = (
                        orchestrator_output.reasoning if hasattr(orchestrator_output, "reasoning") else "No reasoning provided"
                    )
                else:
                    console.print("[yellow]Warning: Unexpected response format. Unable to process.[/yellow]")
                    continue

                console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")

                # Keep executing until we get a final response
                while not isinstance(action_instance, FinalResponseSchema):
                    # Handle the case where action_instance is a dictionary
                    if isinstance(action_instance, dict):
                        console.print(
                            "[yellow]Warning: Received dictionary instead of schema object. Attempting to convert...[/yellow]"
                        )
                        console.print(f"[dim]Dictionary contents: {action_instance}[/dim]")

                        # Special handling for function-call format {"recipient_name": "functions.toolname", "parameters": {...}}
                        if "recipient_name" in action_instance and "parameters" in action_instance:
                            console.print("[yellow]Detected function call format with recipient_name and parameters[/yellow]")
                            recipient = action_instance.get("recipient_name", "")
                            parameters = action_instance.get("parameters", {})

                            # Extract tool name from recipient (format might be "functions.toolname")
                            tool_parts = recipient.split(".")
                            if len(tool_parts) > 1:
                                tool_name = tool_parts[-1]  # Take last part after the dot
                                console.print(
                                    f"[yellow]Extracted tool name '{tool_name}' from recipient '{recipient}'[/yellow]"
                                )

                                # Special case for calculator
                                if tool_name.lower() == "calculate":
                                    tool_name = "Calculator"
                                    console.print("[yellow]Mapped 'calculate' to 'Calculator' tool[/yellow]")

                                # Try to find a matching tool class by name
                                matching_tool = next((t for t in tools if t.mcp_tool_name.lower() == tool_name.lower()), None)

                                if matching_tool:
                                    try:
                                        # Create an instance using the parameters
                                        action_instance = matching_tool.input_schema(**parameters)
                                        console.print(
                                            f"[green]Successfully created {matching_tool.input_schema.__name__} from function call format[/green]"
                                        )
                                        continue
                                    except Exception as e:
                                        console.print(f"[red]Error creating schema from function parameters: {e}[/red]")

                        # Try to find a tool_name in the dictionary (original approach)
                        tool_name = action_instance.get("tool_name")

                        # If tool_name is not found, try alternative approaches to identify the tool
                        if not tool_name:
                            # Approach 1: Look for a field that might contain a tool name
                            for key in action_instance.keys():
                                if "tool" in key.lower():
                                    tool_name = action_instance.get(key)
                                    if tool_name:
                                        console.print(
                                            f"[yellow]Found potential tool name '{tool_name}' in field '{key}'[/yellow]"
                                        )

                            # Approach 2: Try to match dictionary fields with tool schemas
                            if not tool_name:
                                console.print("[yellow]Trying to match dictionary fields with available tools...[/yellow]")
                                best_match = None
                                best_match_score = 0

                                for ToolClass in tools:
                                    if not hasattr(ToolClass, "input_schema"):
                                        continue

                                    # Try to create a sample instance to get field names
                                    try:
                                        schema_fields = set(
                                            ToolClass.input_schema.__annotations__.keys()
                                            if hasattr(ToolClass.input_schema, "__annotations__")
                                            else []
                                        )
                                        dict_fields = set(action_instance.keys())

                                        # Count matching fields
                                        matching_fields = len(schema_fields.intersection(dict_fields))
                                        if matching_fields > best_match_score and matching_fields > 0:
                                            best_match_score = matching_fields
                                            best_match = ToolClass
                                            console.print(
                                                f"[dim]Found {matching_fields} matching fields with {ToolClass.mcp_tool_name}[/dim]"
                                            )
                                    except Exception as e:
                                        console.print(
                                            f"[dim]Error checking {getattr(ToolClass, 'mcp_tool_name', 'unknown tool')}: {str(e)}[/dim]"
                                        )

                                if best_match:
                                    tool_name = best_match.mcp_tool_name
                                    console.print(
                                        f"[yellow]Best matching tool: {tool_name} with {best_match_score} matching fields[/yellow]"
                                    )

                        if not tool_name:
                            # Final fallback: Check if this might be a final response
                            if any(
                                key in action_instance for key in ["response_text", "text", "response", "message", "content"]
                            ):
                                response_content = \
                                    action_instance.get("response_text") or \
                                    action_instance.get("text") or \
                                    action_instance.get("response") or \
                                    action_instance.get("message") or \
                                    action_instance.get("content") or \
                                    "No message content found"
                                console.print("[yellow]Appears to be a final response. Converting directly.[/yellow]")
                                action_instance = FinalResponseSchema(response_text=response_content)
                                continue

                            console.print("[red]Error: Could not determine tool type from dictionary[/red]")
                            # Create a final response with an error message
                            action_instance = FinalResponseSchema(
                                response_text="I encountered an internal error. The tool could not be determined from the response. "
                                "Please try rephrasing your question."
                            )
                            break

                        # Try to find a matching tool class by name
                        matching_tool = next((t for t in tools if t.mcp_tool_name == tool_name), None)
                        if not matching_tool:
                            console.print(f"[red]Error: No tool found with name {tool_name}[/red]")
                            # Create a final response with an error message
                            action_instance = FinalResponseSchema(
                                response_text=f"I encountered an internal error. Could not find tool named '{tool_name}'."
                            )
                            break

                        # Create an instance of the input schema with the dictionary data
                        try:
                            # Remove tool_name if it's not a field in the schema
                            params = {}
                            has_annotations = hasattr(matching_tool.input_schema, "__annotations__")

                            for k, v in action_instance.items():
                                # Include the key-value pair if it's not "tool_name" or if it's a valid field in the schema
                                if k not in ["tool_name"] or (
                                    has_annotations and k in matching_tool.input_schema.__annotations__.keys()
                                ):
                                    params[k] = v

                            action_instance = matching_tool.input_schema(**params)
                            console.print(
                                f"[green]Successfully converted dictionary to {matching_tool.input_schema.__name__}[/green]"
                            )
                        except Exception as e:
                            console.print(f"[red]Error creating schema instance: {e}[/red]")
                            # Create a final response with an error message
                            action_instance = FinalResponseSchema(
                                response_text=f"I encountered an internal error when trying to use the {tool_name} tool: {str(e)}"
                            )
                            break

                    schema_type = type(action_instance)
                    ToolClass = tool_schema_to_class_map.get(schema_type)
                    if not ToolClass:
                        console.print(f"[red]Unknown schema type '{schema_type.__name__}' returned by orchestrator[/red]")
                        # Create a final response with an error message
                        action_instance = FinalResponseSchema(
                            response_text="I encountered an internal error. The tool type could not be recognized."
                        )
                        break

                    tool_name = ToolClass.mcp_tool_name
                    console.print(f"[blue]Executing tool:[/blue] {tool_name}")
                    console.print(f"[dim]Parameters: {action_instance.model_dump()}")

                    tool_instance = ToolClass()
                    tool_output = tool_instance.run(action_instance)
                    console.print(f"[bold green]Result:[/bold green] {tool_output.result}")

                    # Add tool result to agent memory
                    result_message = MCPOrchestratorInputSchema(
                        query=f"Tool {tool_name} executed with result: {tool_output.result}"
                    )
                    orchestrator_agent.memory.add_message("system", result_message)

                    # Run the agent again without parameters to continue the flow
                    orchestrator_output = orchestrator_agent.run()

                    # Debug output for subsequent responses
                    console.print(
                        f"[dim]Debug - subsequent orchestrator_output type: {type(orchestrator_output)}, fields: {orchestrator_output.model_dump()}"
                    )

                    # Handle different response formats
                    if hasattr(orchestrator_output, "chat_message") and not hasattr(orchestrator_output, "action"):
                        console.print("[yellow]Note: Converting BaseAgentOutputSchema to FinalResponseSchema[/yellow]")
                        action_instance = FinalResponseSchema(response_text=orchestrator_output.chat_message)
                        reasoning = "Response generated directly from chat model"
                    elif hasattr(orchestrator_output, "action"):
                        action_instance = orchestrator_output.action
                        reasoning = (
                            orchestrator_output.reasoning
                            if hasattr(orchestrator_output, "reasoning")
                            else "No reasoning provided"
                        )
                    else:
                        console.print("[yellow]Warning: Unexpected response format. Unable to process.[/yellow]")
                        break

                    console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")

                # Final response from the agent
                response_text = getattr(
                    action_instance, "response_text", getattr(action_instance, "chat_message", str(action_instance))
                )
                md = Markdown(response_text)
                # Render the response as markdown
                console.print("[bold blue]Agent: [/bold blue]")
                console.print(md)

            except Exception as e:
                console.print(f"[red]Error processing query:[/red] {str(e)}")
                console.print_exception()
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {str(e)}")
        console.print_exception()


if __name__ == "__main__":
    main()
