import json
import random
import instructor
import openai
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase
from atomic_agents.agents.base_chat_agent import BaseChatAgentConfig, BaseChatAgent

class SharedContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title):
        super().__init__(title)
        self.shared_context = {}

    def get_info(self) -> str:
        # Here you can do something with the shared context to display it, to keep it simple we will just turn it into JSON
        return json.dumps(self.shared_context)

    def update_context(self, key: str, value: str):
        self.shared_context[key] = value

# Define two simple agents with shared context
agent_one = BaseChatAgent(
    config=BaseChatAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model='gpt-3.5-turbo',
    )
)

agent_two = BaseChatAgent(
    config=BaseChatAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model='gpt-3.5-turbo',
    )
)
agent_two.system_prompt_generator.system_prompt_info.output_instructions.append('Always respond in a beautiful poetic rhyming verse.')

# Define a context provider that will be shared between the two agents
shared_context_provider = SharedContextProvider('Shared Context Provider')

agent_one.register_context_provider('shared_context', shared_context_provider)
agent_two.register_context_provider('shared_context', shared_context_provider)

# Function to update context with a random number and query both agents
def query_agents_with_random_number():
    random_number = random.randint(1, 100)
    shared_context_provider.update_context('random_number', str(random_number))
    print(f'Updated shared context with random number: {random_number}')

    # Get responses from both agents
    response_one = agent_one.run(agent_one.input_schema(chat_input="What is the random number?"))
    response_two = agent_two.run(agent_two.input_schema(chat_input="What is the random number?"))

    print(f'Agent One: {response_one.response}')
    print(f'Agent Two: {response_two.response}')

if __name__ == "__main__":
    query_agents_with_random_number()