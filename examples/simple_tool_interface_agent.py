import instructor
import openai
from  rich.console import Console

from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent
from atomic_agents.lib.tools.searx import SearxNGSearchTool

console = Console()

# Initialize the client
client = instructor.from_openai(openai.OpenAI())

# Initialize the SearxNGSearchTool
searx_tool = SearxNGSearchTool(max_results=5)

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