---
description: Quickly create a new Atomic Agents agent with proper configuration, schemas, and system prompt
argument-hint: Description of the agent to create (e.g., "a research agent that summarizes articles")
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Skill
  - Task
  - AskUserQuestion
---

# Quick Agent Creation

Create a new Atomic Agents agent based on the user's description.

## Process

### 1. Understand Requirements

If `$ARGUMENTS` is provided, parse the agent description. Otherwise, ask:
- What should this agent do?
- What input does it need?
- What output should it produce?

### 2. Load Knowledge

```
Use the Skill tool to load: atomic-agents
Use the Skill tool to load: atomic-schemas
Use the Skill tool to load: atomic-prompts
```

### 3. Identify Target Location

- Check if there's an existing project structure
- Look for `agents/` directory or determine where to create the agent
- Identify existing schemas to potentially reuse

### 4. Design the Agent

Use the `schema-designer` agent for complex schemas:
```
Task(subagent_type="schema-designer", prompt="Design input and output schemas for an agent that: [description]. Use ultrathink.")
```

### 5. Create Files

Create the following:

**schemas.py** (or add to existing):
```python
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field

class [Agent]InputSchema(BaseIOSchema):
    """Input for [agent purpose]."""
    # fields...

class [Agent]OutputSchema(BaseIOSchema):
    """Output from [agent purpose]."""
    # fields...
```

**[agent_name].py**:
```python
import instructor
import openai
from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory

from .schemas import [Agent]InputSchema, [Agent]OutputSchema

# Initialize client
client = instructor.from_openai(openai.OpenAI())

# Configure agent
config = AgentConfig(
    client=client,
    model="gpt-4o-mini",
    history=ChatHistory(),
    system_prompt_generator=SystemPromptGenerator(
        background=[
            "You are an expert [role].",
            "Your purpose is to [purpose].",
        ],
        steps=[
            "1. [First step]",
            "2. [Second step]",
            "3. [Third step]",
        ],
        output_instructions=[
            "Provide [format instructions].",
            "Ensure [quality requirements].",
        ],
    ),
)

# Create agent
agent = AtomicAgent[InputSchema, OutputSchema](config=config)
```

### 6. Provide Usage Example

Show how to use the created agent:
```python
from [module] import agent, [Agent]InputSchema

# Run the agent
input_data = [Agent]InputSchema(field="value")
output = agent.run(input_data)
print(output)
```

### 7. Quick Review

Perform a quick validation:
- [ ] Schemas inherit from BaseIOSchema
- [ ] All fields have descriptions
- [ ] SystemPromptGenerator has background, steps, output_instructions
- [ ] Client is wrapped with instructor
- [ ] Type parameters match schemas

Report any issues found.

---

## Output

Provide:
1. Created files with their paths
2. Usage example
3. Any suggestions for enhancement
