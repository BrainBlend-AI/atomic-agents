# Quickstart Guide

This guide will help you get started with Atomic Agents quickly through practical examples.

## Installation

1. Clone the Atomic Agents repository:

   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Install dependencies using Poetry:

   ```bash
   cd atomic-agents
   poetry install
   ```

## Basic Examples

### 1. Basic Chatbot

This example demonstrates a simple chatbot using the Atomic Agents framework:

```python
import os
import instructor
from openai import OpenAI
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

# Initialize OpenAI client
client = instructor.from_openai(OpenAI())

# Create basic configuration
config = BaseAgentConfig(
    client=client,
    model="gpt-4o-mini"
)

# Initialize agent
agent = BaseAgent(config)

# Start chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break

    response = agent.run({"chat_message": user_input})
    print(f"Assistant: {response.chat_message}")
```

### 2. Custom Chatbot

This example shows how to create a custom chatbot with a specific personality:

```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Create custom system prompt
generator = SystemPromptGenerator(
    background=[
        "You are a friendly assistant that always responds in rhyming verse.",
        "You maintain a playful and poetic tone while being helpful.",
    ],
    steps=[
        "1. Understand the user's question or request",
        "2. Formulate your response in rhyming verse",
        "3. Ensure the response is both helpful and entertaining"
    ],
    output_instructions=[
        "Always respond in rhyming verse",
        "Keep responses concise but informative",
        "Maintain a playful tone"
    ]
)

# Create agent with custom configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=generator
    )
)
```

### 3. Custom Schema

This example demonstrates using a custom output schema:

```python
from pydantic import BaseModel
from typing import List

class CustomResponseSchema(BaseModel):
    chat_message: str
    follow_up_questions: List[str]

# Create agent with custom schema
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        output_schema=CustomResponseSchema
    )
)
```

### 4. Multiple Providers

This example shows how to use different AI providers:

```python
# OpenAI
openai_client = instructor.from_openai(OpenAI())

# Groq
from groq import Groq
groq_client = instructor.from_openai(Groq())

# Ollama (for local development)
from atomic_agents.lib.providers.ollama import OllamaClient
ollama_client = instructor.from_openai(OllamaClient())

# Use any provider
agent = BaseAgent(
    config=BaseAgentConfig(
        client=openai_client,  # or groq_client, or ollama_client
        model="gpt-4o-mini"    # adjust model name based on provider
    )
)
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

1. Explore [basic concepts](basic_concepts) for deeper understanding
2. Learn about [tools and their integration](tools.md)
3. Check out [advanced usage patterns](advanced_usage)
4. Review the [API reference](../api/index) for detailed documentation
