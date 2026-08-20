# Dependencies

*Last Updated: 2026-08-20*

Declared in `pyproject.toml` (Hatchling build, `uv` workspace; versions locked in `uv.lock`).

## Runtime — core
| Package | Purpose |
|---------|---------|
| instructor (==1.14.5) | Structured (Pydantic) LLM outputs across providers — the core dependency |
| pydantic (≥2.11,<3) | Schemas / data validation for all I/O |
| litellm (≥1.50,<2) | Provider-agnostic token counting & model metadata |
| rich (≥13.7.1,<14) | Console formatting |

## Runtime — CLI / tooling
| Package | Purpose |
|---------|---------|
| textual (≥5.3,<6) | TUI framework for the `atomic` assembler |
| mcp[cli] (≥1.6) | Model Context Protocol client + CLI |
| requests (≥2.32,<3) | HTTP |
| gitpython (≥3.1.43,<4) | Clone each configured Forge source to fetch tools |
| pyyaml (≥6,<7) | Read tool `config.yaml` metadata |
| pyfiglet (≥1,<2) | ASCII-art banners in the TUI |

## Development
| Package | Purpose |
|---------|---------|
| black (≥24.8,<25) | Formatter (line length 127) |
| flake8 (≥7.1,<8) | Linter |
| pre-commit (≥4,<5) | Git hook runner |
| pytest / pytest-cov / pytest-asyncio | Tests, coverage, async tests |
| openai (≥2,<3) | Example/test provider client |

## Docs
`sphinx`, `sphinx-rtd-theme`, `myst-parser`, `sphinx-copybutton`, `sphinx-design`,
`sphinx-autobuild`, `sphinxcontrib-mermaid`, `pdoc3`, `beautifulsoup4`, `markdownify`.

## Console script
`atomic = atomic_assembler.main:main` (from `[project.scripts]`).

## Notes
- `requirements.txt` / `setup.py` are legacy shims; `pyproject.toml` + `uv.lock` are the source of truth.
- Instructor is pinned exactly (`==1.14.5`); most other deps use compatible ranges.
- Each `atomic-forge` tool and each `atomic-examples` project declares its **own** dependencies.
