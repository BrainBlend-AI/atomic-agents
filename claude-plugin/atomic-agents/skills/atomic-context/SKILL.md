---
description: This skill should be used when the user asks to "create context provider", "dynamic context", "inject context", "BaseDynamicContextProvider", "share data between agents", or needs guidance on context providers, dynamic prompt injection, and sharing information across agents in Atomic Agents applications.
---

# Atomic Agents Context Providers

Context providers dynamically inject information into agent system prompts at runtime. They enable agents to access current data without modifying the base prompt.

## Core Concept

```
┌─────────────────────────────────────────────────────────┐
│                   System Prompt                         │
├─────────────────────────────────────────────────────────┤
│ Background: [static content]                            │
│ Steps: [static content]                                 │
│ Output Instructions: [static content]                   │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Dynamic Context:                                    │ │
│ │ - User Context: Current user is Alice               │ │
│ │ - RAG Context: [retrieved documents]                │ │
│ │ - Time Context: Current time is 2025-01-15          │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Basic Context Provider

```python
from atomic_agents.lib.components.system_prompt_generator import BaseDynamicContextProvider

class UserContextProvider(BaseDynamicContextProvider):
    """Provides current user information to the agent."""

    def __init__(self):
        super().__init__(title="User Context")
        self.user_name: str = ""
        self.user_role: str = ""

    def get_info(self) -> str:
        if not self.user_name:
            return "No user logged in."
        return f"Current user: {self.user_name} (Role: {self.user_role})"
```

## Registering Providers

```python
from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig

# Create agent
agent = AtomicAgent[InputSchema, OutputSchema](config=config)

# Create and register provider
user_provider = UserContextProvider()
agent.register_context_provider("user", user_provider)

# Update context before running
user_provider.user_name = "Alice"
user_provider.user_role = "Admin"

# Run agent - system prompt now includes user context
output = agent.run(input_data)
```

## Common Context Provider Patterns

### RAG Context Provider
```python
class RAGContextProvider(BaseDynamicContextProvider):
    """Provides retrieved documents to the agent."""

    def __init__(self):
        super().__init__(title="Retrieved Documents")
        self.documents: list[dict] = []

    def set_documents(self, docs: list[dict]):
        """Set retrieved documents."""
        self.documents = docs

    def get_info(self) -> str:
        if not self.documents:
            return "No relevant documents found."

        sections = []
        for i, doc in enumerate(self.documents, 1):
            sections.append(f"Document {i}:\n{doc['content']}\nSource: {doc['source']}")

        return "\n\n".join(sections)


# Usage
rag_provider = RAGContextProvider()
agent.register_context_provider("rag", rag_provider)

# Before each query, update with relevant docs
relevant_docs = vector_db.search(query)
rag_provider.set_documents(relevant_docs)
output = agent.run(query_input)
```

### Time Context Provider
```python
from datetime import datetime

class TimeContextProvider(BaseDynamicContextProvider):
    """Provides current time information."""

    def __init__(self):
        super().__init__(title="Current Time")

    def get_info(self) -> str:
        now = datetime.now()
        return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
```

### Session Context Provider
```python
class SessionContextProvider(BaseDynamicContextProvider):
    """Provides session-specific context."""

    def __init__(self):
        super().__init__(title="Session Context")
        self.session_data: dict = {}

    def set(self, key: str, value: str):
        self.session_data[key] = value

    def get_info(self) -> str:
        if not self.session_data:
            return "No session context available."

        lines = [f"- {k}: {v}" for k, v in self.session_data.items()]
        return "Session information:\n" + "\n".join(lines)
```

### Database Context Provider
```python
class DatabaseContextProvider(BaseDynamicContextProvider):
    """Provides database schema or recent data."""

    def __init__(self, db_connection):
        super().__init__(title="Database Context")
        self.db = db_connection
        self._cache = None
        self._cache_time = None

    def get_info(self) -> str:
        # Cache for 5 minutes
        if self._cache and (time.time() - self._cache_time) < 300:
            return self._cache

        tables = self.db.get_table_names()
        schema_info = []
        for table in tables:
            columns = self.db.get_columns(table)
            schema_info.append(f"Table: {table}\n  Columns: {', '.join(columns)}")

        self._cache = "Database Schema:\n" + "\n".join(schema_info)
        self._cache_time = time.time()
        return self._cache
```

## Managing Providers

```python
# Register
agent.register_context_provider("name", provider)

# Unregister
agent.unregister_context_provider("name")

# Check if registered
if "name" in agent.context_providers:
    print("Provider is registered")
```

## Sharing Context Between Agents

```python
# Create shared provider
shared_context = SharedContextProvider()

# Register with multiple agents
agent1.register_context_provider("shared", shared_context)
agent2.register_context_provider("shared", shared_context)

# Update once, both agents see the change
shared_context.update_data(new_data)
```

## Context Provider Best Practices

1. **Keep get_info() fast** - It's called on every agent.run()
2. **Cache when appropriate** - Avoid repeated expensive operations
3. **Return strings** - get_info() must return a string
4. **Use descriptive titles** - Title appears in system prompt
5. **Handle empty state** - Return helpful message when no data
6. **Update before run** - Set context before calling agent.run()
7. **Don't block** - Use async providers for slow operations

## Advanced: Async Context Provider

For providers that need async data fetching:

```python
class AsyncContextProvider(BaseDynamicContextProvider):
    def __init__(self):
        super().__init__(title="Async Data")
        self._cached_data = ""

    async def refresh(self):
        """Call this before agent.run_async()"""
        data = await fetch_external_data()
        self._cached_data = format_data(data)

    def get_info(self) -> str:
        return self._cached_data

# Usage
await context_provider.refresh()
output = await agent.run_async(input_data)
```

## References

See `references/` for:
- `rag-patterns.md` - RAG context provider patterns
- `caching-strategies.md` - Context caching approaches

See `examples/` for:
- `user-context.py` - User session provider
- `rag-context.py` - Document retrieval provider
