"""FastAPI client example demonstrating async MCP tool usage."""

import os
from typing import Dict, Any, Union, Type
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from atomic_agents.connectors.mcp import fetch_mcp_tools_async, MCPTransportType
from atomic_agents.context import ChatHistory, SystemPromptGenerator
from atomic_agents import BaseIOSchema, AtomicAgent, AgentConfig
import openai
import instructor


@dataclass
class MCPConfig:
    """Configuration for the MCP Agent system using HTTP Stream transport."""

    mcp_server_url: str = "http://localhost:6969"
    openai_model: str = "gpt-4o"
    openai_api_key: str = os.getenv("OPENAI_API_KEY") or ""

    def __post_init__(self):
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")


class NaturalLanguageRequest(BaseModel):
    query: str = Field(..., description="Natural language query for mathematical operations")


class CalculationResponse(BaseModel):
    result: Any
    tools_used: list[str]
    query: str


class MCPOrchestratorInputSchema(BaseIOSchema):
    """Input schema for the MCP orchestrator that processes user queries."""

    query: str = Field(...)


class FinalResponseSchema(BaseIOSchema):
    """Schema for the final response to the user."""

    response_text: str = Field(...)


# Global storage for MCP tools, schema mapping
mcp_tools = {}
tool_schema_map: Dict[Type[BaseIOSchema], Type] = {}
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP tools and orchestrator agent on startup."""
    global config

    config = MCPConfig()

    mcp_endpoint = config.mcp_server_url

    try:
        print(f"Attempting to connect to MCP server at {mcp_endpoint}")
        print(f"Using transport type: {MCPTransportType.HTTP_STREAM}")

        import requests

        try:
            response = requests.get(f"{mcp_endpoint}/health", timeout=5)
            print(f"Health check response: {response.status_code}")
        except Exception as health_error:
            print(f"Health check failed: {health_error}")

        tools = await fetch_mcp_tools_async(mcp_endpoint=mcp_endpoint, transport_type=MCPTransportType.HTTP_STREAM)

        print(f"fetch_mcp_tools returned {len(tools)} tools")
        print(f"Tools type: {type(tools)}")

        for i, tool in enumerate(tools):
            tool_name = getattr(tool, "mcp_tool_name", tool.__name__)
            mcp_tools[tool_name] = tool
            print(f"Tool {i}: name='{tool_name}', type={type(tool).__name__}")

        print(f"Initialized {len(mcp_tools)} MCP tools: {list(mcp_tools.keys())}")

        tool_schema_map.update(
            {ToolClass.input_schema: ToolClass for ToolClass in tools if hasattr(ToolClass, "input_schema")}
        )

        available_schemas = tuple(tool_schema_map.keys()) + (FinalResponseSchema,)

        client = instructor.from_openai(openai.OpenAI(api_key=config.openai_api_key))
        history = ChatHistory()

        globals()["client"] = client
        globals()["history"] = history
        globals()["available_schemas"] = available_schemas

        print("MCP tools, schema mapping, and agent components initialized successfully")

    except Exception as e:
        print(f"Failed to initialize MCP tools: {e}")
        print(f"Exception type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        print("\n" + "=" * 60)
        print("ERROR: Could not connect to MCP server!")
        print("Please start the MCP server first:")
        print("  cd /path/to/example-mcp-server")
        print("  poetry run python -m example_mcp_server.server --mode=http_stream")
        print("=" * 60)
        raise RuntimeError(f"MCP server connection failed: {e}") from e

    yield

    mcp_tools.clear()
    tool_schema_map.clear()


app = FastAPI(
    title="MCP FastAPI Client Example",
    description="Demonstrates async MCP tool usage in FastAPI handlers with agent-based architecture",
    lifespan=lifespan,
)


async def execute_with_orchestrator_async(query: str) -> tuple[str, list[str]]:
    """Execute using orchestrator agent pattern with async execution."""
    if not config or not tool_schema_map:
        raise HTTPException(status_code=503, detail="Agent components not initialized")

    tools_used = []

    try:
        available_schemas = tuple(tool_schema_map.keys()) + (FinalResponseSchema,)
        ActionUnion = Union[available_schemas]

        class OrchestratorOutputSchema(BaseIOSchema):
            """Output schema for the MCP orchestrator containing reasoning and selected action."""

            reasoning: str
            action: ActionUnion

        orchestrator_agent = AtomicAgent[MCPOrchestratorInputSchema, OrchestratorOutputSchema](
            AgentConfig(
                client=globals()["client"],
                model=config.openai_model,
                history=ChatHistory(),
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

        orchestrator_output = orchestrator_agent.run(MCPOrchestratorInputSchema(query=query))

        print(f"Debug - orchestrator_output type: {type(orchestrator_output)}, fields: {orchestrator_output.model_dump()}")

        if hasattr(orchestrator_output, "chat_message") and not hasattr(orchestrator_output, "action"):
            action_instance = FinalResponseSchema(response_text=orchestrator_output.chat_message)
            reasoning = "Response generated directly from chat model"
        elif hasattr(orchestrator_output, "action"):
            action_instance = orchestrator_output.action
            reasoning = orchestrator_output.reasoning if hasattr(orchestrator_output, "reasoning") else "No reasoning provided"
        else:
            return "I encountered an unexpected response format. Unable to process.", tools_used

        print(f"Debug - Orchestrator reasoning: {reasoning}")
        print(f"Debug - Action instance type: {type(action_instance)}")
        print(f"Debug - Action instance: {action_instance}")

        iteration_count = 0
        max_iterations = 5

        while not isinstance(action_instance, FinalResponseSchema) and iteration_count < max_iterations:
            iteration_count += 1
            print(f"Debug - Iteration {iteration_count}, processing action type: {type(action_instance)}")

            tool_class = tool_schema_map.get(type(action_instance))
            if not tool_class:
                print(f"Debug - Error: No tool found for schema {type(action_instance)}")
                print(f"Debug - Available schemas: {list(tool_schema_map.keys())}")
                return "I encountered an internal error. Could not find the appropriate tool.", tools_used

            tool_name = tool_class.mcp_tool_name
            tools_used.append(tool_name)

            print(f"Debug - Executing {tool_class.mcp_tool_name}...")
            print(f"Debug - Parameters: {action_instance.model_dump()}")
            tool_instance = tool_class()
            try:
                result = await tool_instance.arun(action_instance)
                print(f"Debug - Result: {result.result}")

                next_query = f"Based on the tool result: {result.result}, please provide the final response to the user's original query: {query}"
                next_output = orchestrator_agent.run(MCPOrchestratorInputSchema(query=next_query))

                print(f"Debug - subsequent orchestrator_output type: {type(next_output)}, fields: {next_output.model_dump()}")

                if hasattr(next_output, "action"):
                    action_instance = next_output.action
                    if hasattr(next_output, "reasoning"):
                        print(f"Debug - Orchestrator reasoning: {next_output.reasoning}")
                else:
                    action_instance = FinalResponseSchema(response_text=next_output.chat_message)

            except Exception as e:
                print(f"Debug - Error executing tool: {e}")
                return f"I encountered an error while executing the tool: {str(e)}", tools_used

        if iteration_count >= max_iterations:
            print(f"Debug - Hit max iterations ({max_iterations}), forcing final response")
            action_instance = FinalResponseSchema(
                response_text="I reached the maximum number of processing steps. Please try rephrasing your query."
            )

        if isinstance(action_instance, FinalResponseSchema):
            return action_instance.response_text, tools_used
        else:
            return "Error: Expected final response but got something else", tools_used

    except Exception as e:
        print(f"Debug - Orchestrator execution error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Orchestrator execution failed: {e}")


@app.get("/")
async def root():
    """Root endpoint showing available tools and following the schema structure."""
    return {
        "message": "MCP FastAPI Client Example - Agent-based Architecture",
        "available_tools": list(mcp_tools.keys()),
        "tool_schemas": {
            name: tool.input_schema.__name__ if hasattr(tool, "input_schema") else "N/A" for name, tool in mcp_tools.items()
        },
        "endpoints": {
            "calculate": "/calculate - Natural language queries using agent orchestration (e.g., 'multiply 15 by 3')"
        },
        "example_usage": {
            "natural_language": {
                "endpoint": "/calculate",
                "body": {"query": "What is 25 divided by 5?"},
                "description": "Agent will determine the appropriate tool",
            }
        },
        "config": {
            "mcp_server_url": config.mcp_server_url if config else "Not initialized",
            "model": config.openai_model if config else "Not initialized",
        },
    }


@app.post("/calculate", response_model=CalculationResponse)
async def calculate_with_agent(request: NaturalLanguageRequest):
    """Calculate using agent-based orchestration with natural language input."""
    try:
        result_text, tools_used = await execute_with_orchestrator_async(request.query)
        return CalculationResponse(result=result_text, tools_used=tools_used, query=request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent calculation failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
