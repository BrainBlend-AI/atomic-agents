# simple_web_search_agent.py
import os
import instructor
import openai
from rich.console import Console

from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig
from atomic_agents.lib.tools.search.searx_tool import SearxNGTool, SearxNGToolConfig

def initialize_searx_tool():
    """
    Initialize the SearxNGTool with configuration.
    """
    base_url = os.getenv('SEARXNG_BASE_URL')
    config = SearxNGToolConfig(base_url=base_url, max_results=10)
    return SearxNGTool(config)

def initialize_agent(client, searx_tool):
    """
    Initialize the ToolInterfaceAgent with the given client and SearxNGTool.
    """
    agent_config = ToolInterfaceAgentConfig(
        client=client,
        model='gpt-3.5-turbo',
        tool_instance=searx_tool,
        return_raw_output=False
    )
    return ToolInterfaceAgent(config=agent_config)

def main():
    console = Console()
    client = instructor.from_openai(openai.OpenAI())
    searx_tool = initialize_searx_tool()
    agent = initialize_agent(client, searx_tool)

    console.print("ToolInterfaceAgent with SearxNGTool is ready.")

    while True:
        user_input = input('You: ')
        if user_input.lower() in ['exit', 'quit']:
            print('Exiting chat...')
            break
        
        # Fix this
        response = agent.run(agent.input_schema(tool_input_SearxNGTool=user_input))
        console.print(f'Agent: {response.chat_message}')

if __name__ == "__main__":
    main()