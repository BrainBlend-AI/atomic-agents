import os
import logging
from typing import Union
from pydantic import BaseModel, Field
import instructor
import openai
from rich.console import Console

from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo
from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentResponseSchema, BaseChatAgentConfig
from atomic_agents.lib.tools.yelp_restaurant_finder_tool import YelpSearchTool, YelpSearchToolConfig, YelpSearchToolSchema

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define system prompt information including background, steps, and output instructions
system_prompt = SystemPromptInfo(
    background=[
        'This assistant is a restaurant finder AI designed to help users find the best restaurants based on their preferences by asking clarifying questions.',
    ],
    steps=[
        'Greet the user and introduce yourself as a restaurant finder assistant.',
        'Inspect the required Yelp schema and identify the necessary filters.',
        'Ask the user questions to gather information for each filter until all required information is clear.',
        'Use the chat responses to gather all necessary information from the user.',
        'Once all required information is gathered, use the YelpSearchTool schema to search Yelp for restaurants.',
    ],
    output_instructions=[
        'Provide helpful and relevant information to assist the user.',
        'Be friendly and respectful in all interactions.',
        'Ensure that the chat responses are used to ask clarifying questions and gather information, and the Yelp schema is used to perform the actual search.'
    ]
)

# Initialize the system prompt generator with the defined system prompt and dynamic info providers
system_prompt_generator = SystemPromptGenerator(system_prompt)

# Initialize chat memory to store conversation history
memory = ChatMemory()
# Define initial memory with a greeting message from the assistant
initial_memory = [
    {'role': 'assistant', 'content': 'Hello, can I help you find a restaurant?'}
]
# Load the initial memory into the chat memory
memory.load(initial_memory)

console = Console()

# Initialize the client
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
client = instructor.from_openai(openai.OpenAI())

# Initialize the YelpSearchTool
yelp_tool = YelpSearchTool(YelpSearchToolConfig(api_key=os.getenv('YELP_API_KEY'), max_results=10))

# Define a custom response schema that can handle both chat responses and Yelp search tool responses
class ResponseSchema(BaseModel):
    chosen_schema: Union[BaseChatAgentResponseSchema, YelpSearchToolSchema] = Field(..., description='The response from the chat agent.')

    class Config:
        title = 'ResponseSchema'
        description = 'The response schema for the chat agent.'
        json_schema_extra = {
            'title': title,
            'description': description,
        }

# Create a config for the chat agent
agent_config = BaseChatAgentConfig(
    client=client,
    system_prompt_generator=system_prompt_generator,
    model='gpt-3.5-turbo',
    memory=memory,
    output_schema=ResponseSchema
)

# Create a chat agent with the specified config
agent = BaseChatAgent(config=agent_config)

console.print("BaseChatAgent with YelpSearchTool is ready.")
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = agent.run(agent.input_schema(chat_input=user_input))
    
    # Log the chosen schema
    logger.info(f'Chosen schema: {response.chosen_schema}')
    
    # Check the type of the response schema
    if isinstance(response.chosen_schema, YelpSearchToolSchema):
        output = yelp_tool.run(response.chosen_schema)
        
        # In this example, we will add a simple "internal thought" to the chat memory followed by an empty agent.run() call. 
        # This will make the agent continue the conversation without user input.
        # In a more complex example, it might be preferable to extend the BaseChatAgent class and override the _get_and_handle_response method.
        agent.memory.add_message('assistant', f'INTERNAL THOUGHT: I have found the following information: {output.results}\n\n I will now summarize the results for the user.')
        output = agent.run().chosen_schema.response
    else:
        output = response.chosen_schema.response
        
    console.print(f'Agent: {output}')