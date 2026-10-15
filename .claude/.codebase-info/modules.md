# Key Modules

*Last Updated: 2026-10-15*

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

### observability (opt-in)
- **Location:** `atomic-agents/atomic_agents/observability/`
- **Purpose:** OpenInference tracing for Arize Phoenix and any OpenTelemetry backend. `AtomicAgentsInstrumentor`
  (`__init__.py`, stdlib-only imports) lazily loads `openinference_tracing.py`, which patches the four
  `AtomicAgent.run*` methods into AGENT spans and every `BaseTool` subclass's `run`/`run_async`/`arun` into TOOL
  spans (existing classes via a `__subclasses__` walk, future ones via a wrapped `BaseTool.__init_subclass__`).
- **Contract:** `instrument(tracer_provider=, config=TraceConfig)` / `uninstrument()` /
  `is_instrumented_by_opentelemetry`; idempotent and fully reversible. Needs the `observability` extra
  (`openinference-instrumentation>=0.1.38`); older versions are refused with a warning so Phoenix's
  `register(auto_instrument=True)` (which loads the `openinference_instrumentor` entry point) never fails.
- **Span facts:** `agent.name` = `Class[InputSchema, OutputSchema]`; namespaced `atomic_agents.*` attributes
  (model, mode, schema names, history size, context provider names, SHA-256 of the static prompt sections);
  streams record the final/last partial and `atomic_agents.stream.closed_early`; a `ContextVar` re-entrancy guard
  keeps `run -> arun` / `to_thread` delegation to one TOOL span. Nothing in `atomic_agents/__init__.py` imports it.
- **Tests:** `atomic-agents/tests/observability/` (in-memory span exporter).

## Subprojects

### atomic-assembler (CLI)
- **Location:** `atomic-assembler/atomic_assembler/`
- **Purpose:** Textual TUI to browse and install forge tools into a user project.
- **Key files:** `main.py` (`main()`; argparse `--enable-logging`, `--version`), `app.py`
  (`AtomicAssembler(App)`), `screens/` (`main_menu`, `atomic_tool_explorer`, `file_explorer`,
  `tool_info_screen`), `widgets/`, `utils.py` (`GithubRepoCloner`, `AtomicToolManager`),
  `constants.py` (GitHub URL, `TOOLS_SUBFOLDER`).

### atomic-forge (tools)
- **Location:** `atomic-forge/tools/`
- **Purpose:** Standalone tools, each an independent mini-project following the `BaseTool` pattern,
  copied into user projects by the assembler (build files such as `pyproject.toml` / `requirements.txt`
  / `uv.lock` are skipped on copy).
- **Recent additions:** `firecrawl_search` provides web/news search; `fxmacrodata` provides economic releases, FX and COT data. Both keep their own dependencies and setup.
- **YouTube compatibility:** `youtube_transcript_scraper` uses the instance-based transcript API and converts SDK transcript objects to raw entries.
- **Authoring guide:** `atomic-forge/guides/tool_structure.md`.

### atomic-examples
- **Location:** `atomic-examples/`
- **Purpose:** 16 runnable reference apps. Catalog in `entry-points.md`.
