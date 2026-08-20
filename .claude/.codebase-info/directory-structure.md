# Directory Structure

*Last Updated: 2026-08-20*

## Root Layout

```
atomic-agents/                  # repo root (uv workspace)
├── atomic-agents/              # CORE framework project (PyPI: atomic-agents)
│   └── atomic_agents/          #   import package
│       ├── agents/             #     AtomicAgent, AgentConfig
│       ├── base/               #     BaseIOSchema, BaseTool, BaseResource, BasePrompt, VideoURL
│       ├── context/            #     SystemPromptGenerator, BaseChatHistory/ChatHistory, context providers
│       ├── connectors/mcp/     #     Model Context Protocol integration
│       └── utils/              #     token counter, tool-message formatting
│   └── tests/                  #   pytest suite (agents/, base/, context/, connectors/, utils/; VideoURL tests in base/)
├── atomic-assembler/           # Textual TUI + noninteractive `atomic` Forge client
│   └── atomic_assembler/       #   main.py, source/index/download utilities, TUI screens/widgets
├── atomic-forge/               # vendored-code tool registry (NOT a package)
│   ├── tools/<tool>/           #   standalone package: tool/, tests/, pyproject.toml, requirements.txt
│   ├── conformance/            #   registry package-contract test suite
│   ├── scripts/                #   deterministic index generator
│   ├── index.json              #   generated tool catalog
│   └── guides/                 #   tool authoring guides
├── atomic-examples/            # 16 runnable example apps (each its own project)
├── claude-plugin/atomic-agents/ # AI-assistant plugin: 8 skills + 2 subagents (Claude Code plugin,
│                               #   also installable cross-tool via `npx skills add eigenwise/atomic-agents`)
├── .claude-plugin/             # marketplace.json — plugin marketplace manifest (drives npx skills discovery)
├── docs/                       # Sphinx + MyST documentation (api/, guides/, examples/)
├── guides/                     # DEV_GUIDE.md and contributor guides
├── scripts/                    # generate_llms_files.py (llms.txt index + llms-*.txt bundles)
├── pyproject.toml              # package metadata, deps, [tool.black], uv workspace
├── pyrightconfig.json          # Pyright configuration for the uv-managed `.venv`
├── context7.json               # Context7 indexing config + v2 API rules for AI assistants
├── build_and_deploy.ps1        # version bump + uv build/publish
├── AGENTS.md                   # the project's own design philosophy (imported by CLAUDE.md)
└── README.md
```

## Key Directories

### `atomic-agents/atomic_agents/` (core)
The framework itself. `agents/atomic_agent.py` is the heart (`AtomicAgent`). `base/` holds the
Pydantic-based contracts every agent/tool/resource/prompt implements. `context/` assembles system
prompts and stores conversation history. `connectors/mcp/` bridges to MCP servers. `utils/` does
token accounting via LiteLLM.

### `atomic-assembler/atomic_assembler/`
The `atomic` entry point runs the Textual UI with no subcommand and supports scripting with `list`,
`download`, and `sources` subcommands. Source utilities clone configured Git repositories, resolve an
indexed package only inside the configured tools directory, and copy the full standalone package into the
user’s project. Source/index metadata is treated as untrusted before it reaches the terminal or filesystem.

### `atomic-forge/`
A shadcn-style collection of 13 self-contained tool packages. Each package contains `tool/<name>.py`
(Input/Output `BaseIOSchema`, `BaseToolConfig`, `BaseTool`), tests, `pyproject.toml`, and
`requirements.txt`; those files stay with the package when it is downloaded. `index.json` is generated
from each package’s metadata, and `conformance/` plus CI enforce the registry contract.

### `atomic-examples/`
16 standalone example apps (`quickstart`, `rag-chatbot`, `deep-research`, `web-search-agent`,
`mcp-agent`, `fastapi-memory`, `persistent-memory`, `youtube-summarizer`, …), each with its own
`pyproject.toml`. These are excluded from the workspace build.

### `docs/` and `guides/`
`docs/` is a Sphinx + MyST site (`api/` reference, `guides/`, `examples/`, `conf.py`), deployed to
GitHub Pages. `guides/DEV_GUIDE.md` is the contributor setup/workflow guide.
