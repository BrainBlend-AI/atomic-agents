# Atomic Agents Plugin for Claude Code

A Claude Code plugin that gives Claude deep, just-in-time knowledge of the [Atomic Agents](https://github.com/BrainBlend-AI/atomic-agents) Python framework. When you work on an Atomic Agents codebase, Claude picks up the right patterns for schemas, agents, tools, context providers, prompts, orchestration, and provider wiring — without you having to paste documentation or repeat conventions.

## What you get

Two skills + one subagent, loaded on demand:

- **`framework` skill** — auto-triggered when Claude sees atomic-agents code. Orients Claude on the framework and exposes eleven focused reference files (schemas, agents, tools, context providers, prompts, orchestration, memory, hooks, providers, project structure, testing). Progressive disclosure keeps the parent context lean.
- **`new-app` skill** — slash-invokable scaffolder (`/atomic-agents:new-app`). Four short questions and produces a runnable project with the right `pyproject.toml`, environment file, and first agent.
- **`atomic-reviewer` subagent** — auto-triggered (or `Task`-invoked) when you ask for a review, audit, or check of atomic-agents code. Runs in isolated context with read-only tools so the file-exploration load never pollutes the parent thread. Focuses only on framework-specific concerns (BaseIOSchema invariants, Instructor wrapping, per-provider role and mode, context-provider I/O hygiene, orchestration hazards, common API misuses). Returns a single confidence-filtered structured report. Complements generic code review; does not replace it.

This follows the hybrid pattern Anthropic themselves ship: reference skills for knowledge that should inform the main thread, specialist subagents for discrete verification tasks.

## Install

### Claude Code marketplace

```
/plugin install atomic-agents@<marketplace-name>
```

### Local

```bash
claude --plugin-dir /path/to/atomic-agents/claude-plugin/atomic-agents
```

### Validate

```bash
/plugin validate /path/to/claude-plugin/atomic-agents
```

## How it works

This plugin follows Anthropic's 2026 skill-authoring conventions:

- Each skill is a folder with a `SKILL.md` file (≤500 lines) plus an optional `references/` directory.
- YAML frontmatter has two fields: `name` and `description`. The description is what Claude reads to decide when the skill applies.
- Reference files are one level deep from `SKILL.md`, each ≤ a few pages. Claude loads only the ones relevant to the current task.
- No README, CHANGELOG, or auxiliary docs inside skill folders — those live at the plugin root.

Read the `framework` skill's `SKILL.md` if you want to see the routing table and minimum-viable-agent template up front.

## Typical flows

**Writing new atomic-agents code.** Open your project. Claude notices imports from `atomic_agents`, loads the `framework` skill, and pulls in `references/schemas.md`, `references/agents.md`, etc. as the conversation progresses.

**Before committing.** Ask "review my changes for atomic-agents issues." The `atomic-reviewer` subagent fires (or Claude invokes it via the `Task` tool), reads the diff in its own context, and returns a confidence-filtered list of framework-specific issues with ready-to-apply fixes.

**Starting from nothing.** Run `/atomic-agents:new-app my-project`. Four questions, one scaffolded project, one runnable agent.

## Framework compatibility

- Python 3.12+ (PEP 695 generics).
- Atomic Agents 2.7+.
- Instructor 1.14+ with provider extras (`instructor[openai]`, `instructor[anthropic]`, `instructor[groq]`, `instructor[google-genai]`).
- Pydantic 2.

## Development

Edit files in place and re-run `/reload-plugins` in Claude Code to pick up changes without restarting. `--plugin-dir` loads take precedence over installed marketplace copies for the current session.

Skill-authoring guidance comes from Anthropic's [skill-creator](https://github.com/anthropics/skills) and [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). Keep descriptions in third person with concrete trigger terms, keep SKILL.md bodies under 500 lines, and push detail into `references/` files so progressive disclosure works.

## License

MIT — see `LICENSE`.

## Links

- Framework: https://github.com/BrainBlend-AI/atomic-agents
- Examples: https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples
- Changelog: `CHANGELOG.md`

Built by [BrainBlend AI](https://github.com/BrainBlend-AI).
