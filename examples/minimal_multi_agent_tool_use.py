import os
from typing import Union
import instructor
import openai
from pydantic import create_model
from rich.console import Console
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig
from atomic_agents.lib.tools.search.searxng_tool import SearxNGTool, SearxNGToolConfig
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolConfig

console = Console()
client = instructor.from_openai(openai.OpenAI())
searxng_tool = SearxNGTool(SearxNGToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=10))
calc_tool = CalculatorTool(CalculatorToolConfig())

search_agent_config = ToolInterfaceAgentConfig(
    client=client, model="gpt-4o-mini", tool_instance=searxng_tool, return_raw_output=False
)
calculator_agent_config = ToolInterfaceAgentConfig(
    client=client, model="gpt-4o-mini", tool_instance=calc_tool, return_raw_output=False
)
searx_agent = ToolInterfaceAgent(config=search_agent_config)
calc_agent = ToolInterfaceAgent(config=calculator_agent_config)

UnionResponse = create_model(
    "UnionResponse", __base__=BaseIOSchema, response=(Union[searx_agent.input_schema, calc_agent.input_schema], ...)
)

orchestration_agent = BaseAgent(config=BaseAgentConfig(client=client, model="gpt-4o-mini", output_schema=UnionResponse))

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    orchestration_agent_output = orchestration_agent.run(orchestration_agent.input_schema(chat_message=user_input))
    console.print(f"Agent: {orchestration_agent_output.response}")

    if isinstance(orchestration_agent_output.response, searx_agent.input_schema):
        console.print(f"Using searx agent")
        response = searx_agent.run(orchestration_agent_output.response)
    elif isinstance(orchestration_agent_output.response, calc_agent.input_schema):
        console.print(f"Using calc agent")
        response = calc_agent.run(orchestration_agent_output.response)

    console.print(f"Agent: {response}")
