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
from rich.console import Console
from dotenv import load_dotenv
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory

# Load environment variables and setup
load_dotenv()
console = Console()

# Initialize memory with assistant's first message
memory = AgentMemory()
memory.add_assistant_message("Hello! I'm your AI assistant. How can I help you today?")

# Create agent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY"))),
        model="gpt-4-turbo-preview",
        model_api_parameters={"max_tokens": 2048}
    )
)

# Chat loop
while True:
    # Get user input
    user_input = console.input("[bold green]You:[/bold green] ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # Add user message to memory
    memory.add_user_message(user_input)

    # Get response from agent
    response = agent.run(memory=memory)

    # Add response to memory and display
    memory.add_assistant_message(response)
    console.print("[bold blue]Assistant:[/bold blue]", response)
```

## Streaming Responses

For a more interactive experience, you can use streaming:

```python
import os
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from dotenv import load_dotenv
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory

# Setup as before...

# Chat loop with streaming
while True:
    user_input = console.input("[bold green]You:[/bold green] ")
    if user_input.lower() in ["exit", "quit"]:
        break

    memory.add_user_message(user_input)

    # Stream the response
    with Live(console=console, refresh_per_second=4) as live:
        response = ""
        for chunk in agent.stream(memory=memory):
            response += chunk
            live.update(Markdown(f"**Assistant:** {response}"))

    memory.add_assistant_message(response)
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
        model=model,
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
from pydantic import BaseModel, Field

class CustomInput(BaseModel):
    question: str = Field(..., description="The user's question")
    context: str = Field(..., description="Additional context for the question")

class CustomOutput(BaseModel):
    answer: str = Field(..., description="The answer to the user's question")
    confidence: float = Field(..., description="Confidence score (0-1)")
    sources: list[str] = Field(default_factory=list, description="Sources used")

# Create agent with custom schema
agent = BaseAgent[CustomInput, CustomOutput](
    config=BaseAgentConfig(
        client=client,
        model=model,
        input_schema=CustomInput,
        output_schema=CustomOutput
    )
)

# Use with custom schema
result = agent.run(
    memory=memory,
    input_data=CustomInput(
        question="What is machine learning?",
        context="Explain for a beginner"
    )
)
print(f"Answer: {result.answer}")
print(f"Confidence: {result.confidence}")
print(f"Sources: {result.sources}")
```

## Linux Shell Agent

For safe execution of Linux commands through natural language, use the LinuxShellAgent:

```python
from atomic_agents.agents.linux_shell_agent import LinuxShellAgent, LinuxShellInputSchema
from atomic_agents.agents.base_agent import BaseAgentConfig

# Create Linux shell agent
agent = LinuxShellAgent(
    config=BaseAgentConfig(
        client=client,
        model=model
    )
)

# Execute commands through natural language
response = agent.run(
    LinuxShellInputSchema(
        instruction="List all Python files in the current directory",
        working_directory="/path/to/dir"  # optional
    )
)

# Access results
print(response.chat_message)  # Explanation of what was done
for output in response.command_outputs:
    print(f"Command: {output.command}")
    print(f"Output: {output.stdout}")
    if output.stderr:
        print(f"Errors: {output.stderr}")

# View command history
history = agent.get_command_history()
for entry in history:
    print(f"{'✓' if entry.success else '✗'} {entry.command}")
```

The LinuxShellAgent provides:
- Safe execution of whitelisted Linux commands
- Natural language interface to the command line
- Path validation and security checks
- Command pipeline support (e.g., `ls | grep pattern`)
- Command history tracking
- Man page integration for command help

Supported commands include: ls, cp, mv, rm, cat, grep, find, sort, wc, and more.

All commands are executed in a controlled environment with safety checks to prevent dangerous operations.

## Multiple Providers

The framework supports multiple AI providers:

```python
import os
import instructor
from rich.console import Console
from dotenv import load_dotenv
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

load_dotenv()
console = Console()

def setup_client(provider):
    if provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(OpenAI(api_key=api_key))
        model = "gpt-4-turbo-preview"

    elif provider == "anthropic":
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        client = instructor.from_anthropic(Anthropic(api_key=api_key))
        model = "claude-3-haiku-20240307"

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
            )
        )
        model = "llama2"

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
        model = "gemini-pro"

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return client, model

# Choose a provider
provider = "openai"  # or "anthropic", "groq", "ollama", "gemini"
client, model = setup_client(provider)

# Create agent with chosen provider
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model=model,
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
