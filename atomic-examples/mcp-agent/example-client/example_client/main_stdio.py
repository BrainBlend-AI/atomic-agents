# pyright: reportInvalidTypeForm=false
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools
from rich.console import Console
from rich.table import Table
import openai
import os
import instructor
import asyncio
import shlex
from contextlib import AsyncExitStack
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from typing import Union, Type, Dict, Optional
from dataclasses import dataclass
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# 1. Configuration and environment setup
@dataclass
class MCPConfig:
    """Configuration for the MCP Agent system using STDIO transport."""

    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    # Command to run the STDIO server.
    # In practice, this could be something like "pipx some-other-persons-server or npx some-other-persons-server
    # if working with a server you did not write yourself.
    mcp_stdio_server_command: str = "poetry run example-mcp-server --mode stdio"

    def __post_init__(self):
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")


config = MCPConfig()
console = Console()
client = instructor.from_openai(openai.OpenAI(api_key=config.openai_api_key))


class FinalResponseSchema(BaseIOSchema):
    """Schema for providing a final text response to the user."""

    response_text: str = Field(..., description="The final text response to the user's query")


# --- Bootstrap persistent STDIO session ---
stdio_session: Optional[ClientSession] = None
stdio_loop: Optional[asyncio.AbstractEventLoop] = None
stdio_exit_stack: Optional[AsyncExitStack] = None

# Initialize STDIO session
stdio_loop = asyncio.new_event_loop()


async def _bootstrap_stdio():
    global stdio_exit_stack  # Allow modification of the global variable
    stdio_exit_stack = AsyncExitStack()
    command_parts = shlex.split(config.mcp_stdio_server_command)
    server_params = StdioServerParameters(command=command_parts[0], args=command_parts[1:], env=None)
    read_stream, write_stream = await stdio_exit_stack.enter_async_context(stdio_client(server_params))
    session = await stdio_exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    return session


stdio_session = stdio_loop.run_until_complete(_bootstrap_stdio())
# The stdio_exit_stack is kept to clean up later

# Fetch tools and build ActionUnion statically
tools = fetch_mcp_tools(
    mcp_endpoint=None,
    use_stdio=True,
    client_session=stdio_session,  # Pass persistent session
    event_loop=stdio_loop,  # Pass corresponding loop
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


# 3. Main logic and script entry point
def main():
    global stdio_session, stdio_loop, stdio_exit_stack  # Ensure access if cleanup is needed
    try:
        console.print("[bold green]Initializing MCP Agent System (STDIO mode)...[/bold green]")
        # Display available tools
        table = Table(title="Available MCP Tools", box=None)
        table.add_column("Tool Name", style="cyan")
        table.add_column("Input Schema", style="yellow")
        table.add_column("Description", style="magenta")
        for ToolClass in tools:
            schema_name = ToolClass.input_schema.__name__ if hasattr(ToolClass, "input_schema") else "N/A"
            table.add_row(ToolClass.mcp_tool_name, schema_name, ToolClass.__doc__ or "")
        console.print(table)
        # Create and initialize orchestrator agent
        console.print("[dim]• Creating orchestrator agent...[/dim]")
        memory = AgentMemory()
        orchestrator_agent = BaseAgent(
            BaseAgentConfig(
                client=client,
                model=config.openai_model,
                memory=memory,
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "You are an MCP Orchestrator Agent, designed to intelligently route user queries to appropriate tools or provide direct responses.",
                        "Your primary responsibility is to analyze user queries and determine the most effective way to handle them using the available tools.",
                        "You have access to a variety of specialized tools, each with specific capabilities and input requirements.",
                    ],
                    steps=[
                        "1. Carefully analyze the user's query to understand their intent and requirements.",
                        "2. Evaluate whether the query can be handled by an available tool or requires a direct response.",
                        "3. If using a tool: Extract and validate all necessary parameters from the query.",
                        "4. If providing a direct response: Formulate a clear, helpful response that addresses the query.",
                    ],
                    output_instructions=[
                        "Always provide a detailed explanation of your decision-making process in the 'reasoning' field.",
                        "Choose exactly one action schema that best matches the user's needs.",
                        "Ensure all required parameters are properly extracted and validated.",
                        "Maintain a professional and helpful tone in all responses.",
                        "If applicable, it is important to break down the user's query into smaller, more manageable tasks and route them to the appropriate tool before responding with a final response.",
                    ],
                ),
                input_schema=MCPOrchestratorInputSchema,
                output_schema=OrchestratorOutputSchema,
            )
        )
        console.print("[green]Successfully created orchestrator agent.[/green]")
        # Interactive chat loop
        console.print("[bold green]MCP Agent Interactive Chat (STDIO mode). Type 'exit' or 'quit' to leave.[/bold green]")
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
                action_instance = orchestrator_output.action
                reasoning = orchestrator_output.reasoning
                console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")

                # Keep executing until we get a final response
                while not isinstance(action_instance, FinalResponseSchema):
                    schema_type = type(action_instance)
                    ToolClass = tool_schema_to_class_map.get(schema_type)
                    if not ToolClass:
                        raise ValueError(f"Unknown schema type '{schema_type.__name__}' returned by orchestrator")

                    tool_name = ToolClass.mcp_tool_name
                    console.print(f"[blue]Executing tool:[/blue] {tool_name}")
                    console.print(f"[dim]Parameters:[/dim] {action_instance.model_dump()}")

                    tool_instance = ToolClass()
                    # The persistent session/loop are already part of the ToolClass definition
                    tool_output = tool_instance.run(action_instance)
                    console.print(f"[bold green]Result:[/bold green] {tool_output.result}")

                    # Add tool result to agent memory
                    result_message = MCPOrchestratorInputSchema(
                        query=f"Tool {tool_name} executed with result: {tool_output.result}"
                    )
                    orchestrator_agent.memory.add_message("system", result_message)

                    # Run the agent again without parameters to continue the flow
                    orchestrator_output = orchestrator_agent.run()
                    action_instance = orchestrator_output.action
                    reasoning = orchestrator_output.reasoning
                    console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")

                # Final response from the agent
                console.print(f"[bold blue]Agent:[/bold blue] {action_instance.response_text}")

            except Exception as e:
                console.print(f"[red]Error processing query:[/red] {str(e)}")
                console.print_exception()
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {str(e)}")
        console.print_exception()
        return
    finally:
        # Cleanup persistent STDIO resources
        if stdio_loop and stdio_exit_stack:
            console.print("\n[dim]Cleaning up STDIO resources...[/dim]")
            try:
                stdio_loop.run_until_complete(stdio_exit_stack.aclose())
            except Exception as cleanup_err:
                console.print(f"[red]Error during STDIO cleanup:[/red] {cleanup_err}")
            finally:
                stdio_loop.close()


if __name__ == "__main__":
    main()
