# Basic Concepts

This guide introduces the core concepts of Atomic Agents.

## What is an Agent?

In Atomic Agents, an agent is an autonomous entity that can:

- Process input using natural language
- Make decisions based on its configuration and context
- Execute actions through defined tools and capabilities
- Maintain state and history of interactions

## Core Components

### BaseAgent

The `BaseAgent` class is the foundation of all agents in the framework. It provides:

- Input/output schema handling
- Memory management
- System prompt generation
- Streaming capabilities
- Tool integration

### Components

Components are modular pieces that can be added to agents to extend their functionality:

#### AgentMemory

Manages conversation history and state:

```python
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgentOutputSchema
from rich.console import Console

# Initialize console for pretty outputs
console = Console()

# Initialize memory
memory = AgentMemory()

# Initialize with a greeting
initial_message = BaseAgentOutputSchema(
    chat_message="Hello! How can I assist you today?"
)
memory.add_message("assistant", initial_message)

# Add system context if needed
memory.add_message(
    "system",
    "This agent has access to specific tools and capabilities..."
)

# Access conversation history
for message in memory.get_messages():
    console.print(f"{message.role}: {message.content}")
```

#### SystemPromptGenerator

Customizes agent behavior through prompts:

```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

generator = SystemPromptGenerator(
    background=[
        "This assistant is a knowledgeable AI designed to be helpful, friendly, and informative.",
        "It specializes in providing clear explanations and step-by-step guidance.",
        "It maintains a professional yet approachable tone.",
    ],
    steps=[
        "1. Carefully analyze the user's input to understand their needs and context.",
        "2. Consider any relevant background information or previous conversation context.",
        "3. Formulate a clear, structured response that directly addresses the query.",
        "4. Include examples or analogies when they would help clarify the explanation.",
    ],
    output_instructions=[
        "Always provide clear, actionable information.",
        "Use markdown formatting for code blocks and technical terms.",
        "Break down complex concepts into digestible parts.",
        "Maintain a helpful and encouraging tone.",
    ]
)

# Use in agent configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=generator
    )
)
```

## Basic Usage Patterns

### Creating an Agent

```python
import os
import instructor
import openai
from rich.console import Console
from rich.panel import Panel
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

# Initialize console for pretty outputs
console = Console()

# API Key setup
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable "
        "or in the environment variable OPENAI_API_KEY."
    )

# OpenAI client setup
client = instructor.from_openai(openai.OpenAI(api_key=API_KEY))

# Create agent with custom configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=generator
    )
)

# Display the system prompt
default_system_prompt = agent.system_prompt_generator.generate_prompt()
console.print(Panel(default_system_prompt, width=console.width, style="bold cyan"))
```

### Running Commands

```python
from atomic_agents.agents.base_agent import BaseAgentInputSchema
from rich.text import Text
from rich.live import Live

# Simple command
input_schema = BaseAgentInputSchema(chat_message="What is the weather?")
response = agent.run(input_schema)
console.print(Text("Agent:", style="bold green"), end=" ")
console.print(Text(response.chat_message, style="green"))

# Streaming response
async def process_stream():
    with Live("", refresh_per_second=10, auto_refresh=True) as live:
        current_response = ""
        async for partial_response in agent.run_async(input_schema):
            if hasattr(partial_response, "chat_message") and partial_response.chat_message:
                if partial_response.chat_message != current_response:
                    current_response = partial_response.chat_message
                    display_text = Text.assemble(
                        ("Agent: ", "bold green"),
                        (current_response, "green")
                    )
                    live.update(display_text)

# Run with asyncio
import asyncio
asyncio.run(process_stream())
```

## Next Steps

After understanding these basic concepts, you can:

1. Explore [advanced usage patterns](advanced_usage)
2. Check out the [API Reference](/api/index) for detailed documentation
3. Try building your own custom agents

## Implementation Patterns

Atomic Agents supports several common implementation patterns for different use cases:

### Chatbots and Assistants

Create conversational agents with various capabilities:

```python
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Create memory for conversation history
memory = AgentMemory()

# Create personality
generator = SystemPromptGenerator(
    background=["You are a helpful assistant specializing in technical support."],
    steps=[
        "1. Understand the technical issue",
        "2. Ask clarifying questions if needed",
        "3. Provide step-by-step solutions"
    ]
)

# Create agent
support_agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=generator
    )
)
```

### RAG Systems

Build Retrieval-Augmented Generation systems:

```python
from atomic_agents.lib.components.rag import RAGComponent
from atomic_agents.lib.components.embeddings import EmbeddingsManager

# Initialize RAG components
embeddings = EmbeddingsManager(client=client)
rag = RAGComponent(embeddings=embeddings)

# Create RAG agent
rag_agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        components={"rag": rag}
    )
)
```
