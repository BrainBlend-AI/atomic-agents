# API Reference

This section contains the API reference for all public modules and classes in Atomic Agents.

```{toctree}
:maxdepth: 2
:caption: API Reference

agents
components
utils
```

## Core Components

The Atomic Agents framework is built around several core components that work together to provide a flexible and powerful system for building AI agents.

### Agents

The agents module provides the base classes for creating AI agents:

- `BaseAgent`: The foundational agent class that handles interactions with LLMs
- `BaseAgentConfig`: Configuration class for customizing agent behavior
- `BaseAgentInputSchema`: Standard input schema for agent interactions
- `BaseAgentOutputSchema`: Standard output schema for agent responses

[Learn more about agents](agents.md)

### Components

The components module contains building blocks for extending agent functionality:

- `AgentMemory`: Manages conversation history and context
- `SystemPromptGenerator`: Creates dynamic system prompts
- `SystemPromptContextProvider`: Provides contextual information for prompts

[Learn more about components](components.md)

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
- [Basic Concepts](../guides/basic_concepts.md)
- [Tools Guide](../guides/tools.md)
- [Advanced Usage](../guides/advanced_usage.md)
