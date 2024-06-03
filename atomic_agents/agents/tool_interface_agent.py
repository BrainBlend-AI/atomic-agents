from datetime import datetime
import os
from typing import Optional, Type
import instructor
import openai
from pydantic import BaseModel, Field, create_model
from rich.console import Console
from atomic_agents.lib.chat_memory import ChatMemory
from atomic_agents.lib.utils.format_tool_message import format_tool_message
from atomic_agents.tools.base import BaseTool
from atomic_agents.tools.searx import SearxNGSearchTool
from atomic_agents.tools.calculator_tool import CalculatorTool
from atomic_agents.lib.utils.logger import logger

class NextStepsResponse(BaseModel):
    observation: str = Field(..., description='Observation of the current state of the conversation.')
    thought: str = Field(..., description='Thought process of the agent.')
    next_action: str = Field(..., description='Description of the next action the assistant should take.')
    conclusion: str = Field(..., description='Conclusion of the current state of the conversation.')
    
    class Config:
        title = "NextStepsResponse"
        description = "Response from the agent that details the next steps to take in the conversation based on the current state and the agent's thought process."
        json_schema_extra = {
            "title": title,
            "description": description
        }

class ToolInterfaceAgentOutput(BaseModel):
    internal_thought: NextStepsResponse = Field(..., description="Internal thought process involved in formulating the response or tool call.")
    processed_output: str = Field(..., description="Processed markdown-enabled output of the tool to answer the original query or instruction.")
    
    class Config:
        title = "ToolInterfaceAgentOutput"
        description = "Processed output of the ToolInterfaceAgent. The first property will always be the 'internal_thought' property, which is the internal thought process of the agent."
        json_schema_extra = {
            "title": title,
            "description": description
        }

class ToolInterfaceAgent:
    def __init__(
            self, 
            tool_instance: BaseTool, 
            client, openai_api_key: Optional[str] = None, 
            openai_base_url: Optional[str] = None, 
            model: str = "gpt-3.5-turbo", 
            process_output: bool = True, 
            agent_background: Optional[str] = "This AI agent is designed to interact with tools to perform various tasks. The agent gets human readable input, converts it to a command, and returns the output in a human readable format."
        ):
        self.tool_instance = tool_instance
        
        self.tool_name = f"{self.tool_instance.tool_name}"
        self.tool_description = f"{self.tool_instance.tool_description}"
        
        self.client = client
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_base_url = openai_base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model
        self.memory = ChatMemory()
        self.process_output = process_output
        self.agent_background = agent_background
        
        self.console = Console()
        
        self.input_schema = create_model(
            self.tool_name,
            tool_input=(str, Field(..., description=f"{self.tool_name} tool input. Presented as a single question or instruction", alias=f'tool_input_{self.tool_name}')),
            __config__=type('Config', (), {
                'title': self.tool_name,
                'description': self.tool_description,
                'json_schema_extra': {
                    "title": self.tool_name,
                    "description": self.tool_description
                }
            })
        )
        
        if self.process_output:
            self.output_schema = ToolInterfaceAgentOutput
        else:
            self.output_schema = self.tool_instance.output_schema

    def get_system_prompt(self) -> str:
        current_date = datetime.now().isoformat()
        system_prompt = (
            f"{self.agent_background}\n"
            "\n"
            f"The tool being used is {self.tool_name}: {self.tool_description}.\n"
            f"\n"
            f"The current date, in ISO format, is {current_date}.\n"
        )
        return system_prompt

    def get_response(self, response_schema: Type[BaseModel] = ToolInterfaceAgentOutput) -> Type[BaseModel]:
        messages = [{"role": "system", "content": self.get_system_prompt()}] + self.memory.get_history()
        result = self.client.chat.completions.create(
            model=self.model,
            response_model=response_schema,
            messages=messages,
        )
        logger.verbose(f"get_response result: {result}")
        return result

    def run(self, params: Type[BaseModel]) -> Type[BaseModel]:
        text = params.tool_input
        self.memory.add_message("user", text)
        logger.verbose(f"User input added to memory: {text}")
        input_params = self.get_response(self.tool_instance.input_schema)
        logger.verbose(f"Input parameters received: {input_params}")
        tool_message = format_tool_message(input_params)
        logger.verbose(f"Formatted tool message: {tool_message}")
        output = self.tool_instance.run(input_params)
        logger.verbose(f"Tool output: {output}")
        
        if self.process_output:
            self.memory.add_message("assistant", "", tool_message=tool_message)
            self.memory.add_message("tool", output.model_dump_json(), tool_id=tool_message['id'])
            response = self.get_response(ToolInterfaceAgentOutput)
            logger.info(f"ToolInterfaceAgent response: {response}")
            self.memory.add_message("assistant", response.model_dump_json())
            return response
        else:
            return output


if __name__ == "__main__":    
    # Initialize the OpenAI client
    openai_client = instructor.from_openai(
        openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    )
    
    # Instantiate tool instances directly
    web_search_tool = SearxNGSearchTool(max_results=20)
    calculator_tool = CalculatorTool()
    
    # Instantiate agents with tool instances and the client
    web_search_agent = ToolInterfaceAgent(web_search_tool, openai_client, model="gpt-3.5-turbo")
    calculator_agent = ToolInterfaceAgent(calculator_tool, openai_client, model="gpt-3.5-turbo")
    
    console = Console()
    
    # Example usage with SearxNGSearchTool
    web_search_output = web_search_agent.run(web_search_agent.input_schema(tool_input_SearxNGSearchTool="Search for the best restaurants in New York City"))
    console.print(web_search_output) # Type will be ToolInterfaceAgentOutput
    console.print("\n====================\n")
    calculator_output = calculator_agent.run(calculator_agent.input_schema(tool_input_CalculatorTool="Calculate the square root of 144"))
    console.print(calculator_output) # Type will be ToolInterfaceAgentOutput