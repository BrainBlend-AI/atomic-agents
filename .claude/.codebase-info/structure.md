# Project structure

*Last Updated: 2026-07-23*

Light notes on intent only — the actual tree is in [directory-structure.md](./directory-structure.md).

## What this project is
The Atomic Agents monorepo: a Python framework for building agentic AI apps as schema-driven,
composable components, published on PyPI as `atomic-agents`, plus its CLI, tool library, examples,
and the Claude Code plugin distributed from this repo.

## Organizing principle
uv-workspace monorepo whose **root is the published package**. Everything else (assembler, forge
tools, examples) is a workspace member that depends on the core but never the reverse.

## Where things go
| Kind of thing | Lives in | Notes |
|---------------|----------|-------|
| Framework code | `atomic-agents/atomic_agents/` | the only code that ships to PyPI |
| New forge tool | `atomic-forge/tools/<name>/` | follow `atomic-forge/guides/tool_structure.md`; NOT bundled with the package |
| New example | `atomic-examples/<name>/` | self-contained project with its own `pyproject.toml` |
| Claude Code plugin | `claude-plugin/` (+ `.claude-plugin/` manifest) | versioned separately from the PyPI package |
| Docs | `docs/` | Sphinx + MyST |

## Conventions that aren't obvious from the tree
- Tools are deliberately downloadable, not importable: never add a forge tool as a core dependency.
- The package version lives in the root `pyproject.toml`; `__version__` reads installed metadata,
  don't hardcode it anywhere.
- Every `BaseIOSchema` subclass needs a non-empty docstring — enforced at class-definition time,
  and it flows into the LLM prompt.
- Releases go through `build_and_deploy.ps1` (see the `release` skill), not manual builds.
