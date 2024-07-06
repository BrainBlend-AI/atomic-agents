import json
import os
import random
import groq
import instructor
import openai
from rich.console import Console
from atomic_agents.agents.base_chat_agent import BaseChatAgentConfig, BaseChatAgent, BaseChatAgentInputSchema, BaseChatAgentOutputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo

# Initialize the system prompts. For simplicity, we use the same system prompt for both agents.
agent1_system_prompt_info = SystemPromptInfo(
    background=['You are an agent that adds 1 to the number said by the previous person in the conversation.'],
    steps=['If the previous message contains a number, add 1 to it.'],
    output_instructions=['Respond with only the resulting added number and never anything else. Do not include any additional text.']
)

agent2_system_prompt_info = SystemPromptInfo(
    background=['You are an agent that adds 1 to the number said by the previous person in the conversation.'],
    steps=['If the previous message contains a number, add 1 to it.'],
    output_instructions=['Respond with only the resulting added number and never anything else. Do not include any additional text.']
)

# Initialize the agents. For fun, we use two different clients for the agents. One uses Groq and the other uses OpenAI.
# You can use the same client for both agents if you prefer. For a list of supported clients, refer to the `instructor` library documentation.
agent1 = BaseChatAgent(
    config=BaseChatAgentConfig(
        client=instructor.from_groq(groq.Groq(api_key=os.getenv('GROQ_API_KEY'))),
        model=os.getenv('GROQ_CHAT_MODEL'),
        system_prompt_generator=SystemPromptGenerator(system_prompt_info=agent1_system_prompt_info)
    )
)

agent2 = BaseChatAgent(
    config=BaseChatAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model='gpt-3.5-turbo',
        system_prompt_generator=SystemPromptGenerator(system_prompt_info=agent2_system_prompt_info)
    )
)

# Function to simulate a conversation between the two agents
def simulate_conversation(num_turns=5):
    console = Console()
    next_input = "123"
    
    for _ in range(num_turns):
        agent1_response = agent1.run(agent1.input_schema(chat_message=next_input))
        console.print(f'[bold blue]Agent 1:[/bold blue] {agent1_response.chat_message}')
        next_input = agent1_response.chat_message
        
        agent2_response = agent2.run(agent2.input_schema(chat_message=next_input))
        console.print(f'[bold green]Agent 2:[/bold green] {agent2_response.chat_message}')
        next_input = agent2_response.chat_message

if __name__ == "__main__":
    simulate_conversation(num_turns=5)
