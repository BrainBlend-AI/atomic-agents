# Atomic Agents Plugin for Claude Code

A comprehensive Claude Code plugin for building well-organized [Atomic Agents](https://github.com/BrainBlend-AI/atomic-agents) applications. This plugin provides specialized sub-agents, guided workflows, and progressive-disclosure skills to help you create production-ready AI agent systems.

## Overview

The Atomic Agents framework is a lightweight, modular system for building AI agents using Pydantic schemas and the Instructor library. This plugin brings that power into Claude Code with:

- **4 Specialized Agents** for analysis, design, review, and schema generation
- **3 Workflow Commands** from guided creation to quick scaffolding
- **6 Progressive-Disclosure Skills** for just-in-time knowledge

## Installation

### From a Marketplace

```bash
# If published to a marketplace
/plugin install atomic-agents@marketplace-name
```

### Local Installation

```bash
# Clone or copy the plugin to a directory
claude --plugin-dir /path/to/atomic-agents
```

### Validate Installation

```bash
# Check that the plugin loads correctly
/plugin validate /path/to/atomic-agents
```

## Commands

### `/atomic-create` - Guided Application Workflow

The master command for building complete Atomic Agents applications through a 7-phase workflow:

```bash
/atomic-create A research agent that summarizes academic papers
```

**Phases:**
1. **Discovery** - Understand requirements
2. **Exploration** - Analyze existing code (if applicable)
3. **Clarification** - Resolve ambiguities
4. **Architecture** - Design the application
5. **Implementation** - Build components
6. **Review** - Validate against best practices
7. **Summary** - Document what was created

### `/atomic-agent` - Quick Agent Creation

Rapidly scaffold a new agent with proper configuration:

```bash
/atomic-agent A customer support agent that handles refund requests
```

Creates:
- Input/output schemas
- Agent configuration with SystemPromptGenerator
- Usage examples

### `/atomic-tool` - Quick Tool Creation

Scaffold a new tool for external integrations:

```bash
/atomic-tool A weather API tool that fetches current conditions
```

Creates:
- Input/output/error schemas
- Tool configuration with environment variables
- Error handling patterns
- Usage examples

## Agents

### atomic-explorer (Yellow)

Deeply analyzes existing Atomic Agents applications:
- Maps agent configurations and purposes
- Catalogs schemas, tools, and context providers
- Traces orchestration patterns and data flow
- Identifies architecture patterns

**Triggered by:** Exploring codebases, understanding existing implementations

### atomic-architect (Green)

Designs application architectures:
- Analyzes requirements
- Selects appropriate orchestration patterns
- Creates implementation blueprints
- Specifies component designs

**Triggered by:** Planning new applications, designing multi-agent systems

### atomic-reviewer (Red)

Reviews code for quality and best practices:
- Schema quality and type safety
- Agent configuration correctness
- Security and error handling
- Performance considerations

**Triggered by:** Code review, pre-commit validation, quality audits

### schema-designer (Blue)

Generates well-structured Pydantic schemas:
- Input/output schemas for agents
- Tool parameter schemas
- Complex nested structures
- Validators for business rules

**Triggered by:** Schema design, data contract definition

## Skills

Skills provide progressive-disclosure knowledge, loading only when needed to keep context lean:

| Skill | Trigger Phrases | Purpose |
|-------|----------------|---------|
| `atomic-schemas` | "create schema", "BaseIOSchema", "field validation" | Pydantic schema patterns |
| `atomic-agents` | "create agent", "AgentConfig", "ChatHistory" | Agent configuration |
| `atomic-tools` | "create tool", "BaseTool", "tool orchestration" | Tool development |
| `atomic-context` | "context provider", "dynamic context", "share data" | Context providers |
| `atomic-prompts` | "system prompt", "SystemPromptGenerator" | Prompt engineering |
| `atomic-structure` | "project structure", "pyproject.toml" | Project organization |

## Usage Examples

### Create a Complete Application

```
You: /atomic-create A RAG chatbot that answers questions from PDF documents

Claude: I'll guide you through creating this application...
[7-phase workflow begins]
```

### Quick Agent Scaffolding

```
You: /atomic-agent A sentiment analysis agent

Claude: [Creates schemas and agent configuration]
```

### Explore Existing Code

```
You: Help me understand how the agents in this project work

Claude: [Deploys atomic-explorer to analyze the codebase]
```

### Review Implementation

```
You: Review my Atomic Agents code for issues

Claude: [Deploys atomic-reviewer with confidence-based filtering]
```

## Framework Reference

This plugin targets the [Atomic Agents](https://github.com/BrainBlend-AI/atomic-agents) framework:

### Core Components

- **AtomicAgent** - Main agent class with structured I/O
- **AgentConfig** - Configuration for model, history, prompts
- **BaseIOSchema** - Base class for Pydantic schemas
- **SystemPromptGenerator** - Structured prompt builder
- **BaseTool** - Base class for tools
- **BaseDynamicContextProvider** - Dynamic context injection
- **ChatHistory** - Conversation state management

### Supported Providers

- OpenAI (GPT-4, GPT-4o, etc.)
- Anthropic (Claude)
- Groq
- Ollama (local models)
- OpenRouter
- Any OpenAI-compatible API

## Best Practices

### When Using This Plugin

1. **Start with /atomic-create** for new projects - it ensures proper structure
2. **Use skills for quick reference** - they load just-in-time knowledge
3. **Let agents do deep analysis** - atomic-explorer for understanding, atomic-reviewer for validation
4. **Follow the workflow** - the 7-phase process prevents common mistakes

### Atomic Agents Best Practices

1. **Always use BaseIOSchema** - never plain Pydantic BaseModel
2. **Describe all fields** - descriptions are used in prompt generation
3. **Use environment variables** - never hardcode API keys
4. **Wrap with instructor** - required for structured outputs
5. **Handle errors gracefully** - tools should return error schemas, not raise

## Troubleshooting

### Plugin Not Loading

1. Verify plugin structure: `.claude-plugin/plugin.json` exists
2. Run validation: `/plugin validate /path/to/plugin`
3. Check for JSON syntax errors in plugin.json

### Skills Not Triggering

1. Use explicit trigger phrases from skill descriptions
2. Manually load: "Load the atomic-schemas skill"

### Agents Not Found

1. Check agents/ directory exists with .md files
2. Verify YAML frontmatter is valid in agent files

## Contributing

Contributions are welcome! Please:

1. Follow the existing plugin structure
2. Add tests for new components
3. Update documentation
4. Follow semantic versioning

## License

MIT License - See [LICENSE](LICENSE) file.

## Links

- **Atomic Agents Framework**: https://github.com/BrainBlend-AI/atomic-agents
- **Documentation**: https://github.com/BrainBlend-AI/atomic-agents/tree/main/docs
- **Examples**: https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples

---

Built with care for the Atomic Agents community by [BrainBlend AI](https://github.com/BrainBlend-AI).
