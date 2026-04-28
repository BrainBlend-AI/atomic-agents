Atomic Agents monorepo — lightweight Python framework for modular AI agents built on Pydantic + Instructor.

## Structure
- `atomic-agents/` — core library (`pip install atomic-agents`)
- `atomic-assembler/` — CLI (`atomic` command)
- `atomic-examples/` — runnable example projects
- `atomic-forge/` — downloadable tools (not bundled; users copy what they need)

## Development
- **Package manager**: uv only — never use pip directly
- `uv sync` — install deps
- `uv run pytest --cov=atomic_agents atomic-agents` — run tests
- `uv run black atomic-agents atomic-assembler atomic-examples atomic-forge` — format (line-length=127)
- `uv run flake8 --extend-exclude=.venv atomic-agents atomic-assembler atomic-examples atomic-forge` — lint

## Conventions
- Python 3.12+, Black + Flake8, line-length=127
- Pydantic v2 (`BaseIOSchema`) for all agent I/O — no raw dicts
- Branch: `main` only
- Composition over inheritance; no hidden abstractions; all control flow in Python
