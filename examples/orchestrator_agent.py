import os
from typing import List, Type, Union
from pydantic import BaseModel, Field
from rich.console import Console
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentResponse
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator, SystemPromptInfo
import instructor
import openai

from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolSchema
from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig, SearxNGSearchToolSchema

search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=10))
calculator_tool = CalculatorTool()

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
        'Look at the tools available and determine which to use next based on the current context, user input, and history.',
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

class ResponseSchema(BaseModel):
    chosen_schema: Union[BaseChatAgentResponse, SearxNGSearchToolSchema, CalculatorToolSchema] = Field(..., description='The response from the chat agent.')
    
    class Config:
        title = 'ResponseSchema'
        description = 'The response schema for the chat agent.'
        json_schema_extra = {
            'title': title,
            'description': description,
        }

# Initialize the system prompt generator with the defined system prompt and dynamic info providers
system_prompt_generator = SystemPromptGenerator(system_prompt)

# Test out the system prompt generator
from rich.markdown import Markdown
from rich.console import Console
Console().print('='*50)
Console().print(Markdown(system_prompt_generator.generate_prompt()))
Console().print('='*50)

# Print the response schema
Console().print(ResponseSchema.model_json_schema())
Console().print('='*50)

# Initialize chat memory to store conversation history
memory = ChatMemory()
# Define initial memory with a greeting message from the assistant
initial_memory = [
    {'role': 'assistant', 'content': 'How do you do? What can I do for you? Tell me, pray, what is your need today?'}
]
# Load the initial memory into the chat memory
memory.load(initial_memory)

# Create a chat agent with the specified model, system prompt generator, and memory
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
agent = BaseChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    system_prompt_generator=system_prompt_generator,
    model='gpt-3.5-turbo',
    memory=memory,
    output_schema=ResponseSchema
)

# Main chat loop for testing the chat agent
console = Console()
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['/exit', '/quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response}')