---
description: This skill should be used when the user asks to "create an agent", "configure AtomicAgent", "set up agent", "agent configuration", "AgentConfig", "ChatHistory", or needs guidance on agent initialization, model selection, history management, and agent execution patterns for Atomic Agents applications.
---

# Atomic Agents Agent Configuration

The `AtomicAgent` is the core class for LLM interactions in the Atomic Agents framework. It handles structured input/output, conversation history, and system prompt management.

## Basic Agent Setup

```python
import instructor
import openai
from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory

# 1. Create instructor-wrapped client
client = instructor.from_openai(openai.OpenAI())

# 2. Configure the agent
config = AgentConfig(
    client=client,
    model="gpt-4o-mini",
    history=ChatHistory(),
    system_prompt_generator=SystemPromptGenerator(
        background=["You are an expert assistant."],
        steps=["1. Analyze the input.", "2. Generate response."],
        output_instructions=["Be concise and helpful."],
    ),
)

# 3. Create the agent with type parameters
agent = AtomicAgent[InputSchema, OutputSchema](config=config)
```

## AgentConfig Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client` | Instructor client | Yes | Instructor-wrapped LLM client |
| `model` | str | Yes | Model identifier (e.g., "gpt-4o-mini") |
| `history` | ChatHistory | No | Conversation history manager |
| `system_prompt_generator` | SystemPromptGenerator | No | System prompt configuration |
| `input_schema` | BaseIOSchema | No | Override input schema |
| `output_schema` | BaseIOSchema | No | Override output schema |
| `model_api_parameters` | dict | No | Additional API parameters |

## LLM Provider Setup

### OpenAI
```python
import instructor
import openai

client = instructor.from_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
model = "gpt-4o-mini"  # or "gpt-4o", "gpt-4-turbo"
```

### Anthropic
```python
import instructor
import anthropic

client = instructor.from_anthropic(anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")))
model = "claude-sonnet-4-20250514"
```

### Groq
```python
import instructor
from groq import Groq

client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")), mode=instructor.Mode.JSON)
model = "llama-3.1-70b-versatile"
```

### Ollama (Local)
```python
import instructor
import openai

client = instructor.from_openai(
    openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
)
model = "llama3.1"
```

## Agent Execution Methods

### Synchronous
```python
output = agent.run(InputSchema(message="Hello"))
```

### Asynchronous
```python
output = await agent.run_async(InputSchema(message="Hello"))
```

### Streaming (Sync)
```python
for partial in agent.run_stream(InputSchema(message="Hello")):
    print(partial)  # Partial responses as they arrive
```

### Streaming (Async)
```python
async for partial in agent.run_async_stream(InputSchema(message="Hello")):
    print(partial)
```

## ChatHistory Management

```python
from atomic_agents.lib.components.chat_history import ChatHistory

# Create history
history = ChatHistory()

# Use with agent
config = AgentConfig(client=client, model=model, history=history)
agent = AtomicAgent[InputSchema, OutputSchema](config=config)

# Run multiple turns (history accumulates)
agent.run(InputSchema(message="Hello"))
agent.run(InputSchema(message="Tell me more"))

# Reset history
agent.reset_history()

# Save/load history
history_data = history.to_dict()
new_history = ChatHistory.from_dict(history_data)
```

## Context Providers

Dynamic context injection into system prompts:

```python
from atomic_agents.lib.components.system_prompt_generator import BaseDynamicContextProvider

class UserContextProvider(BaseDynamicContextProvider):
    def __init__(self):
        super().__init__(title="User Context")
        self.user_name = ""

    def get_info(self) -> str:
        return f"Current user: {self.user_name}"

# Register with agent
provider = UserContextProvider()
agent.register_context_provider("user", provider)

# Update context dynamically
provider.user_name = "Alice"
agent.run(input_data)  # System prompt now includes user context
```

## Token Counting

```python
# Get token usage
token_info = agent.get_context_token_count()

print(f"Total: {token_info.total}")
print(f"System prompt: {token_info.system_prompt}")
print(f"History: {token_info.history}")
print(f"Utilization: {token_info.utilization:.1%}")
```

## Hooks for Monitoring

```python
def on_response(response):
    print(f"Got response: {response}")

def on_error(error):
    print(f"Error: {error}")

agent.register_hook("completion:response", on_response)
agent.register_hook("completion:error", on_error)
agent.register_hook("parse:error", on_error)
```

Hook events:
- `completion:kwargs` - Before API call
- `completion:response` - After successful response
- `completion:error` - On API error
- `parse:error` - On parsing/validation error

## Model API Parameters

Pass additional parameters to the LLM:

```python
config = AgentConfig(
    client=client,
    model="gpt-4o",
    model_api_parameters={
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.9,
    },
)
```

## Best Practices

1. **Always wrap with instructor** - Required for structured outputs
2. **Use environment variables** - Never hardcode API keys
3. **Initialize history when needed** - Only if conversation state matters
4. **Type your agents** - `AtomicAgent[Input, Output]` for type safety
5. **Use streaming for long responses** - Better user experience
6. **Monitor with hooks** - Track errors and performance
7. **Reset history appropriately** - Prevent context overflow

## References

See `references/` for:
- `multi-provider.md` - Detailed provider configurations
- `async-patterns.md` - Async and streaming patterns

See `examples/` for:
- `basic-agent.py` - Minimal agent setup
- `streaming-agent.py` - Streaming implementation
