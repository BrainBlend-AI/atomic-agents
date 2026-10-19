# Technology Landscape

*Last Updated: 2026-10-20*

## Source-of-Truth Files

| Information | File |
|-------------|------|
| Package metadata, deps, console scripts | `pyproject.toml` |
| Locked dependency versions | `uv.lock` |
| Legacy install shims | `setup.py`, `requirements.txt` |
| Lint | `.flake8` |
| Format + git hooks | `.pre-commit-config.yaml`, `[tool.black]` in `pyproject.toml` |
| Type checking | `pyrightconfig.json` |
| Tests | `pytest.ini`, `.coveragerc` |
| CI/CD | `.github/workflows/` |
| Release | `build_and_deploy.ps1` |
| Docs build | `docs/conf.py` |

## Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Language | Python ≥3.12 | PEP 695 generics |
| Structured LLM I/O | Instructor >=1.17.0,<2 (range in 2.13.0) | provider-agnostic structured outputs |
| Data modeling | Pydantic v2 (≥2.11.4) | all schemas are Pydantic models |
| Provider / token utils | LiteLLM (≥1.50) | token counting, model metadata |
| Tool protocol | MCP — `mcp[cli]` (≥1.8,<2) | Model Context Protocol connectors |
| TUI | Textual (≥5.3,<6) | the `atomic` assembler UI |
| Console output | Rich, pyfiglet | |
| HTTP / Git | requests, GitPython | assembler fetches forge from GitHub |
| Build backend | Hatchling | `[build-system]` |
| Workspace / lock / publish | uv | `uv sync` / `uv build` / `uv publish` |
| Static type checking | Pyright | configured for the workspace `.venv` via `pyrightconfig.json` |
| Docs | Sphinx + MyST + RTD theme | + `sphinxcontrib-mermaid`, deployed to GitHub Pages |

## Infrastructure

- **CI (GitHub Actions):**
  - `code-quality.yml` — on push/PR to `main`/`v2.0`, three jobs: `quality` (`uv sync`,
    `black --check` and `flake8` across all four project directories, a focused Pyright 1.1.414 constructor check, then
    `pytest --cov=atomic_agents` for the core); `fresh-install` (build the wheel, install
    it with the observability extra into a clean venv without the lockfile, import every module under
    `atomic_agents`, which is what a new user's `pip install` sees); `lowest-versions` (resolve runtime
    dependencies with `uv pip compile --resolution lowest-direct`, install current pytest tooling, run
    the suite, so every declared floor is a tested floor).
  - `docs.yml` — on push to `main`: build Sphinx docs, run
    `scripts/generate_llms_files.py` (spec-compliant `llms.txt` index + `llms-*.txt`
    bundles, copied to the site root), deploy to GitHub Pages. The docs version needs
    no sync step — `docs/conf.py` reads it from the root `pyproject.toml` via `tomllib`.
- **Release:** `build_and_deploy.ps1 <major|minor|patch> [--dry]` bumps the version in
  `pyproject.toml`, then `uv sync` → `uv build` → `uv publish` (requires a `PYPI_TOKEN`).
- **Distribution:** PyPI package `atomic-agents`; the `atomic` console script ships with it.
- **No runtime infrastructure** — no database, no server, no containers. It is a library + CLI.
