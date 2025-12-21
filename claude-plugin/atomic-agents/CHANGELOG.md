# Changelog

All notable changes to the Atomic Agents Claude Code Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-21

### Added

#### Agents
- **atomic-explorer** - Analyzes existing Atomic Agents applications by tracing configurations, schemas, tools, and orchestration patterns
- **atomic-architect** - Designs application architectures with pattern selection and implementation blueprints
- **atomic-reviewer** - Reviews code for bugs, anti-patterns, security issues with confidence-based filtering
- **schema-designer** - Generates well-structured Pydantic schemas with proper validation

#### Commands
- **/atomic-create** - 7-phase guided workflow for creating complete Atomic Agents applications
  - Discovery, Exploration, Clarification, Architecture, Implementation, Review, Summary phases
  - Parallel agent deployment for comprehensive analysis
  - User approval gates at critical decision points
- **/atomic-agent** - Quick scaffolding for new agents with schemas and configuration
- **/atomic-tool** - Quick scaffolding for new tools with error handling patterns

#### Skills
- **atomic-schemas** - BaseIOSchema patterns, field definitions, validators, type constraints
- **atomic-agents** - Agent configuration, ChatHistory, provider setup, execution methods
- **atomic-tools** - BaseTool development, configuration, error handling, orchestration
- **atomic-context** - Context providers, dynamic prompt injection, RAG patterns
- **atomic-prompts** - SystemPromptGenerator structure, prompt engineering best practices
- **atomic-structure** - Project organization patterns from simple to complex applications

### Framework Support
- Full coverage of Atomic Agents core components
- Support for multiple LLM providers (OpenAI, Anthropic, Groq, Ollama)
- Patterns for synchronous, asynchronous, and streaming execution
- Multi-agent orchestration patterns (sequential, parallel, router, supervisor)

---

## [Unreleased]

### Planned
- Hook for automatic schema validation on file save
- MCP server integration for external tool discovery
- Additional skills for advanced patterns (MCP, testing, deployment)
- Example templates for common application types
