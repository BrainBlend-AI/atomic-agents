# Agents
## Overview
In the Atomic Agents framework, an agent is a class that can interact with a user or another agent. Agents can be used to handle chat interactions, interface with tools, or perform other specialized tasks. The `BaseChatAgent` class is the base class for all chat agents, and the `ToolInterfaceAgent` class extends the `BaseChatAgent` to add tool interfacing capabilities.

## BaseChatAgent
The `BaseChatAgent` class serves two primary purposes:
1. It can be used directly to handle chat interactions.
2. It can be extended to create more specialized agents either to be re-used such as the `ToolInterfaceAgent` or to create new agents for specific tasks. For examples, see the `examples` directory.

## ToolInterfaceAgent
The `ToolInterfaceAgent` class extends the `BaseChatAgent` class to add tool interfacing capabilities. It provides a standard interface for interacting with tools such as those in the `atomic_agents.tools` package.