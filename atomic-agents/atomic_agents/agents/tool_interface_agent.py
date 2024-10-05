import json

from pydantic import Field, create_model

from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.base.base_tool import BaseTool
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
