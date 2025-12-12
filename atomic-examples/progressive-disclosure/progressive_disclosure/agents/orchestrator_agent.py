# pyright: reportInvalidTypeForm=false
"""Dynamic Orchestrator Factory for progressive disclosure.

This module provides a factory for creating orchestrator agents with
dynamically filtered tool sets. Instead of loading all available MCP tools,
the orchestrator is created with only the tools selected by the Tool Finder Agent.

This is the key component that achieves context window efficiency through
progressive disclosure.

Supports both sequential and parallel tool execution modes.
"""

from typing import List, Type, Dict, Union, Optional, Any, Callable
from pydantic import Field
import instructor
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator
from atomic_agents.base.base_tool import BaseTool
from atomic_agents.connectors.mcp import (
    fetch_mcp_tools,
    MCPTransportType,
)


########################
# INPUT/OUTPUT SCHEMAS #
########################
class OrchestratorInputSchema(BaseIOSchema):
    """Input schema for the orchestrator agent."""

    query: str = Field(
        ...,
        description="The user's query to process using the available tools.",
    )


class FinalResponseSchema(BaseIOSchema):
    """Schema for the final response to the user."""

    response_text: str = Field(
        ...,
        description="The final text response to the user's query.",
    )


class MCPToolOutputSchema(BaseIOSchema):
    """Generic output schema for MCP tool execution."""

    result: Any = Field(..., description="The result from the tool execution.")


#######################
# ORCHESTRATOR OUTPUT #
#######################
def create_orchestrator_output_schema(
    tool_schemas: tuple[Type[BaseIOSchema], ...],
    parallel: bool = False,
) -> Type[BaseIOSchema]:
    """Dynamically create an orchestrator output schema with the given tools.

    Args:
        tool_schemas: Tuple of tool input schema classes.
        parallel: If True, creates schema supporting multiple parallel actions.

    Returns:
        A new BaseIOSchema class with the dynamic action field(s).
    """
    # Create the union of all schemas
    all_schemas = tool_schemas + (FinalResponseSchema,)
    ActionUnion = Union[all_schemas]  # type: ignore[valid-type]

    if parallel:

        class ParallelOrchestratorOutputSchema(BaseIOSchema):
            """Orchestrator output schema supporting parallel tool execution."""

            reasoning: str = Field(
                ...,
                description="Explanation of why these tools are needed and how they work together.",
            )
            actions: List[ActionUnion] = Field(  # type: ignore[valid-type]
                ...,
                description="List of tool executions. Independent tools will run in parallel. Include FinalResponseSchema when done.",
            )

            model_config = {"arbitrary_types_allowed": True}

        return ParallelOrchestratorOutputSchema
    else:

        class DynamicOrchestratorOutputSchema(BaseIOSchema):
            """Dynamically generated orchestrator output schema."""

            reasoning: str = Field(
                ...,
                description="Detailed explanation of why this action was chosen and how it addresses the user's query.",
            )
            action: ActionUnion = Field(  # type: ignore[valid-type]
                ...,
                description="The chosen action: either a tool's input schema instance or a final response.",
            )

            model_config = {"arbitrary_types_allowed": True}

        return DynamicOrchestratorOutputSchema


######################
# ORCHESTRATOR CLASS #
######################
class OrchestratorFactory:
    """Factory for creating orchestrator agents with filtered tool sets.

    This factory creates orchestrator agents that only have access to
    the specific tools selected by the Tool Finder Agent, implementing
    the progressive disclosure pattern.

    Supports both sequential (one tool at a time) and parallel execution modes.

    Example:
        >>> factory = OrchestratorFactory(
        ...     mcp_endpoint="http://localhost:6969",
        ...     transport_type=MCPTransportType.HTTP_STREAM,
        ...     client=instructor.from_openai(openai.OpenAI()),
        ...     parallel_execution=True,  # Enable parallel mode
        ... )
        >>> orchestrator, tool_map = factory.create_with_tools(
        ...     ["AddNumbers", "SubtractNumbers"],
        ...     all_tools=all_mcp_tools,
        ... )
    """

    def __init__(
        self,
        mcp_endpoint: Optional[str],
        transport_type: MCPTransportType,
        client: instructor.Instructor,
        model: str = "gpt-5.1",
        client_session: Optional[Any] = None,
        event_loop: Optional[asyncio.AbstractEventLoop] = None,
        parallel_execution: bool = True,
    ):
        """Initialize the orchestrator factory.

        Args:
            mcp_endpoint: MCP server endpoint URL (None for STDIO).
            transport_type: MCP transport type (HTTP_STREAM, SSE, STDIO).
            client: Instructor-wrapped LLM client.
            model: Model to use for orchestration.
            client_session: Optional MCP client session for STDIO transport.
            event_loop: Optional event loop for STDIO transport.
            parallel_execution: If True, enables parallel tool execution mode.
        """
        self.mcp_endpoint = mcp_endpoint
        self.transport_type = transport_type
        self.client = client
        self.model = model
        self.client_session = client_session
        self.event_loop = event_loop
        self.parallel_execution = parallel_execution

    def create_with_tools(
        self,
        tool_names: List[str],
        all_tools: Optional[List[Type[BaseTool]]] = None,
    ) -> tuple[AtomicAgent, Dict[Type[BaseIOSchema], Type[BaseTool]]]:
        """Create an orchestrator with only the specified tools.

        This is the core method that achieves progressive disclosure:
        only the selected tools are included in the orchestrator's schema,
        keeping the context window lean and focused.

        Args:
            tool_names: Names of tools to include (from Tool Finder Agent).
            all_tools: Optional pre-fetched list of all MCP tools. If not provided,
                      tools will be fetched from the MCP server.

        Returns:
            Tuple of (orchestrator_agent, tool_schema_to_class_map).

        Raises:
            ValueError: If no matching tools are found.
        """
        # Get all tools if not provided
        if all_tools is None:
            all_tools = fetch_mcp_tools(
                mcp_endpoint=self.mcp_endpoint,
                transport_type=self.transport_type,
                client_session=self.client_session,
                event_loop=self.event_loop,
            )

        # Filter to only the requested tools
        filtered_tools = [tool for tool in all_tools if getattr(tool, "mcp_tool_name", None) in tool_names]

        if not filtered_tools:
            # If no MCP tools match, create a minimal orchestrator
            return self._create_minimal_orchestrator(), {}

        # Build schema-to-class mapping for execution
        tool_schema_to_class: Dict[Type[BaseIOSchema], Type[BaseTool]] = {tool.input_schema: tool for tool in filtered_tools}

        # Create the dynamic output schema with only filtered tools
        tool_input_schemas = tuple(tool.input_schema for tool in filtered_tools)
        output_schema = create_orchestrator_output_schema(tool_input_schemas, parallel=self.parallel_execution)

        # Build tool descriptions for the system prompt
        tool_descriptions = []
        for tool in filtered_tools:
            tool_name = getattr(tool, "mcp_tool_name", tool.__name__)
            tool_desc = tool.__doc__ or "No description available"
            tool_descriptions.append(f"- {tool_name}: {tool_desc}")

        # Create system prompt based on execution mode
        if self.parallel_execution:
            background = [
                "You are an Orchestrator Agent that MUST use the provided tools.",
                "You have a FOCUSED set of tools for this task.",
                "",
                "Available tools:",
                *tool_descriptions,
                "",
                "CRITICAL: You MUST call tools - never compute results yourself!",
                "PARALLEL MODE: Batch independent tool calls together for speed.",
            ]
            steps = [
                "1. Identify ALL tool calls needed for the query",
                "2. Batch 1: Call ALL tools whose inputs are already known",
                "3. Wait for results, then Batch 2: Call tools using those results",
                "4. Only return FinalResponseSchema AFTER all tools have been called",
            ]
            output_instructions = [
                "MANDATORY: Use tools for ALL calculations - never compute in your head",
                "BATCH independent calls: char_count('a'), char_count('b') → 2 actions together",
                "NEVER skip tools - even for simple math like sqrt or counting",
                "FinalResponseSchema: Only after ALL required tools have returned results",
            ]
        else:
            background = [
                "You are an Orchestrator Agent that processes user queries using available tools.",
                "You have been given a FOCUSED set of tools relevant to the current task.",
                "",
                "Available tools:",
                *tool_descriptions,
                "",
                "SEQUENTIAL MODE: Execute ONE tool per turn.",
                "You will be called multiple times, receiving tool results after each execution.",
            ]
            steps = [
                "1. Analyze what needs to be done next (considering previous results if any)",
                "2. Choose exactly ONE tool to execute, or provide the final response",
                "3. Fill in the tool's parameters directly in the action field",
                "4. After receiving results, continue with the next tool or finalize",
            ]
            output_instructions = [
                "Execute exactly ONE tool per turn",
                "The 'action' field must contain a SINGLE tool's input schema directly",
                "When all tools have been executed, use FinalResponseSchema with the complete answer",
            ]

        # Create the orchestrator agent
        orchestrator = AtomicAgent[OrchestratorInputSchema, output_schema](
            config=AgentConfig(
                client=self.client,
                model=self.model,
                history=ChatHistory(),
                system_prompt_generator=SystemPromptGenerator(
                    background=background,
                    steps=steps,
                    output_instructions=output_instructions,
                ),
            )
        )

        return orchestrator, tool_schema_to_class

    def _create_minimal_orchestrator(self) -> AtomicAgent:
        """Create a minimal orchestrator with no tools (for conversation only)."""
        output_schema = create_orchestrator_output_schema(tuple(), parallel=self.parallel_execution)

        if self.parallel_execution:
            output_instructions = [
                "Provide clear, helpful responses",
                "Use FinalResponseSchema in the actions list for your response",
            ]
        else:
            output_instructions = [
                "Provide clear, helpful responses",
                "Use FinalResponseSchema for your response",
            ]

        return AtomicAgent[OrchestratorInputSchema, output_schema](
            config=AgentConfig(
                client=self.client,
                model=self.model,
                history=ChatHistory(),
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "You are an assistant that responds to user queries.",
                        "No tools are currently available for this query.",
                    ],
                    steps=[
                        "1. Analyze the user's query",
                        "2. Provide a helpful response based on your knowledge",
                    ],
                    output_instructions=output_instructions,
                ),
            )
        )


##################################
# SEQUENTIAL EXECUTION (LEGACY)  #
##################################
def execute_orchestrator_loop(
    orchestrator: AtomicAgent,
    tool_schema_to_class: Dict[Type[BaseIOSchema], Type[BaseTool]],
    initial_query: str,
    max_iterations: int = 10,
    on_tool_execution: Optional[Callable] = None,
) -> str:
    """Execute the orchestrator loop sequentially (one tool at a time).

    This function handles the multi-turn interaction where the orchestrator
    selects and executes tools until it produces a final response.

    Args:
        orchestrator: The orchestrator agent.
        tool_schema_to_class: Mapping from input schemas to tool classes.
        initial_query: The user's initial query.
        max_iterations: Maximum number of tool executions.
        on_tool_execution: Optional callback for tool execution events.

    Returns:
        The final response text.
    """
    # Initial run with user query
    output = orchestrator.run(OrchestratorInputSchema(query=initial_query))
    action = output.action

    iteration = 0
    while not isinstance(action, FinalResponseSchema) and iteration < max_iterations:
        iteration += 1
        schema_type = type(action)

        # Find and execute the matching tool
        tool_class = tool_schema_to_class.get(schema_type)
        if tool_class is None:
            raise ValueError(f"Unknown action schema: {schema_type.__name__}")

        # Execute the tool
        tool_instance = tool_class()
        tool_name = getattr(tool_class, "mcp_tool_name", tool_class.__name__)

        if on_tool_execution:
            on_tool_execution(tool_name, action.model_dump())

        tool_output = tool_instance.run(action)

        # Add result to history
        result_message = OrchestratorInputSchema(query=f"Tool '{tool_name}' executed. Result: {tool_output.result}")
        orchestrator.history.add_message("system", result_message)

        # Continue the loop
        output = orchestrator.run()
        action = output.action

    if isinstance(action, FinalResponseSchema):
        return action.response_text
    else:
        return "Maximum iterations reached. Please try a simpler query."


##################################
# PARALLEL EXECUTION             #
##################################
def execute_orchestrator_loop_parallel(
    orchestrator: AtomicAgent,
    tool_schema_to_class: Dict[Type[BaseIOSchema], Type[BaseTool]],
    initial_query: str,
    max_iterations: int = 10,
    on_tool_execution: Optional[Callable] = None,
    on_parallel_batch: Optional[Callable] = None,
    max_parallel_workers: int = 5,
) -> str:
    """Execute the orchestrator loop with parallel tool execution.

    When the orchestrator returns multiple independent tools in its 'actions' list,
    they are executed concurrently using a thread pool for maximum efficiency.

    Args:
        orchestrator: The orchestrator agent (must be created with parallel_execution=True).
        tool_schema_to_class: Mapping from input schemas to tool classes.
        initial_query: The user's initial query.
        max_iterations: Maximum number of execution rounds (not individual tools).
        on_tool_execution: Optional callback for each tool execution.
        on_parallel_batch: Optional callback when a parallel batch starts, receives count.
        max_parallel_workers: Maximum concurrent tool executions.

    Returns:
        The final response text.
    """
    # Initial run with user query
    output = orchestrator.run(OrchestratorInputSchema(query=initial_query))
    actions = output.actions  # List of actions in parallel mode

    # Track executed tool calls to prevent duplicates
    executed_calls: set[str] = set()

    def get_call_signature(action) -> str:
        """Create a unique signature for a tool call."""
        tool_class = tool_schema_to_class.get(type(action))
        if tool_class is None:
            return ""
        tool_name = getattr(tool_class, "mcp_tool_name", tool_class.__name__)
        # Create signature from tool name + sorted params
        params = action.model_dump()
        params.pop("tool_name", None)  # Remove tool_name from params
        param_str = str(sorted(params.items()))
        return f"{tool_name}:{param_str}"

    iteration = 0
    while iteration < max_iterations:
        iteration += 1

        # Separate final response from tool actions
        final_responses = [a for a in actions if isinstance(a, FinalResponseSchema)]
        tool_actions = [a for a in actions if not isinstance(a, FinalResponseSchema)]

        # Filter out duplicate tool calls
        unique_tool_actions = []
        skipped_duplicates = 0
        for action in tool_actions:
            sig = get_call_signature(action)
            if sig and sig not in executed_calls:
                unique_tool_actions.append(action)
                executed_calls.add(sig)
            else:
                skipped_duplicates += 1

        tool_actions = unique_tool_actions

        # If no tool actions, we're done - return final response or error
        if not tool_actions:
            if final_responses:
                return final_responses[0].response_text
            # If we skipped duplicates, prompt model for final answer
            if skipped_duplicates > 0:
                prompt_msg = OrchestratorInputSchema(
                    query="All tool results are now available. Please provide your final answer using FinalResponseSchema."
                )
                orchestrator.history.add_message("system", prompt_msg)
                output = orchestrator.run()
                actions = output.actions
                continue  # Re-check for FinalResponseSchema
            return "No actions returned by orchestrator."

        # Notify about parallel batch
        if on_parallel_batch and len(tool_actions) > 1:
            on_parallel_batch(len(tool_actions))

        # Execute tools in parallel using ThreadPoolExecutor
        def execute_single_tool(action):
            schema_type = type(action)
            tool_class = tool_schema_to_class.get(schema_type)
            if tool_class is None:
                return {"error": f"Unknown action schema: {schema_type.__name__}"}

            tool_instance = tool_class()
            tool_name = getattr(tool_class, "mcp_tool_name", tool_class.__name__)

            if on_tool_execution:
                on_tool_execution(tool_name, action.model_dump())

            try:
                # Use sync run method - it handles async internally for MCP tools
                import warnings

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    tool_output = tool_instance.run(action)
                return {
                    "tool_name": tool_name,
                    "result": tool_output.result,
                    "success": True,
                }
            except Exception as e:
                return {
                    "tool_name": tool_name,
                    "error": str(e),
                    "success": False,
                }

        # Execute all tools in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
            future_to_action = {executor.submit(execute_single_tool, action): action for action in tool_actions}
            for future in as_completed(future_to_action):
                results.append(future.result())

        # Build result message for history
        if len(results) == 1:
            r = results[0]
            if r.get("success"):
                result_text = f"Tool '{r['tool_name']}' executed. Result: {r['result']}"
            else:
                result_text = f"Tool '{r['tool_name']}' failed. Error: {r.get('error')}"
        else:
            result_lines = ["Tools executed in parallel:"]
            for r in results:
                if r.get("success"):
                    result_lines.append(f"  - {r['tool_name']}: {r['result']}")
                else:
                    result_lines.append(f"  - {r['tool_name']}: ERROR - {r.get('error')}")
            result_text = "\n".join(result_lines)

        # Add results to history
        result_message = OrchestratorInputSchema(query=result_text)
        orchestrator.history.add_message("system", result_message)

        # Continue the loop
        output = orchestrator.run()
        actions = output.actions

    return "Maximum iterations reached. Please try a simpler query."


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from rich.console import Console

    console = Console()
    console.print("[bold]Orchestrator Factory Demo[/bold]")
    console.print("This module is typically used via main.py")
    console.print("See main.py for a complete example of progressive disclosure in action.")
    console.print("")
    console.print("[cyan]Parallel Execution Mode:[/cyan]")
    console.print("  - Multiple independent tools execute concurrently")
    console.print("  - Example: sqrt(14) + sqrt(10) runs both sqrt calls in parallel")
    console.print("  - Reduces latency by ~50% for independent operations")
