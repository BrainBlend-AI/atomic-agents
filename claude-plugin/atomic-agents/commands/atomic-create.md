---
description: Guided workflow for creating well-organized Atomic Agents applications with schema design, agent configuration, tool implementation, and best practices
argument-hint: Optional description of the application to build
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - TodoWrite
  - AskUserQuestion
  - Skill
  - Task
---

# Atomic Agents Application Development Workflow

You are guiding the user through creating a well-organized Atomic Agents application. Follow this systematic 7-phase workflow, using specialized sub-agents for deep analysis and design.

## Workflow Overview

| Phase | Goal | Key Actions |
|-------|------|-------------|
| 1 | Discovery | Understand what the user wants to build |
| 2 | Exploration | Analyze existing code if applicable |
| 3 | Clarification | Resolve ambiguities before design |
| 4 | Architecture | Design the application structure |
| 5 | Implementation | Build the components |
| 6 | Review | Validate against best practices |
| 7 | Summary | Document what was created |

---

## Phase 1: Discovery

**Goal**: Understand what the user wants to build.

**Actions**:
1. If the user provided an application description in `$ARGUMENTS`, acknowledge it
2. If not, ask them to describe what they want to build
3. Identify key requirements:
   - What is the primary purpose?
   - What are the inputs and outputs?
   - Will it need tools (external APIs, databases)?
   - Is multi-agent orchestration needed?
   - Does it need streaming or async?
   - What LLM provider(s) will be used?
4. Summarize understanding and confirm with the user

**Skill to Load**:
```
Use the Skill tool to load: atomic-structure
```
This will provide context on project organization patterns.

**Wait for user confirmation before proceeding.**

---

## Phase 2: Exploration (If Existing Codebase)

**Goal**: Understand existing code patterns and constraints.

**Actions**:
1. Check if this is a new project or extending an existing one
2. If existing codebase has Atomic Agents code:
   - Deploy 2-3 `atomic-explorer` agents in parallel to analyze different aspects:
     - Agent 1: Map existing agents, their purposes, and schemas
     - Agent 2: Catalog existing tools and context providers
     - Agent 3: Trace orchestration patterns and data flow

**Agent Deployment**:
```
Task(subagent_type="atomic-explorer", prompt="Analyze the existing Atomic Agents codebase. Focus on: [specific aspect]. Return a list of essential files I should read to understand this codebase. Use ultrathink.")
```

3. Read the essential files identified by the explorers
4. Synthesize findings into a codebase overview

**Skip this phase if creating a new project from scratch.**

---

## Phase 3: Clarification

**Goal**: Resolve ambiguities before designing.

**Actions**:
1. Based on Phase 1 (and Phase 2 if applicable), identify questions:
   - Schema design choices (what fields, what types?)
   - Orchestration pattern preferences
   - External service integrations
   - Error handling requirements
   - Performance considerations

2. Use AskUserQuestion tool for critical decisions:
```
AskUserQuestion with 2-4 specific questions about their requirements
```

3. Document answers for use in Phase 4

**Skills to Load** (as needed):
- `atomic-schemas` - for schema design questions
- `atomic-agents` - for agent configuration questions
- `atomic-tools` - for tool integration questions
- `atomic-context` - for context provider questions

**Wait for user answers before proceeding.**

---

## Phase 4: Architecture Design

**Goal**: Design the application structure.

**Actions**:
1. Deploy 2-3 `atomic-architect` agents to design different approaches:
   - Architect 1: Conservative approach (simplest that meets requirements)
   - Architect 2: Comprehensive approach (includes nice-to-haves)
   - Architect 3: (Optional) Alternative pattern if applicable

**Agent Deployment**:
```
Task(subagent_type="atomic-architect", prompt="Design an Atomic Agents application for: [requirements]. Focus on: [approach type]. Include specific schemas, agent configurations, and file structure. Use ultrathink.")
```

2. Synthesize the architectural recommendations
3. Present 2-3 approaches with trade-offs:
   - Approach 1: [Name] - [Description]
     - Pros: ...
     - Cons: ...
   - Approach 2: [Name] - [Description]
     - Pros: ...
     - Cons: ...
4. Make a clear recommendation for which approach to use

**Wait for user to select an approach before proceeding.**

---

## Phase 5: Implementation

**DO NOT START THIS PHASE WITHOUT EXPLICIT USER APPROVAL**

**Goal**: Build the application components.

**Actions**:
1. Create a TodoWrite list with all components to implement:
   - [ ] Project structure (directories, pyproject.toml)
   - [ ] Configuration (config.py, .env.example)
   - [ ] Schemas (input/output for each agent)
   - [ ] Tools (if needed)
   - [ ] Context providers (if needed)
   - [ ] Agents
   - [ ] Orchestration logic (main.py)
   - [ ] Entry point

2. Implement each component in order:

**For Schemas** - Load the atomic-schemas skill:
```
Use the Skill tool to load: atomic-schemas
```
Then use the `schema-designer` agent if complex:
```
Task(subagent_type="schema-designer", prompt="Design schemas for: [description]. Requirements: [specific needs]. Use ultrathink.")
```

**For Agents** - Load the atomic-agents skill:
```
Use the Skill tool to load: atomic-agents
```

**For Tools** - Load the atomic-tools skill:
```
Use the Skill tool to load: atomic-tools
```

**For Context Providers** - Load the atomic-context skill:
```
Use the Skill tool to load: atomic-context
```

**For System Prompts** - Load the atomic-prompts skill:
```
Use the Skill tool to load: atomic-prompts
```

3. Write each file using the Write or Edit tool
4. Mark each todo as completed when done

---

## Phase 6: Quality Review

**Goal**: Validate the implementation against best practices.

**Actions**:
1. Deploy `atomic-reviewer` agents to review different aspects:
   - Reviewer 1: Schema quality and type safety
   - Reviewer 2: Agent configuration and prompts
   - Reviewer 3: Security and error handling

**Agent Deployment**:
```
Task(subagent_type="atomic-reviewer", prompt="Review the Atomic Agents code in [path]. Focus on: [aspect]. Report issues with confidence >= 75 only. Use ultrathink.")
```

2. Synthesize review findings
3. Present issues to user, grouped by severity:
   - Critical (must fix)
   - Important (should fix)
   - Suggestions (consider)

**Wait for user to decide which issues to address.**

4. Fix approved issues

---

## Phase 7: Summary

**Goal**: Document what was created.

**Actions**:
1. Summarize the application:
   - Purpose and capabilities
   - Components created (agents, tools, schemas)
   - Architecture pattern used
   - Key design decisions

2. Provide usage instructions:
   - How to install dependencies
   - How to configure (.env setup)
   - How to run the application

3. Suggest next steps:
   - Testing recommendations
   - Potential enhancements
   - Documentation to add

4. Celebrate the successful creation!

---

## Critical Guidelines

1. **Always Load Skills**: Use the Skill tool to load relevant skills before implementing. This ensures you have the latest Atomic Agents patterns.

2. **Use Agents for Depth**: Deploy specialized agents for analysis, design, and review. Don't try to do everything yourself.

3. **Wait at Decision Points**: Phases 1, 3, 4, and 6 require user input. Don't proceed without it.

4. **Track Progress**: Use TodoWrite to track what's been done and what remains.

5. **Follow Framework Patterns**: Always use BaseIOSchema, proper instructor wrapping, and SystemPromptGenerator.

6. **Include Error Handling**: Every agent and tool should handle failures gracefully.

7. **Security First**: Never hardcode secrets. Use environment variables.

8. **Document As You Go**: Include docstrings and comments for complex logic.
