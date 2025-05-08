# Quickstart Guide

This guide will help you get started with the Atomic Agents framework. We'll cover basic usage, custom agents, and different AI providers.

## Installation

First, install the package using pip:

```bash
pip install atomic-agents
```

## Basic Chatbot

Let's start with a simple chatbot:

```python
import os
import instructor
import openai
from rich.console import Console
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema

# Initialize console for pretty outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize memory with an initial message from the assistant
initial_message = BaseAgentOutputSchema(chat_message="Hello! How can I assist you today?")
memory.add_message("assistant", initial_message)

# OpenAI client setup using the Instructor library
client = instructor.from_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

# Agent setup with specified configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",  # Using gpt-4o-mini model
        memory=memory,
    )
)

# Start a loop to handle user inputs and agent responses
while True:
    # Prompt the user for input
    user_input = console.input("[bold blue]You:[/bold blue] ")
    # Check if the user wants to exit the chat
    if user_input.lower() in ["/exit", "/quit"]:
        console.print("Exiting chat...")
        break

    # Process the user's input through the agent and get the response
    input_schema = BaseAgentInputSchema(chat_message=user_input)
    response = agent.run(input_schema)

    # Display the agent's response
    console.print("Agent: ", response.chat_message)
```

## Streaming Responses

For a more interactive experience, you can use streaming:

```python
import os
import instructor
import openai
import asyncio
from rich.console import Console
from rich.live import Live
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema

# Initialize console for pretty outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize memory with an initial message from the assistant
initial_message = BaseAgentOutputSchema(chat_message="Hello! How can I assist you today?")
memory.add_message("assistant", initial_message)

# OpenAI client setup using the Instructor library for async operations
client = instructor.from_openai(openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

# Agent setup with specified configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
    )
)

async def main():
    # Start a loop to handle user inputs and agent responses with streaming
    while True:
        # Prompt the user for input
        user_input = console.input("[bold blue]You:[/bold blue] ")
        # Check if the user wants to exit the chat
        if user_input.lower() in ["/exit", "/quit"]:
            console.print("Exiting chat...")
            break

        # Process the user's input through the agent with streaming
        input_schema = BaseAgentInputSchema(chat_message=user_input)
        
        # Stream the response
        with Live("", refresh_per_second=10, auto_refresh=True) as live:
            current_response = ""
            async for partial_response in agent.run_async(input_schema):
                if hasattr(partial_response, "chat_message") and partial_response.chat_message:
                    # Only update if we have new content
                    if partial_response.chat_message != current_response:
                        current_response = partial_response.chat_message
                        # Display the response
                        display_text = Text.assemble(("Agent: ", "bold green"), (current_response, "green"))
                        live.update(display_text)

if __name__ == "__main__":
    asyncio.run(main())
```

## Custom Chatbot

You can customize the agent's behavior using system prompts and context providers. Context providers are particularly useful for injecting dynamic information that changes between calls:

```python
from dataclasses import dataclass
from typing import List
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator,
    SystemPromptContextProviderBase
)

@dataclass
class SearchResult:
    content: str
    metadata: dict

class SearchResultsProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.results: List[SearchResult] = []

    def get_info(self) -> str:
        """Dynamically format search results for the system prompt"""
        if not self.results:
            return "No search results available."

        return "\n\n".join([
            f"Result {idx}:\nMetadata: {result.metadata}\nContent:\n{result.content}\n{'-' * 80}"
            for idx, result in enumerate(self.results, 1)
        ])

# Create prompt generator with dynamic context
prompt_generator = SystemPromptGenerator(
    background=[
        "You are an AI assistant that answers questions based on search results.",
        "Analyze the provided search results to give accurate answers."
    ],
    steps=[
        "1. Review all provided search results",
        "2. Extract relevant information",
        "3. Synthesize a comprehensive answer"
    ],
    output_instructions=[
        "Base your answer only on the provided search results",
        "Cite specific results when possible",
        "Admit when information is not found in the results"
    ],
    context_providers={
        "search_results": SearchResultsProvider("Search Results")
    }
)

# Create agent with dynamic context
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=prompt_generator
    )
)

# Example usage with dynamic updates
def process_question(question: str):
    # Perform search and get results
    results = perform_search(question)  # Your search implementation

    # Update context provider with new results
    search_provider = prompt_generator.context_providers["search_results"]
    search_provider.results = [
        SearchResult(content=result.text, metadata=result.meta)
        for result in results
    ]

    # Each call to the agent will now include the updated search results
    response = agent.run(memory=memory)
```

The key difference with context providers is that they allow you to:
- Inject dynamic information that changes between calls
- Update context (like search results, current state, etc.) without changing the base prompt
- Keep a clear separation between static prompt elements and dynamic context
- Handle potentially large or structured data in a clean way

This pattern is especially useful for:
- RAG (Retrieval Augmented Generation) systems
- Agents that need access to external data
- Stateful conversations where context changes
- Multi-step processes with varying intermediate results

## Custom Input/Output Schema

For more structured interactions, define custom schemas:

```python
import os
import instructor
import openai
from rich.console import Console
from typing import List
from pydantic import Field
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

# Initialize console for pretty outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Custom output schema
class CustomOutputSchema(BaseIOSchema):
    """This schema represents the response generated by the chat agent, including suggested follow-up questions."""

    chat_message: str = Field(
        ...,
        description="The chat message exchanged between the user and the chat agent.",
    )
    suggested_user_questions: List[str] = Field(
        ...,
        description="A list of suggested follow-up questions the user could ask the agent.",
    )

# Initialize memory with an initial message from the assistant
initial_message = CustomOutputSchema(
    chat_message="Hello! How can I assist you today?",
    suggested_user_questions=["What can you do?", "Tell me a joke", "Tell me about how you were made"],
)
memory.add_message("assistant", initial_message)

# OpenAI client setup using the Instructor library
client = instructor.from_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

# Custom system prompt
system_prompt_generator = SystemPromptGenerator(
    background=[
        "This assistant is a knowledgeable AI designed to be helpful, friendly, and informative.",
        "It has a wide range of knowledge on various topics and can engage in diverse conversations.",
    ],
    steps=[
        "Analyze the user's input to understand the context and intent.",
        "Formulate a relevant and informative response based on the assistant's knowledge.",
        "Generate 3 suggested follow-up questions for the user to explore the topic further.",
    ],
    output_instructions=[
        "Provide clear, concise, and accurate information in response to user queries.",
        "Maintain a friendly and professional tone throughout the conversation.",
        "Conclude each response with 3 relevant suggested questions for the user.",
    ],
)

# Agent setup with specified configuration and custom output schema
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=system_prompt_generator,
        memory=memory,
        output_schema=CustomOutputSchema,
    )
)

# Start a loop to handle user inputs and agent responses
while True:
    # Prompt the user for input
    user_input = console.input("[bold blue]You:[/bold blue] ")
    # Check if the user wants to exit the chat
    if user_input.lower() in ["/exit", "/quit"]:
        console.print("Exiting chat...")
        break

    # Process the user's input through the agent
    input_schema = BaseAgentInputSchema(chat_message=user_input)
    response = agent.run(input_schema)

    # Display the agent's response
    console.print("[bold green]Agent:[/bold green] ", response.chat_message)
    
    # Display the suggested questions
    console.print("\n[bold cyan]Suggested questions you could ask:[/bold cyan]")
    for i, question in enumerate(response.suggested_user_questions, 1):
        console.print(f"[cyan]{i}. {question}[/cyan]")
    console.print()  # Add an empty line for better readability

## Multiple Provider Support

The framework supports multiple AI providers:

```json
{
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "groq": "mixtral-8x7b-32768",
    "ollama": "llama3",
    "gemini": "gemini-2.0-flash-exp",
    "openrouter": "mistral/ministral-8b"
}
```

Here's how to set up clients for different providers:

```python
import os
import instructor
from rich.console import Console
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from dotenv import load_dotenv

load_dotenv()

# Initialize console for pretty outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize memory with an initial message from the assistant
initial_message = BaseAgentOutputSchema(chat_message="Hello! How can I assist you today?")
memory.add_message("assistant", initial_message)

# Function to set up the client based on the chosen provider
def setup_client(provider):
    if provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(OpenAI(api_key=api_key))
        model = "gpt-4o-mini"

    elif provider == "anthropic":
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        client = instructor.from_anthropic(Anthropic(api_key=api_key))
        model = "claude-3-5-haiku-20241022"

    elif provider == "groq":
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        client = instructor.from_groq(
            Groq(api_key=api_key),
            mode=instructor.Mode.JSON
        )
        model = "mixtral-8x7b-32768"

    elif provider == "ollama":
        from openai import OpenAI as OllamaClient
        client = instructor.from_openai(
            OllamaClient(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            ),
            mode=instructor.Mode.JSON
        )
        model = "llama3"

    elif provider == "gemini":
        from openai import OpenAI
        api_key = os.getenv("GEMINI_API_KEY")
        client = instructor.from_openai(
            OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            ),
            mode=instructor.Mode.JSON
        )
        model = "gemini-2.0-flash-exp"
        
    elif provider == "openrouter":
        from openai import OpenAI as OpenRouterClient
        api_key = os.getenv("OPENROUTER_API_KEY")
        client = instructor.from_openai(
            OpenRouterClient(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
        )
        model = "mistral/ministral-8b"

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return client, model

# Prompt for provider choice
provider = console.input("Choose a provider (openai/anthropic/groq/ollama/gemini/openrouter): ").lower()

# Set up client and model
client, model = setup_client(provider)

# Create agent with chosen provider
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model=model,
        memory=memory,
        model_api_parameters={"max_tokens": 2048}
    )
)
```

The framework supports multiple providers through Instructor:

- **OpenAI**: Standard GPT models
- **Anthropic**: Claude models
- **Groq**: Fast inference for open models
- **Ollama**: Local models (requires Ollama running)
- **Gemini**: Google's Gemini models

Each provider requires its own API key (except Ollama) which should be set in environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Groq
export GROQ_API_KEY="your-groq-key"

# Gemini
export GEMINI_API_KEY="your-gemini-key"

# OpenRouter
export OPENROUTER_API_KEY="your-openrouter-key"
```

## Running the Examples

To run any of these examples:

1. Save the code in a Python file (e.g., `chatbot.py`)
2. Set your API key as an environment variable:

   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. Run the script:

   ```bash
   poetry run python chatbot.py
   ```

## Next Steps

After trying these examples, you can:

1. Learn about [tools and their integration](tools.md)
2. Review the [API reference](../api/index) for detailed documentation
