###############################
# WARNING: NOT YET FINISHED!  #
###############################


import os
from rich.console import Console
from pydantic import BaseModel, Field
from typing import List
from rich.markdown import Markdown
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo
import instructor
import openai

from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig
from examples.deep_research_multi_agent.deep_query_agent import DeepQueryAgentInputSchema, deep_query_agent

search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=30))

# Define the Pydantic schema for the article outline
class Subsection(BaseModel):
    title: str = Field(..., description="The title of the subsection. This field is required.")
    content: str = Field(..., description="A brief description or content of the subsection. This field is required.")

class Section(BaseModel):
    title: str = Field(..., description="The title of the section. This field is required.")
    subsections: List[Subsection] = Field(..., description="A list of subsections under this section. This field is required.")

class ArticleOutline(BaseModel):
    title: str = Field(..., description="The title of the article. This field is required.")
    sections: List[Section] = Field(..., description="A list of sections in the article. This field is required.")

# Define system prompt information including background, steps, and output instructions
system_prompt = SystemPromptInfo(
    background=[
        'This assistant is an expert at generating article outlines based on user input.',
    ],
    steps=[
        '1. Understand the user\'s input and identify the main topic of the article.',
        '2. Generate a relevant article outline based on the identified topic, including sections and subsections, based on search results and user input.',
        '3. Ensure the outline includes sections and subsections with appropriate titles and detailed descriptions.',
        '4. Each section should have a clear and concise title that reflects its content.',
        '5. Each subsection should provide a brief but comprehensive description of its content.',
        '6. Review the generated outline to ensure it is well-structured and logically organized.',
    ],
    output_instructions=[
        'Provide a structured article outline in the form of sections and subsections.',
        'Be clear and concise in the titles and descriptions.',
        'Ensure that all fields are filled and nothing is left blank.',
    ]
)

# Initialize the system prompt generator with the defined system prompt and dynamic info providers
system_prompt_generator = SystemPromptGenerator(system_prompt)

# Initialize chat memory to store conversation history
memory = ChatMemory()
# Define initial memory with a greeting message from the assistant
initial_memory = [
    {'role': 'assistant', 'content': 'How do you do? What can I do for you? Tell me, pray, what is your need today?'}
]
# Load the initial memory into the chat memory
memory.load(initial_memory)

def format_search_results(search_results: List[SearxNGSearchTool.output_schema]) -> str:
    formatted_results = []
    for idx, result in enumerate(search_results):
        formatted_results.append(f"{idx+1}. {result.title} - {result.content}")
    return "\n".join(formatted_results)

class ArticleOutlineGenAgentConfig(BaseChatAgentConfig):
    pass

class ArticleOutlineGenAgent(BaseChatAgent):
    def _pre_run(self):
        # For ease of demonstration, we will pass the client        
        self.memory.add_message('assistant', 'First, I will ask the deep research agent to generate a list of deep research queries.')
        response = self.get_response(response_model=DeepQueryAgentInputSchema)
        deep_queries = deep_query_agent.run(response.user_input)
        self.memory.add_message('system', f'Queries: {deep_queries}')
        search_results = search_tool.run(deep_queries)
        formatted_results = format_search_results(search_results.results)
        self.memory.add_message('system', f'Search results:\n{formatted_results}')
        self.memory.add_message('assistant', 'I have gathered the search results and will now generate an article outline based on the information.')
        return
        

# Create a chat agent with the specified model, system prompt generator, and memory
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
agent = ArticleOutlineGenAgent(
    config=ArticleOutlineGenAgentConfig(
        client=instructor.from_openai(openai.OpenAI()), 
        system_prompt_generator=system_prompt_generator,
        model='gpt-3.5-turbo',
        memory=memory,
        output_schema=ArticleOutline
    )
)


############################################################################################################
# Main chat loop for testing the chat agent
############################################################################################################
console = Console()
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['/exit', '/quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    response_dict = response.dict()

    def format_markdown_section(title, items):
        if isinstance(items, list):
            return f"## {title}\n" + "\n".join([f"- {item['title']}: {item['content']}" for item in items]) + "\n"
        return f"## {title}\n{items}\n"

    markdown_string = f"# {response_dict['title']}\n"
    for section in response_dict['sections']:
        markdown_string += format_markdown_section(section['title'], section['subsections'])

    markdown_response = Markdown(markdown_string)
    console.print(markdown_response)