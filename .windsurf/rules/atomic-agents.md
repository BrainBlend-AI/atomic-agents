---
trigger: always_on
---

Atomic Agents monorepo — lightweight Python framework for modular AI agents (Pydantic + Instructor).

## Structure
- `atomic-agents/` — core library (`pip install atomic-agents`)
- `atomic-assembler/` — CLI tool
- `atomic-examples/` — example projects
- `atomic-forge/` — downloadable tools

## Development
- Package manager: uv (never pip)
- `uv sync` — install deps
- `uv run pytest --cov=atomic_agents atomic-agents` — tests
- `uv run black atomic-agents atomic-assembler atomic-examples atomic-forge` — format (line-length=127)
- `uv run flake8 --extend-exclude=.venv atomic-agents atomic-assembler atomic-examples atomic-forge` — lint

## Conventions
- Python 3.12+, Black + Flake8, line-length=127
- Pydantic v2 (`BaseIOSchema`) for all agent I/O — no raw dicts
- Branch: `main` only
- Composition over inheritance; all control flow in Python
