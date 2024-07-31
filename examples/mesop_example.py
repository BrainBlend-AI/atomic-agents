##########
# This example is basically the same as "simple_web_search_agent.py",
# but it uses the Google Mesop library for a simple and easy chat UI
# simply do "pip install mesop" to install it.
# https://google.github.io/mesop/
#
# To run, do "mesop simple_web_search_agent.py"
##########

import os
import instructor
import openai
from rich.console import Console
import mesop as me
import mesop.labs as mel
from dataclasses import field

from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig
from atomic_agents.lib.tools.search.searxng_tool import SearxNGTool, SearxNGToolConfig

# Initialize the console, client, and tools
console = Console()
client = instructor.from_openai(openai.OpenAI())


def initialize_searxng_tool():
    base_url = os.getenv("SEARXNG_BASE_URL")
    config = SearxNGToolConfig(base_url=base_url, max_results=10)
    return SearxNGTool(config)


searxng_tool = initialize_searxng_tool()


def initialize_agent(client, searxng_tool):
    agent_config = ToolInterfaceAgentConfig(
        client=client, model="gpt-4o-mini", tool_instance=searxng_tool, return_raw_output=False
    )
    return ToolInterfaceAgent(config=agent_config)


agent = initialize_agent(client, searxng_tool)


# Mesop state class
@me.stateclass
class State:
    chat_history: list[mel.ChatMessage] = field(default_factory=list)


# Mesop transform function
def transform(input: str, history: list[mel.ChatMessage]):
    state = me.state(State)
    response = agent.run(agent.input_schema(tool_input_SearxNGTool=input))
    state.chat_history.append(mel.ChatMessage(content=f"You: {input}"))
    state.chat_history.append(mel.ChatMessage(content=f"Agent: {response.chat_message}"))
    yield response.chat_message


# Mesop page
@me.page(path="/", title="ToolInterfaceAgent Chat")
def page():
    mel.chat(transform, title="ToolInterfaceAgent with SearxNGTool", bot_user="Agent")
