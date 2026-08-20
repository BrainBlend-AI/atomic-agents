# Coding Style

*Last Updated: 2026-08-11*

## Tooling
- **Formatter:** Black, line length **127** (`[tool.black]` in `pyproject.toml`; also a pre-commit hook).
- **Linter:** Flake8 — `.flake8` sets `max-line-length = 150`, `max-complexity = 10`, ignores
  `E203, W293, W503`, and excludes `.venv/venv/__pycache__/build/dist`. (The pre-commit Flake8 hook
  passes `--max-line-length=127` to align with Black.)
- **Pre-commit** (`.pre-commit-config.yaml`): trailing-whitespace, end-of-file-fixer, check-yaml,
  check-added-large-files, Black, Flake8.
- **CI** runs `black --check` and `flake8` across all four subprojects (`code-quality.yml`).
- **Type checker:** Pyright, configured by `pyrightconfig.json` to use the uv-managed `.venv`.

## Conventions
| Kind | Convention | Example |
|------|------------|---------|
| Modules / files | `snake_case.py` | `atomic_agent.py`, `system_prompt_generator.py` |
| Packages | `snake_case` | `atomic_agents`, `atomic_assembler` |
| Classes | `PascalCase` | `AtomicAgent`, `SystemPromptGenerator` |
| Functions / vars | `snake_case` | `register_context_provider`, `max_context_tokens` |
| I/O schemas | `<Thing>InputSchema` / `<Thing>OutputSchema` | `BasicChatInputSchema` |
| Tools / configs | `<Thing>Tool` / `<Thing>ToolConfig` | `CalculatorTool`, `CalculatorToolConfig` |

## Notes
- Target **Python ≥3.12**; use PEP 695 generics (`class AtomicAgent[In, Out]`, `AtomicAgent[A, B](...)`).
- Every `BaseIOSchema` subclass **must** have a docstring — it becomes the schema's description and is
  validated at class-definition time.
- Prefer explicit configuration objects over hidden globals.
