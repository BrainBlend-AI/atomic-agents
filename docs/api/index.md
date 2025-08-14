# API Reference

This section contains the API reference for all public modules and classes in Atomic Agents.

```{toctree}
:maxdepth: 2
:caption: API Reference

agents
context
utils
```

## Core Components

The Atomic Agents framework is built around several core components that work together to provide a flexible and powerful system for building AI agents.

### Agents

The agents module provides the base classes for creating AI agents:

- `AtomicAgent`: The foundational agent class that handles interactions with LLMs
- `AgentConfig`: Configuration class for customizing agent behavior
- `BasicChatInputSchema`: Standard input schema for agent interactions
- `BasicChatOutputSchema`: Standard output schema for agent responses

[Learn more about agents](agents.md)

### Context Components

The context module contains essential building blocks:

- `ChatHistory`: Manages conversation history and state with support for:
  - Message history with role-based messages
  - Turn-based conversation tracking
  - Multimodal content
  - Serialization and persistence
  - History size management

- `SystemPromptGenerator`: Creates structured system prompts with:
  - Background information
  - Processing steps
  - Output instructions
  - Dynamic context through context providers

- `BaseDynamicContextProvider`: Base class for creating custom context providers that can inject dynamic information into system prompts

[Learn more about context components](context.md)

### Utils

The utils module provides helper functions and utilities:

- Message formatting
- Tool response handling
- Schema validation
- Error handling

[Learn more about utilities](utils.md)

## Getting Started

For practical examples and guides on using these components, see:

- [Quickstart Guide](../guides/quickstart.md)
- [Tools Guide](../guides/tools.md)
