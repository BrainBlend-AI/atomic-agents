---
description: This skill should be used when the user asks to "create project structure", "organize atomic agents project", "pyproject.toml", "project layout", "directory structure", or needs guidance on organizing files, configuring dependencies, and structuring Atomic Agents applications for maintainability.
---

# Atomic Agents Project Structure

Proper project organization is essential for maintainable Atomic Agents applications. Structure scales from simple scripts to complex multi-agent systems.

## Project Structure Patterns

### Simple Application (1-2 agents)

```
my_project/
├── pyproject.toml          # Project metadata and dependencies
├── .env                    # Environment variables (API keys)
├── .env.example            # Template for .env
├── .gitignore              # Git ignore patterns
├── README.md               # Documentation
└── my_project/
    ├── __init__.py
    ├── main.py             # Entry point
    ├── config.py           # Configuration
    └── schemas.py          # Input/output schemas
```

### Medium Application (3-5 agents with tools)

```
my_project/
├── pyproject.toml
├── .env
├── .env.example
├── .gitignore
├── README.md
└── my_project/
    ├── __init__.py
    ├── main.py             # Entry point and orchestration
    ├── config.py           # Configuration
    ├── schemas.py          # Shared schemas
    ├── agents/
    │   ├── __init__.py
    │   ├── query_agent.py  # Agent 1
    │   └── response_agent.py # Agent 2
    └── tools/
        ├── __init__.py
        ├── search_tool.py
        └── calculator_tool.py
```

### Complex Application (multi-agent with services)

```
my_project/
├── pyproject.toml
├── .env
├── .env.example
├── .gitignore
├── README.md
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_tools.py
└── my_project/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── agents/
    │   ├── __init__.py
    │   ├── query_agent.py
    │   ├── synthesis_agent.py
    │   └── validation_agent.py
    ├── tools/
    │   ├── __init__.py
    │   └── api_tool.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── inputs.py
    │   └── outputs.py
    ├── services/
    │   ├── __init__.py
    │   ├── database.py
    │   └── external_api.py
    ├── context_providers/
    │   ├── __init__.py
    │   └── rag_provider.py
    └── presentation/
        ├── __init__.py
        └── console.py
```

## pyproject.toml Template

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "An Atomic Agents application for [purpose]"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Your Name", email = "you@example.com" }]

dependencies = [
    "atomic-agents>=1.0.0",
    "instructor>=1.0.0",
    "openai>=1.0.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["my_project"]
```

## Configuration Pattern

**config.py**:
```python
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    """Get OpenAI API key from environment."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return key


@dataclass
class Config:
    """Application configuration."""

    api_key: str = None
    model: str = "gpt-4o-mini"
    max_tokens: int = 1000
    temperature: float = 0.7

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = get_api_key()


# Global config instance
config = Config()
```

## Environment Variables

**.env.example** (commit this):
```bash
# LLM Provider
OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=your-key-here

# Application Settings
MODEL=gpt-4o-mini
MAX_TOKENS=1000
TEMPERATURE=0.7

# External Services
# DATABASE_URL=postgresql://...
# REDIS_URL=redis://...
```

**.gitignore** additions:
```gitignore
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp

# Testing
.pytest_cache/
.coverage
htmlcov/
```

## Entry Point Pattern

**main.py**:
```python
"""Main entry point for the application."""

import instructor
import openai
from rich.console import Console

from .config import config
from .agents.query_agent import create_query_agent
from .schemas import UserInput

console = Console()


def main():
    """Run the application."""
    # Initialize client
    client = instructor.from_openai(openai.OpenAI(api_key=config.api_key))

    # Create agent
    agent = create_query_agent(client, config.model)

    # Main loop
    console.print("[bold green]Ready![/bold green]")
    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.lower() in ("exit", "quit"):
                break

            response = agent.run(UserInput(message=user_input))
            console.print(f"[bold green]Agent:[/bold green] {response.message}")

        except KeyboardInterrupt:
            break

    console.print("\n[yellow]Goodbye![/yellow]")


if __name__ == "__main__":
    main()
```

## Agent Module Pattern

**agents/query_agent.py**:
```python
"""Query processing agent."""

from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory

from ..schemas import QueryInput, QueryOutput


def create_query_agent(client, model: str) -> AtomicAgent[QueryInput, QueryOutput]:
    """Create and configure the query agent."""
    config = AgentConfig(
        client=client,
        model=model,
        history=ChatHistory(),
        system_prompt_generator=SystemPromptGenerator(
            background=["You are a helpful query processor."],
            steps=["1. Understand the query.", "2. Generate response."],
            output_instructions=["Be concise and helpful."],
        ),
    )
    return AtomicAgent[QueryInput, QueryOutput](config=config)
```

## File Naming Conventions

| Component | File Pattern | Class Pattern |
|-----------|--------------|---------------|
| Agents | `*_agent.py` | `*Agent` |
| Tools | `*_tool.py` | `*Tool` |
| Schemas | `schemas.py` or `*.py` | `*Schema` |
| Providers | `*_provider.py` | `*Provider` |
| Config | `config.py` | `Config`, `*Config` |
| Services | `*_service.py` | `*Service` |

## Best Practices

1. **One agent per file** - Easier to maintain and test
2. **Shared schemas in schemas.py** - Or schemas/ directory for many
3. **Factory functions** - `create_*_agent()` for configurable agents
4. **Type hints everywhere** - IDE support and documentation
5. **Docstrings** - Document purpose of each module
6. **Tests alongside code** - tests/ directory mirroring src
7. **Rich for output** - Consistent, beautiful terminal output

## References

See `references/` for:
- `testing-structure.md` - Test organization patterns
- `api-structure.md` - FastAPI integration layout

See `examples/` for:
- `minimal-project/` - Simplest structure
- `full-project/` - Complete structure template
