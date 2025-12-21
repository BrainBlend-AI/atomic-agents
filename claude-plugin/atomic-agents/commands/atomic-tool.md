---
description: Quickly create a new Atomic Agents tool with proper input/output schemas and error handling
argument-hint: Description of the tool to create (e.g., "a weather API tool that fetches current conditions")
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

# Quick Tool Creation

Create a new Atomic Agents tool based on the user's description.

## Process

### 1. Understand Requirements

If `$ARGUMENTS` is provided, parse the tool description. Otherwise, ask:
- What should this tool do?
- What external service does it interact with (API, database, file system)?
- What input parameters does it need?
- What output should it return?
- What error conditions should be handled?

### 2. Load Knowledge

```
Use the Skill tool to load: atomic-tools
Use the Skill tool to load: atomic-schemas
```

### 3. Identify Target Location

- Check if there's an existing project structure
- Look for `tools/` directory or determine where to create the tool
- Check for existing config patterns for API keys

### 4. Design the Tool

Use the `schema-designer` agent for the schemas:
```
Task(subagent_type="schema-designer", prompt="Design input and output schemas for a tool that: [description]. Include error handling schema if applicable. Use ultrathink.")
```

### 5. Create Files

**[tool_name]_tool.py**:
```python
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import Optional
import os

# ============================================================
# Input/Output Schemas
# ============================================================

class [Tool]InputSchema(BaseIOSchema):
    """Input for [tool purpose]."""

    param: str = Field(
        ...,
        description="Description of this parameter"
    )


class [Tool]OutputSchema(BaseIOSchema):
    """Successful output from [tool purpose]."""

    result: str = Field(
        ...,
        description="The result from the tool"
    )


class [Tool]ErrorSchema(BaseIOSchema):
    """Error output from [tool purpose]."""

    error: str = Field(
        ...,
        description="Error message describing what went wrong"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Error code if available"
    )


# ============================================================
# Tool Configuration
# ============================================================

class [Tool]Config(BaseToolConfig):
    """Configuration for [Tool]."""

    api_key: str = Field(
        default_factory=lambda: os.getenv("[SERVICE]_API_KEY", ""),
        description="API key for [service]"
    )
    base_url: str = Field(
        default="https://api.example.com",
        description="Base URL for API requests"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )


# ============================================================
# Tool Implementation
# ============================================================

class [Tool](BaseTool):
    """
    Tool for [purpose].

    This tool [detailed description of what it does].
    """

    input_schema = [Tool]InputSchema
    output_schema = [Tool]OutputSchema

    def __init__(self, config: [Tool]Config = None):
        """Initialize the tool with configuration."""
        super().__init__(config or [Tool]Config())
        self.config: [Tool]Config = self.config

    def run(self, params: [Tool]InputSchema) -> [Tool]OutputSchema | [Tool]ErrorSchema:
        """
        Execute the tool.

        Args:
            params: Input parameters for the tool

        Returns:
            [Tool]OutputSchema on success, [Tool]ErrorSchema on failure
        """
        try:
            # Validate configuration
            if not self.config.api_key:
                return [Tool]ErrorSchema(
                    error="API key not configured",
                    error_code="CONFIG_ERROR"
                )

            # Implement tool logic here
            # Example:
            # response = requests.get(
            #     f"{self.config.base_url}/endpoint",
            #     params={"q": params.param},
            #     headers={"Authorization": f"Bearer {self.config.api_key}"},
            #     timeout=self.config.timeout
            # )
            # response.raise_for_status()
            # data = response.json()

            result = f"Processed: {params.param}"  # Replace with actual logic

            return [Tool]OutputSchema(result=result)

        except Exception as e:
            return [Tool]ErrorSchema(
                error=str(e),
                error_code="EXECUTION_ERROR"
            )


# ============================================================
# Convenience Instance
# ============================================================

# Default tool instance (can be overridden with custom config)
tool = [Tool]()
```

### 6. Provide Usage Examples

**Direct Usage**:
```python
from [module].[tool_name]_tool import tool, [Tool]InputSchema

# Run the tool
input_data = [Tool]InputSchema(param="value")
result = tool.run(input_data)

if isinstance(result, [Tool]ErrorSchema):
    print(f"Error: {result.error}")
else:
    print(f"Result: {result.result}")
```

**With Custom Config**:
```python
from [module].[tool_name]_tool import [Tool], [Tool]Config, [Tool]InputSchema

# Custom configuration
config = [Tool]Config(
    api_key="your-api-key",
    timeout=60
)

# Create tool with custom config
custom_tool = [Tool](config=config)
result = custom_tool.run([Tool]InputSchema(param="value"))
```

**With Agent**:
```python
from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig
from [module].[tool_name]_tool import tool

# Agent can use the tool
# (Show how to integrate with agent's tool orchestration)
```

### 7. Quick Review

Perform a quick validation:
- [ ] Schemas inherit from BaseIOSchema
- [ ] All fields have descriptions
- [ ] Tool inherits from BaseTool
- [ ] input_schema and output_schema class attributes are set
- [ ] Error handling returns ErrorSchema, not raising exceptions
- [ ] Configuration uses environment variables for secrets
- [ ] Timeout is set for external calls

Report any issues found.

---

## Output

Provide:
1. Created files with their paths
2. Required environment variables
3. Usage examples (direct and with agent)
4. Any suggestions for enhancement
