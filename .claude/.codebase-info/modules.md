# Key Modules

*Last Updated: 2026-08-11*

## Core framework — `atomic-agents/atomic_agents/`

### agents
- **Location:** `atomic-agents/atomic_agents/agents/atomic_agent.py`
- **Purpose:** The `AtomicAgent[InputSchema, OutputSchema]` class and `AgentConfig`. Orchestrates the
  run lifecycle (sync / stream / async), context-provider registration, hook registration, and
  context-window trimming.
- **Exposes:** `AtomicAgent`, `AgentConfig`, `BasicChatInputSchema`, `BasicChatOutputSchema`.
- **Depends on:** `base/`, `context/`, `utils/`, `instructor`.

### base
- **Location:** `atomic-agents/atomic_agents/base/`
- **Purpose:** The typed contracts everything else implements.
- **Key files:** `base_io_schema.py` (`BaseIOSchema` — Pydantic base; non-empty docstring enforced and
  used as the schema description), `base_tool.py` (`BaseTool[In, Out]`, `BaseToolConfig`),
  `base_resource.py` (`BaseResource`), `base_prompt.py` (`BasePrompt`), and `multimodal.py`
  (`VideoURL` — OpenAI-compatible `video_url` content-part model for video inputs).
- **Exposes via package root:** `BaseIOSchema`, `BaseTool`, `BaseToolConfig`, `VideoURL`.

### context
- **Location:** `atomic-agents/atomic_agents/context/`
- **Purpose:** System-prompt assembly and conversation memory.
- **Key files:** `system_prompt_generator.py` (`SystemPromptGenerator`, `BaseDynamicContextProvider`),
  `base_chat_history.py` (`BaseChatHistory` — interface-only ABC declaring the memory contract
  `AtomicAgent` depends on; the pluggable seam for custom/persistent backends),
  `chat_history.py` (`ChatHistory`, `Message` — the built-in in-memory implementation of
  `BaseChatHistory`: multimodal Image/Audio/PDF plus `VideoURL`, turn grouping, `dump()`/`load()`
  serialization).
- **Note:** `AgentConfig.history` is typed to `BaseChatHistory`, so any conforming backend drops in.

### connectors/mcp
- **Location:** `atomic-agents/atomic_agents/connectors/mcp/`
- **Purpose:** Model Context Protocol integration — expose MCP server tools/resources/prompts as
  Atomic Agents components.
- **Exposes:** `MCPFactory`, `MCPDefinitionService`, `SchemaTransformer`,
  `fetch_mcp_tools` / `fetch_mcp_resources` / `fetch_mcp_prompts` (sync + async).

### utils
- **Location:** `atomic-agents/atomic_agents/utils/`
- **Key files:** `token_counter.py` (`TokenCounter` via LiteLLM; `get_context_token_count`),
  `format_tool_message.py`.

## Subprojects

### atomic-assembler (CLI)
- **Location:** `atomic-assembler/atomic_assembler/`
- **Purpose:** Textual TUI plus the `atomic` command-line client for vendoring Forge tool packages.
- **Key files:** `main.py` (argparse commands and TUI entry), `app.py` (`AtomicAssembler(App)`),
  `screens/`, `widgets/`, `utils.py` (source clone/index resolution/download), `constants.py`
  (`ForgeSource`, source validation and display safety).
- **Source model:** configured sources live in `~/.atomic-assembler/sources.json`; each source names a
  Git URL, branch, and tools directory. Git authentication stays with SSH or the user’s credential helper.

### atomic-forge (tools)
- **Location:** `atomic-forge/`
- **Purpose:** a vendored-code registry of 13 standalone tools. `index.json` is generated from package
  metadata by `scripts/generate_index.py`; `conformance/` verifies package structure and metadata.
  CI requires a fresh index and runs every tool’s test suite.
- **Authoring guide:** `atomic-forge/guides/tool_structure.md`; user-facing workflow:
  `docs/guides/atomic_forge.md`.

### atomic-examples
- **Location:** `atomic-examples/`
- **Purpose:** 16 runnable reference apps. Catalog in `entry-points.md`.
