# Advanced Usage

This guide covers advanced features and patterns in Atomic Agents.

## Custom Schemas

You can create custom input/output schemas for specialized agents:

```python
from typing import List
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

# Custom output schema
class CustomOutputSchema(BaseIOSchema):
    """Schema for responses with suggested follow-up questions."""

    chat_message: str = Field(
        ...,
        description="The chat message exchanged between the user and the chat agent.",
    )
    suggested_user_questions: List[str] = Field(
        ...,
        description="A list of suggested follow-up questions the user could ask the agent.",
    )

# Initialize memory with custom schema
initial_message = CustomOutputSchema(
    chat_message="Hello! How can I assist you today?",
    suggested_user_questions=[
        "What can you do?",
        "Tell me a joke",
        "Tell me about how you were made"
    ]
)
memory.add_message("assistant", initial_message)

# Create agent with custom schema
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
        output_schema=CustomOutputSchema
    )
)
```

## RAG Implementation

Here's how to implement a Retrieval-Augmented Generation (RAG) system with two specialized agents:

```python
import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Query Agent for generating semantic search queries
class RAGQueryAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG query agent."""
    user_message: str = Field(
        ...,
        description="The user's question or message to generate a semantic search query for"
    )

class RAGQueryAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG query agent."""
    query: str = Field(
        ...,
        description="The semantic search query to use for retrieving relevant chunks"
    )

query_agent = BaseAgent(
    BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert at formulating semantic search queries for RAG systems.",
                "Your role is to convert user questions into effective semantic search queries that will retrieve the most relevant text chunks.",
            ],
            steps=[
                "1. Analyze the user's question to identify key concepts and information needs",
                "2. Reformulate the question into a semantic search query that will match relevant content",
                "3. Ensure the query captures the core meaning while being general enough to match similar content",
            ],
            output_instructions=[
                "Generate a clear, concise semantic search query",
                "Focus on key concepts and entities from the user's question",
                "Avoid overly specific details that might miss relevant matches",
                "Include synonyms or related terms when appropriate",
                "Explain your reasoning for the query formulation",
            ],
        ),
        input_schema=RAGQueryAgentInputSchema,
        output_schema=RAGQueryAgentOutputSchema,
    )
)

# QA Agent for answering questions using retrieved context
class RAGQuestionAnsweringAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG QA agent."""
    question: str = Field(
        ...,
        description="The user's question to answer"
    )

class RAGQuestionAnsweringAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG QA agent."""
    answer: str = Field(
        ...,
        description="The answer to the user's question based on the retrieved context"
    )

qa_agent = BaseAgent(
    BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert at answering questions using retrieved context chunks from a RAG system.",
                "Your role is to synthesize information from the chunks to provide accurate, well-supported answers.",
                "You must explain your reasoning process before providing the answer.",
            ],
            steps=[
                "1. Analyze the question and available context chunks",
                "2. Identify the most relevant information in the chunks",
                "3. Explain how you'll use this information to answer the question",
                "4. Synthesize information into a coherent answer",
            ],
            output_instructions=[
                "First explain your reasoning process clearly",
                "Then provide a clear, direct answer based on the context",
                "If context is insufficient, state this in your reasoning",
                "Never make up information not present in the chunks",
                "Focus on being accurate and concise",
            ],
        ),
        input_schema=RAGQuestionAnsweringAgentInputSchema,
        output_schema=RAGQuestionAnsweringAgentOutputSchema,
    )
)
```

## Streaming with Rich Display

Handle streaming responses with rich formatting:

```python
from rich.live import Live
from rich.text import Text
from typing import List

async def process_stream():
    with Live("", refresh_per_second=10, auto_refresh=True) as live:
        current_response = ""
        current_questions: List[str] = []

        async for partial_response in agent.run_async(input_schema):
            if hasattr(partial_response, "chat_message") and partial_response.chat_message:
                # Update message if changed
                if partial_response.chat_message != current_response:
                    current_response = partial_response.chat_message

                # Update questions if available
                if hasattr(partial_response, "suggested_user_questions"):
                    current_questions = partial_response.suggested_user_questions

                # Build display text
                display_text = Text.assemble(
                    ("Agent: ", "bold green"),
                    (current_response, "green")
                )

                # Add questions if we have them
                if current_questions:
                    display_text.append("\n\n")
                    display_text.append(
                        "Suggested questions you could ask:\n",
                        style="bold cyan"
                    )
                    for i, question in enumerate(current_questions, 1):
                        display_text.append(f"{i}. {question}\n", style="cyan")

                live.update(display_text)

# Run with asyncio
import asyncio
asyncio.run(process_stream())
```

## Best Practices

### Error Handling

```python
try:
    response = agent.run(input_schema)
except openai.APIError as e:
    console.print(f"[red]API Error:[/red] {e}")
    # Handle API-specific errors
except Exception as e:
    console.print(f"[red]Error:[/red] {e}")
    # Handle other errors appropriately
```

### Memory Management

```python
# Initialize memory with context
memory = AgentMemory()

# Add system context
memory.add_message(
    "system",
    "Important context or instructions for the agent..."
)

# Add initial message
memory.add_message("assistant", initial_message)

# Clear memory if needed
memory.clear()
```

### Security

```python
# Use environment variables for sensitive data
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable "
        "or in the environment variable OPENAI_API_KEY."
    )
```

## Troubleshooting
