"""
HTTP Stream transport client for MCP Agent example.
Communicates with the server_http.py `/mcp` endpoint using HTTP GET/POST/DELETE for JSON-RPC streams.
"""
import sys
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
import openai, os, instructor
from typing import Union, Type, Dict
from dataclasses import dataclass
import re


@dataclass
class MCPConfig:
    """Configuration for the MCP Agent system using HTTP Stream transport."""
    mcp_server_url: str = "http://localhost:6969"
    openai_model: str = "gpt-4o"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    def __post_init__(self):
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")


def main():
    # Use default HTTP transport settings from MCPConfig
    config = MCPConfig()
    console = Console()
    client = instructor.from_openai(openai.OpenAI(api_key=config.openai_api_key))

    console.print("[bold green]Initializing MCP Agent System (HTTP Stream mode)...[/bold green]")
    tools = fetch_mcp_tools(mcp_endpoint=config.mcp_server_url, use_stdio=False, use_http_stream=True)
    if not tools:
        console.print(f"[bold red]No MCP tools found at {config.mcp_server_url}[/bold red]")
        sys.exit(1)

    # Display available tools
    table = Table(title="Available MCP Tools", box=None)
    table.add_column("Tool Name", style="cyan")
    table.add_column("Input Schema", style="yellow")
    table.add_column("Description", style="magenta")
    for ToolClass in tools:
        schema_name = getattr(ToolClass.input_schema, '__name__', 'N/A')
        table.add_row(ToolClass.mcp_tool_name, schema_name, ToolClass.__doc__ or "")
    console.print(table)

    # Build orchestrator
    class MCPOrchestratorInputSchema(BaseIOSchema):
        """Input schema for the MCP orchestrator that processes user queries."""
        query: str = Field(...)

    class FinalResponseSchema(BaseIOSchema):
        """Schema for the final response to the user."""
        response_text: str = Field(...)

    # Map schemas and define ActionUnion
    tool_schema_map: Dict[Type[BaseIOSchema], Type] = {
        ToolClass.input_schema: ToolClass for ToolClass in tools if hasattr(ToolClass, 'input_schema')
    }
    available_schemas = tuple(tool_schema_map.keys()) + (FinalResponseSchema,)
    ActionUnion = Union[available_schemas]

    class OrchestratorOutputSchema(BaseIOSchema):
        """Output schema for the MCP orchestrator containing reasoning and selected action."""
        reasoning: str
        action: ActionUnion

    history = ChatHistory()
    orchestrator = BaseAgent[
        MCPOrchestratorInputSchema, OrchestratorOutputSchema
    ](
        BaseAgentConfig(
            client=client,
            model=config.openai_model,
            history=history,
            system_prompt_generator=SystemPromptGenerator(
                background=['You are an MCP orchestrator via HTTP.'],
                steps=['Decide and invoke tools over HTTP stream.'],
                output_instructions=['Provide reasoning and a single action schema.'],
            ),
        )
    )

    console.print("[bold green]HTTP Stream client ready. Type 'exit' to quit.[/bold green]")
    while True:
        query = console.input("[bold yellow]You:[/bold yellow] ").strip()
        if query.lower() in {'exit', 'quit'}:
            break
        if not query:
            continue
        
        try:
            # Initial run with user query
            orchestrator_output = orchestrator.run(MCPOrchestratorInputSchema(query=query))
            
            # Handle the output similar to SSE version
            if hasattr(orchestrator_output, "chat_message") and not hasattr(orchestrator_output, "action"):
                # Convert BaseAgentOutputSchema to FinalResponseSchema
                action_instance = FinalResponseSchema(response_text=orchestrator_output.chat_message)
                reasoning = "Response generated directly from chat model"
            elif hasattr(orchestrator_output, "action"):
                action_instance = orchestrator_output.action
                reasoning = orchestrator_output.reasoning if hasattr(orchestrator_output, "reasoning") else "No reasoning provided"
            else:
                console.print("[yellow]Warning: Unexpected response format. Unable to process.[/yellow]")
                continue
                
            console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")
            
            # Keep executing until we get a final response
            while not isinstance(action_instance, FinalResponseSchema):
                # Find the matching tool class
                tool_class = tool_schema_map.get(type(action_instance))
                if not tool_class:
                    console.print(f"[red]Error: No tool found for schema {type(action_instance)}[/red]")
                    action_instance = FinalResponseSchema(response_text="I encountered an internal error. Could not find the appropriate tool.")
                    break
                
                # Execute the tool
                console.print(f"[blue]Executing {tool_class.mcp_tool_name}...[/blue]")
                tool_instance = tool_class()
                try:
                    result = tool_instance.run(action_instance)
                    console.print(f"[green]Tool result:[/green] {result}")
                    
                    # Ask orchestrator what to do next with the result
                    next_query = f"Based on the tool result: {result}, please provide the final response to the user's original query: {query}"
                    next_output = orchestrator.run(MCPOrchestratorInputSchema(query=next_query))
                    
                    if hasattr(next_output, "action"):
                        action_instance = next_output.action
                    else:
                        # If no action, treat as final response
                        action_instance = FinalResponseSchema(response_text=next_output.chat_message)
                        
                except Exception as e:
                    console.print(f"[red]Error executing tool: {e}[/red]")
                    action_instance = FinalResponseSchema(response_text=f"I encountered an error while executing the tool: {str(e)}")
                    break
            
            # Display final response
            if isinstance(action_instance, FinalResponseSchema):
                console.print(f"[bold green]Assistant:[/bold green] {action_instance.response_text}")
            else:
                console.print("[red]Error: Expected final response but got something else[/red]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    main()
