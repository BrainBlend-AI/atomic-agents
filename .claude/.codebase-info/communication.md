# Communication & Integrations

*Last Updated: 2026-08-20*

The framework exposes no HTTP API of its own; "communication" here means how it talks to LLM
providers and external tools.

## LLM providers (via Instructor)
- All model calls go through an **Instructor-wrapped client** the caller supplies
  (`instructor.from_openai(...)`, `from_anthropic(...)`, etc.). The agent calls
  `client.chat.completions.create(response_model=OutputSchema)` (and `create_partial` for streaming).
- Provider-agnostic: OpenAI, Anthropic, Google Gemini, MiniMax, and 100+ models via LiteLLM. Mode is
  configurable (`Mode.TOOLS` is the default).
- Multimodal content uses Instructor's Image/Audio/PDF types plus the framework's `VideoURL`;
  `ChatHistory.get_history()` converts `VideoURL` to an OpenAI-compatible `video_url` dict, which
  Instructor forwards unchanged to providers that support video inputs.
- Provider quirks live in `AgentConfig`: `system_role`, `assistant_role` (use `"model"` for Gemini),
  `tool_result_role` (auto-detected).
- Code: `atomic-agents/atomic_agents/agents/atomic_agent.py`.

## Token accounting (via LiteLLM)
- `atomic-agents/atomic_agents/utils/token_counter.py` uses LiteLLM's `token_counter` for
  provider-agnostic counts, which drive the context-window trimming in `AtomicAgent`. Video content
  parts are represented by a `[video content]` text placeholder because LiteLLM cannot count them.

## MCP — Model Context Protocol
- `atomic-agents/atomic_agents/connectors/mcp/` turns MCP server capabilities into agent
  tools/resources/prompts: `MCPFactory`, `MCPDefinitionService`, `SchemaTransformer`, and
  `fetch_mcp_tools` / `fetch_mcp_resources` / `fetch_mcp_prompts` (sync + async). See the
  `mcp-agent` and `progressive-disclosure` examples.

## Hooks / observability
- Built on Instructor's hook system: `register_hook(event, handler)`, `unregister_hook`,
  `clear_hooks`. Events include `parse:error`, `completion:kwargs`, `completion:response`,
  `token:counted`. See the `hooks-example` example and `docs/guides/hooks.md`.

## Assembler ↔ Forge sources (Git)
- A **Forge source** is a Git repository, branch, and tools directory (`ForgeSource` in
  `atomic-assembler/atomic_assembler/constants.py`). Sources are stored in
  `~/.atomic-assembler/sources.json` and default to the official
  `https://github.com/eigenwise/atomic-agents.git` on `main` when that file is absent.
- Per source, `GithubRepoCloner` clones into a temp directory via GitPython, then
  `AtomicToolManager.get_indexed_forge_tools` reads the generated `index.json` beside the tools
  directory and `copy_atomic_tool_to_destination` copies the selected package into the user's project
  (skipping `.coveragerc` and `uv.lock`). Both live in `utils.py`.
- **Authentication is out of scope by design.** The assembler stores, prompts for, and prints no
  credentials; private sources rely on the user's Git SSH keys or credential helper.
  `validate_source_url` rejects source URLs carrying userinfo, query strings, or fragments, and
  `redact_source_url` masks them in any output.
- **An index is untrusted input.** Tool paths must be relative, free of `..`, and resolve inside the
  configured tools directory; symlinks escaping the tool directory are refused before the copy; and
  every string reaching the terminal passes through `display_safe_text`, which strips ANSI/OSC escape
  sequences and control characters.
- `atomic list` reports per-source failures on stderr but still prints healthy sources, exiting
  nonzero only when every configured source fails.
