# Components

## Agent Memory

The `AgentMemory` class manages conversation history and state for AI agents:

```python
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

# Initialize memory with optional max messages
memory = AgentMemory(max_messages=10)

# Add messages with proper schemas
memory.add_message(
    role="assistant",
    content=BaseIOSchema(...)
)

# Access history
history = memory.get_history()

# Manage turns
memory.initialize_turn()  # Start new turn
turn_id = memory.get_current_turn_id()

# Persistence
serialized = memory.dump()  # Save to string
memory.load(serialized)    # Load from string

# Create copy
new_memory = memory.copy()
```

Key features:
- Message history management with role-based messages
- Turn-based conversation tracking
- Support for multimodal content
- Serialization and deserialization
- Memory size management
- Deep copy functionality

For full API details:
```{eval-rst}
.. automodule:: atomic_agents.lib.components.agent_memory
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index: Message.role Message.content Message.turn_id
```

## System Prompt Generator

The `SystemPromptGenerator` creates structured system prompts for AI agents:

```python
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator,
    SystemPromptContextProviderBase
)

# Create basic generator
generator = SystemPromptGenerator(
    background=[
        "You are a helpful AI assistant.",
        "You specialize in technical support."
    ],
    steps=[
        "1. Understand the user's request",
        "2. Analyze available information",
        "3. Provide clear solutions"
    ],
    output_instructions=[
        "Use clear, concise language",
        "Include step-by-step instructions",
        "Cite relevant documentation"
    ]
)

# Generate prompt
prompt = generator.generate_prompt()
```

### Context Providers

Create custom context providers by extending `SystemPromptContextProviderBase`:

```python
class CustomContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.data = {}

    def get_info(self) -> str:
        return f"Custom context: {self.data}"

# Use with generator
generator = SystemPromptGenerator(
    background=["You are a helpful AI assistant."],
    context_providers={
        "custom": CustomContextProvider("Custom Info")
    }
)
```

For full API details:
```{eval-rst}
.. automodule:: atomic_agents.lib.components.system_prompt_generator
   :members:
   :undoc-members:
   :show-inheritance:
```

## Base Components

```{eval-rst}
.. automodule:: atomic_agents.lib.base.base_tool
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index: BaseToolConfig.title BaseToolConfig.description BaseTool.input_schema BaseTool.output_schema
```

```{eval-rst}
.. automodule:: atomic_agents.lib.base.base_io_schema
   :members:
   :undoc-members:
   :show-inheritance:
```
