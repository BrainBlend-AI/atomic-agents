# Onboarding

*Last Updated: 2026-07-23*

## Prerequisites
- Python **≥3.12**
- [`uv`](https://docs.astral.sh/uv/) — package & workspace manager
- An LLM API key for whatever provider you use (e.g. `OPENAI_API_KEY`); a repo-level `.env` is supported.

## Quick start
```bash
git clone https://github.com/eigenwise/atomic-agents.git
cd atomic-agents
uv sync                      # install the whole workspace (core + assembler + dev deps)
# add your API key(s) to a .env file
```
Examples are standalone projects — `cd atomic-examples/<name>` and follow that example's README to run
it. To launch the tool-installer TUI: `uv run atomic` (or `atomic` once it's on your PATH).

## Common commands
| Command | Purpose |
|---------|---------|
| `uv sync` | Install/update all workspace dependencies |
| `uv run pytest --cov=atomic_agents atomic-agents` | Run the core test suite with coverage |
| `uv run pytest atomic-assembler` | Run Atomic Assembler CLI and source-handling tests |
| `uv run pytest atomic-forge/conformance` | Verify Forge package and registry contract |
| `uv run black --check atomic-agents atomic-assembler atomic-examples atomic-forge` | Format check |
| `uv run flake8 --extend-exclude=.venv atomic-agents atomic-assembler atomic-examples atomic-forge` | Lint |
| `cd docs && uv run make html` | Build the Sphinx docs |
| `./build_and_deploy.ps1 patch --dry` | Dry-run a release (version bump + build) |

## Common tasks
- **Build a new agent:** define input/output `BaseIOSchema` subclasses, wrap an LLM client with
  Instructor, pass it to `AtomicAgent[In, Out](AgentConfig(...))`. See `patterns.md` + `entry-points.md`.
- **Use a Forge tool:** run `atomic list`, then `atomic download <name>` (or
  `atomic download <source>/<name>` for a collision). Add private Git registries with
  `atomic sources add <name> <url> --tools-path tools`.
- **Add a forge tool:** create `atomic-forge/tools/<name>/` following
  `atomic-forge/guides/tool_structure.md`, give it tests and dependency metadata, regenerate
  `atomic-forge/index.json`, then run the conformance suite.
- **Add an example:** create `atomic-examples/<name>/` with its own `pyproject.toml`.
- **Release:** `build_and_deploy.ps1 <major|minor|patch>` (needs `PYPI_TOKEN`).

## Gotchas
- The LLM client must be **Instructor-wrapped** before it goes into `AgentConfig`.
- For Gemini, set `assistant_role="model"` in `AgentConfig`.
- `__version__` is read from installed package metadata (`importlib.metadata`) — it reflects the
  installed build, not a hardcoded constant.
- Migrating from v1? See `UPGRADE_DOC.md` (renamed classes, flattened imports, schemas as generics).
