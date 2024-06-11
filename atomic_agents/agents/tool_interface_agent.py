import json
from pydantic import Field, create_model
from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo
from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.lib.utils.format_tool_message import format_tool_message


class ToolInterfaceAgentConfig(BaseChatAgentConfig):
    tool_instance: BaseTool
    return_raw_output: bool = False


class ToolInterfaceAgent(BaseChatAgent):
    """
    A specialized chat agent designed to interact with a specific tool.

    This agent extends the BaseChatAgent to include functionality for interacting with a tool instance.
    It generates system prompts, handles tool input and output, and can optionally return raw tool output.

    Attributes:
        tool_instance: The instance of the tool this agent will interact with.
        return_raw_output (bool): Whether to return the raw output from the tool.
    """

    def __init__(self, config: ToolInterfaceAgentConfig):
        """
        Initializes the ToolInterfaceAgent.

        Args:
            config (ToolInterfaceAgentConfig): Configuration for the tool interface agent.
        """
        super().__init__(config=config)
        
        self.tool_instance = config.tool_instance
        self.return_raw_output = config.return_raw_output
        
        self.input_schema = create_model(
            self.tool_instance.tool_name,
            tool_input=(str, Field(..., description=f"{self.tool_instance.tool_name} tool input. Presented as a single question or instruction", alias=f'tool_input_{self.tool_instance.tool_name}')),
            __config__=type('Config', (), {
                'title': self.tool_instance.tool_name,
                'description': self.tool_instance.tool_description,
                'json_schema_extra': {
                    "title": self.tool_instance.tool_name,
                    "description": self.tool_instance.tool_description
                }
            })
        )
        
        if self.return_raw_output:
            self.output_schema = self.tool_instance.output_schema
            
        self.system_prompt_generator = SystemPromptGenerator(
            system_prompt_info=SystemPromptInfo(
                background=[
                    f"This AI agent is designed to interact with the {self.tool_instance.tool_name} tool.",
                    f"Tool description: {self.tool_instance.tool_description}"
                ],
                steps=[
                    "Get the user input.",
                    "Convert the input to the proper parameters to call the tool.",
                    "Call the tool with the parameters.",
                    "Respond to the user"
                ],
                output_instructions=[
                    "Make sure the tool call will maximize the utility of the tool in the context of the user input.",
                    "Process the output of the tool into a human readable format and/or use it to respond to the user input." if self.return_raw_output else "Return the raw output of the tool."
                ]
            )
        )
        
    def _get_and_handle_response(self):
        """
        Handles obtaining and processing the response from the tool.

        This method gets the response from the tool, formats the tool input, adds it to memory,
        runs the tool, and processes the tool output. If `return_raw_output` is True, it returns
        the raw tool output; otherwise, it processes the output and returns the response.
        
        Returns:
            BaseModel: The processed response or raw tool output.
        """
        tool_input = self.get_response(response_model=self.tool_instance.input_schema)
        formatted_tool_input = format_tool_message(tool_input)
        
        self.memory.add_message('assistant', 'TOOL CALL: ' + json.dumps(formatted_tool_input))
        tool_output = self.tool_instance.run(tool_input)
        self.memory.add_message('assistant', 'TOOL RESPONSE: ' + tool_output.model_dump_json())
        
        if self.return_raw_output:
            return tool_output
        
        self.memory.add_message('assistant', 'I will now formulate a response for the user based on the tool output.')
        response = self.get_response(response_model=self.output_schema)        
        return response