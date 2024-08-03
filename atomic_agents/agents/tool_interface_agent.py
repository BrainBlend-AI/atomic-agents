import json

from pydantic import Field, create_model

from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.tools.base_tool import BaseTool
from atomic_agents.lib.utils.format_tool_message import format_tool_message


class ToolInterfaceAgentConfig(BaseAgentConfig):
    tool_instance: BaseTool


class ToolInterfaceAgent(BaseAgent):
    """
    A specialized chat agent designed to interact with a specific tool.

    This agent extends the BaseAgent to include functionality for interacting with a tool instance.
    It generates system prompts, handles tool input and output, and processes the tool output.

    Attributes:
        tool_instance: The instance of the tool this agent will interact with.
    """

    def __init__(self, config: ToolInterfaceAgentConfig):
        """
        Initializes the ToolInterfaceAgent.

        Args:
            config (ToolInterfaceAgentConfig): Configuration for the tool interface agent.
        """
        super().__init__(config=config)

        self.tool_instance = config.tool_instance

        # Create a new model with the updated schema
        self.input_schema = create_model(
            self.tool_instance.__class__.__name__,
            tool_input=(
                str,
                Field(
                    ...,
                    description=(
                        f"{self.tool_instance.__class__.__name__} tool input. " "Presented as a single question or instruction"
                    ),
                    alias=f"tool_input_{self.tool_instance.__class__.__name__}",
                ),
            ),
            __base__=BaseIOSchema,
            __doc__=self.tool_instance.tool_description,
        )

        # Set the __name__ attribute of the new model
        self.input_schema.__name__ = self.tool_instance.__class__.__name__

        output_instructions = [
            "Make sure the tool call will maximize the utility of the tool in the context of the user input.",
            "Process the output of the tool into a human readable format and use it to respond to the user input.",
        ]

        self.system_prompt_generator = SystemPromptGenerator(
            background=[
                f"This AI agent is designed to interact with the {self.tool_instance.tool_name} tool.",
                f"Tool description: {self.tool_instance.tool_description}",
            ],
            steps=[
                "Get the user input.",
                "Convert the input to the proper parameters to call the tool.",
                "Call the tool with the parameters.",
                "Process the tool output and respond to the user",
            ],
            output_instructions=output_instructions,
        )

    def get_response(self, response_model=None):
        """
        Handles obtaining and processing the response from the tool.

        This method gets the response from the tool, formats the tool input, adds it to memory,
        runs the tool, processes the tool output, and returns the processed response.

        Args:
            response_model: Ignored in this implementation, but included for compatibility with BaseAgent.

        Returns:
            BaseModel: The processed response.
        """
        tool_input = super().get_response(response_model=self.tool_instance.input_schema)
        formatted_tool_input = format_tool_message(tool_input)

        self.memory.add_message("assistant", "TOOL CALL: " + json.dumps(formatted_tool_input))
        tool_output = self.tool_instance.run(tool_input)
        self.memory.add_message("assistant", "TOOL RESPONSE: " + tool_output.model_dump_json())

        self.memory.add_message(
            "assistant",
            "I will now formulate a response for the user based on the tool output.",
        )
        response = super().get_response(response_model=response_model or self.output_schema)
        return response


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    import instructor
    import openai
    from atomic_agents.lib.tools.calculator_tool import CalculatorTool

    # Initialize the console
    console = Console()

    # Initialize the client
    client = instructor.from_openai(openai.OpenAI())

    # Initialize the tool
    example_tool = CalculatorTool()

    # Initialize the agent
    config = ToolInterfaceAgentConfig(client=client, model="gpt-4o-mini", tool_instance=example_tool)
    agent = ToolInterfaceAgent(config)

    # Print agent information
    console.print(Panel.fit("[bold blue]Tool Interface Agent Information[/bold blue]", border_style="blue", padding=(1, 1)))

    # Print input schema
    input_schema_table = Table(title="Input Schema", box=box.ROUNDED)
    input_schema_table.add_column("Field", style="cyan")
    input_schema_table.add_column("Type", style="magenta")
    input_schema_table.add_column("Description", style="green")

    for field_name, field in agent.input_schema.model_fields.items():
        input_schema_table.add_row(field_name, str(field.annotation), field.description or "")

    console.print(input_schema_table)

    # Print output schema
    output_schema_table = Table(title="Output Schema", box=box.ROUNDED)
    output_schema_table.add_column("Field", style="cyan")
    output_schema_table.add_column("Type", style="magenta")
    output_schema_table.add_column("Description", style="green")

    for field_name, field in agent.output_schema.model_fields.items():
        output_schema_table.add_row(field_name, str(field.annotation), field.description or "")

    console.print(output_schema_table)

    # Print other agent information
    info_table = Table(title="Agent Configuration", box=box.ROUNDED)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="yellow")

    info_table.add_row("Model", agent.model)
    info_table.add_row("Memory", str(type(agent.memory).__name__))
    info_table.add_row("System Prompt Generator", str(type(agent.system_prompt_generator).__name__))
    info_table.add_row("Tool Instance", str(type(agent.tool_instance).__name__))

    console.print(info_table)

    # Print a sample of the system prompt
    system_prompt = agent.system_prompt_generator.generate_prompt()
    console.print(
        Panel(
            Syntax(system_prompt, "markdown", theme="monokai", line_numbers=True),
            title="Sample System Prompt",
            border_style="green",
            expand=False,
        )
    )

    console.print("\n[bold]Tool Interface Agent initialized and ready to use![/bold]")

    # Test the agent with a sample input
    test_input = agent.input_schema(tool_input="What's the weather like today?")
    console.print(Panel(f"Test Input: {test_input}", title="Test Run", border_style="yellow"))

    response = agent.run(test_input)
    console.print(Panel(f"Agent Response: {response}", title="Test Result", border_style="green"))
