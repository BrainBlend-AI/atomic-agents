import os
from typing import List, Union

from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown

import instructor
import openai

from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentResponse, BaseChatAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator, SystemPromptInfo
from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolSchema
from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig, SearxNGSearchToolSchema

# Initialize tools
search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=10))
calculator_tool = CalculatorTool()

# Define ToolInfoProvider class
class ToolInfoProvider(SystemPromptContextProviderBase):        
    def get_info(self) -> str:
        response = 'The available tools are:\n'
        for tool in [search_tool, calculator_tool]:
            response += f'- {tool.tool_name}: {tool.tool_description}\n'
        return response

# Define system prompt information including background, steps, and output instructions
system_prompt = SystemPromptInfo(
    background=[
        'This assistant is an orchestrator of tasks designed to be helpful and efficient.',
    ],
    steps=[
        'Understand the user\'s input and the current context.',
        'Take a step back and think methodically and step-by-step about how to proceed by using internal reasoning.',
        'Evaluate the available tools and decide whether to use a tool based on the current context, user input, and history.',
        'If a tool can be used, decide which tool to use and how to use it.',
        'If a tool can be used it must always be explicitly mentioned in the internal reasoning response.',
        'If a tool can be used, return nothing but the tool response to the user. If no tool is needed or if the tool has finished, return a chat response.',
        'Execute the chosen tool and provide a relevant response to the user.'
    ],
    output_instructions=[
        'Provide helpful and relevant information to assist the user.',
        'Be efficient and effective in task orchestration.',
        'Always answer in rhyming verse.'
    ],
    context_providers={
        'tools': ToolInfoProvider(title='Available tools')
    }
)

# Define InternalReasoningResponse class
class InternalReasoningResponse(BaseModel):
    observation: str = Field(..., description='What is the current state of the conversation and context? What is the user saying or asking?')
    action_plan: List[str] = Field(..., min_length=1, description='What steps could be taken to address the current observation? Is there a tool that could be used?')

    class Config:
        title = 'InternalReasoningResponse'
        description = 'The internal reasoning response schema for the chat agent, following the ReACT pattern.'
        json_schema_extra = {
            'title': title,
            'description': description,
        }

# Define ResponseSchema class
class ResponseSchema(BaseModel):
    chosen_schema: Union[BaseChatAgentResponse, SearxNGSearchToolSchema, CalculatorToolSchema] = Field(..., description='The response from the chat agent, which may include the result of using a tool if one was deemed necessary.')
    
    class Config:
        title = 'ResponseSchema'
        description = 'The response schema for the chat agent, including potential tool usage results.'
        json_schema_extra = {
            'title': title,
            'description': description,
        }

# Initialize the system prompt generator with the defined system prompt and dynamic info providers
system_prompt_generator = SystemPromptGenerator(system_prompt)

# Test out the system prompt generator
console = Console()
console.print('='*50)
console.print(Markdown(system_prompt_generator.generate_prompt()))
console.print('='*50)

# Print the response schema
console.print(ResponseSchema.model_json_schema())
console.print('='*50)

# Initialize chat memory to store conversation history
memory = ChatMemory()
# Define initial memory with a greeting message from the assistant
initial_memory = [
    {'role': 'assistant', 'content': 'How do you do? What can I do for you? Tell me, pray, what is your need today?'}
]
# Load the initial memory into the chat memory
memory.load(initial_memory)

# Define OrchestratorAgentConfig class
class OrchestratorAgentConfig(BaseChatAgentConfig):
    pass

# Define OrchestratorAgent class
class OrchestratorAgent(BaseChatAgent):
    def _pre_run(self):
        self.memory.add_message('assistant', 'First, I will plan my steps and think about the tools at my disposal.')
        response = self.get_response(response_model=InternalReasoningResponse)
        self.memory.add_message('assistant', f'INTERNAL THOUGHT: I have observed "{response.observation}" and will take the following steps: {", ".join(response.action_plan)}')
        return

# Update the configuration to use OrchestratorAgentConfig
config = OrchestratorAgentConfig(
    client=instructor.from_openai(openai.OpenAI()),
    model='gpt-3.5-turbo',
    system_prompt_generator=system_prompt_generator,
    memory=memory,
    output_schema=ResponseSchema
)

# Create an instance of OrchestratorAgent with the specified configuration
agent = OrchestratorAgent(config=config)

# Main chat loop for testing the chat agent
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['/exit', '/quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response}')