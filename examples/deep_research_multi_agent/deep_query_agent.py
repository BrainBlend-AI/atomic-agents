###############################
# WARNING: NOT YET FINISHED!  #
###############################

from datetime import datetime
import os

from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown

import instructor
import openai

from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator, SystemPromptInfo
from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig

# Initialize tools
search_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=15))

class CurrentDateProvider(SystemPromptContextProviderBase):
    def __init__(self, format: str = '%Y-%m-%d %H:%M:%S', title: str = 'Current date'):
        super().__init__(title=title)
        self.format = format

    def get_info(self) -> str:
        return f'The current date, in the format "{self.format}", is {datetime.now().strftime(self.format)}'

system_prompt_generator = SystemPromptGenerator(SystemPromptInfo(
    background=[
        'This assistant is specialized in generating deep research queries to help users find the information they need.',
    ],
    steps=[
        'First, generate generic queries to get a broad overview of the topic and do a web search',
        'Based on the content of the initial search results, generate a series of deep research queries to explore the topic in more depth and provide a comprehensive overview of the topic and related topics.',
        'Return this second set of queries to the user for further exploration.'
    ],
    output_instructions=[
        'Each query should be well-structured and focused on a specific topic.',
        'Ensure that the queries are clear and concise to help the user find the information they need.',
        'Each query must be diverse yet relevant to the user\'s needs, providing a comprehensive overview of the topic and related topics.'
    ],
    context_providers={
        'date': CurrentDateProvider(title='Current date', format='%Y-%m-%d %H:%M:%S')
    }
))

class DeepQueryAgentInputSchema(BaseModel):
    user_input: str = Field(..., description='The user input to generate deep research queries based on.')
    
    class Config:
        title = 'DeepQueryAgentInputSchema'
        description = 'The input schema for the DeepQueryAgent.'
        json_schema_extra = {
            title: 'DeepQueryAgentInputSchema',
            description: 'The input schema for the DeepQueryAgent.'
        }

class DeepQueryAgentConfig(BaseChatAgentConfig):
    search_tool_instance: BaseTool

class DeepQueryAgent(BaseChatAgent):
    def __init__(self, config: DeepQueryAgentConfig):
        super().__init__(config)
        self.search_tool = config.search_tool_instance
        
    def _get_and_handle_response(self):
        """
        Handles obtaining and processing the response.

        Returns:
            Type[BaseModel]: The processed response.
        """
        self.memory.add_message('assistant', 'First, I will generate 3 generic queries to get a broad overview of the topic.')
        initial_response = self.get_response(response_model=self.output_schema)
        search_results = self.search_tool.run(initial_response)
        self.memory.add_message(
            'assistant', (
                'Here are the search results based on the initial response:\n'
                f'{search_results}\n\n'
                '==========='
                'Now, I will generate a series of 7 deep diverse and detailed research queries based on the initial search results to explore the topic and closely related topics in more depth.'
            )
        )
        deep_queries = self.get_response(response_model=self.output_schema)
        return deep_queries

# Initialize the BaseChatAgent with the configured client, system prompt generator, and search toool schema.
deep_query_agent = DeepQueryAgent(
    config=DeepQueryAgentConfig(
        client=instructor.from_openai(openai.OpenAI()), 
        system_prompt_generator=system_prompt_generator,
        model='gpt-3.5-turbo',
        output_schema=search_tool.input_schema,
        search_tool_instance=search_tool
    )
)
        
if __name__ == "__main__":
    # We can test the agent by running a topic through it and observing the generated queries.
    console = Console()
    output = deep_query_agent.run('What are the benefits of exercise?')
    console.print(output)
    