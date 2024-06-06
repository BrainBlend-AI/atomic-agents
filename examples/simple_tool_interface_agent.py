import os
import instructor
import openai
from  rich.console import Console

from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent
from atomic_agents.lib.tools.searx import SearxNGSearchTool

console = Console()

# Initialize the client
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
client = instructor.from_openai(openai.OpenAI())

# Initialize the SearxNGSearchTool
searx_tool = SearxNGSearchTool(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=10)

# Initialize the ToolInterfaceAgent with the SearxNGSearchTool
agent = ToolInterfaceAgent(
    tool_instance=searx_tool,
    client=client,
    model='gpt-3.5-turbo'
)

console.print("ToolInterfaceAgent with SearxNGSearchTool is ready.")

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')