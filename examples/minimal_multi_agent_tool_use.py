import os
from typing import Union
import instructor
import openai
from pydantic import create_model
from rich.console import Console
from atomic_agents.agents.base_chat_agent import BaseAgentIO, BaseChatAgent, BaseChatAgentConfig
from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig
from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolConfig

console = Console()
client = instructor.from_openai(openai.OpenAI())
searx_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=10))
calc_tool = CalculatorTool(CalculatorToolConfig())

search_agent_config = ToolInterfaceAgentConfig(client=client, model='gpt-3.5-turbo', tool_instance=searx_tool, return_raw_output=False)
calculator_agent_config = ToolInterfaceAgentConfig(client=client, model='gpt-3.5-turbo', tool_instance=calc_tool, return_raw_output=False)
searx_agent, calc_agent = ToolInterfaceAgent(config=search_agent_config), ToolInterfaceAgent(config=calculator_agent_config)

UnionResponse = create_model('UnionResponse', __base__=BaseAgentIO, response=(Union[searx_agent.input_schema, calc_agent.input_schema], ...))

orchestration_agent = BaseChatAgent(config=BaseChatAgentConfig(client=client, model='gpt-3.5-turbo', output_schema=UnionResponse))

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = orchestration_agent.run(orchestration_agent.input_schema(chat_input=user_input))
    console.print(f'Agent: {response.response}')

    if isinstance(response.response, searx_agent.input_schema):
        console.print(f'Using searx agent')
        response = searx_agent.run(response.response)
    elif isinstance(response.response, calc_agent.input_schema):
        console.print(f'Using calc agent')
        response = calc_agent.run(response.response)

    console.print(f'Agent: {response.response}')