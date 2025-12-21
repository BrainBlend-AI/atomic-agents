---
description: This skill should be used when the user asks to "create a tool", "implement BaseTool", "add tool to agent", "tool orchestration", "external API tool", or needs guidance on tool development, tool configuration, error handling, and integrating tools with agents in Atomic Agents applications.
---

# Atomic Agents Tool Development

Tools extend agent capabilities by providing access to external services, APIs, databases, and computations. They follow a consistent pattern with input/output schemas and error handling.

## Tool Architecture

```
┌─────────────────────────────────────┐
│           BaseTool                  │
├─────────────────────────────────────┤
│ input_schema: BaseIOSchema          │
│ output_schema: BaseIOSchema         │
│ config: BaseToolConfig              │
├─────────────────────────────────────┤
│ run(params) -> Output | Error       │
└─────────────────────────────────────┘
```

## Basic Tool Template

```python
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import Optional
import os

# ============================================================
# Schemas
# ============================================================

class MyToolInputSchema(BaseIOSchema):
    """Input for the tool."""
    query: str = Field(..., description="The query to process")

class MyToolOutputSchema(BaseIOSchema):
    """Successful output."""
    result: str = Field(..., description="The result")

class MyToolErrorSchema(BaseIOSchema):
    """Error output."""
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")

# ============================================================
# Configuration
# ============================================================

class MyToolConfig(BaseToolConfig):
    """Tool configuration."""
    api_key: str = Field(
        default_factory=lambda: os.getenv("MY_API_KEY", ""),
        description="API key"
    )
    timeout: int = Field(default=30, description="Timeout in seconds")

# ============================================================
# Tool
# ============================================================

class MyTool(BaseTool):
    """Tool description."""

    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema

    def __init__(self, config: MyToolConfig = None):
        super().__init__(config or MyToolConfig())
        self.config: MyToolConfig = self.config

    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema | MyToolErrorSchema:
        try:
            # Tool logic here
            result = f"Processed: {params.query}"
            return MyToolOutputSchema(result=result)
        except Exception as e:
            return MyToolErrorSchema(error=str(e), code="ERROR")

# Convenience instance
tool = MyTool()
```

## Tool Configuration Pattern

```python
class APIToolConfig(BaseToolConfig):
    """Configuration with environment variables."""

    api_key: str = Field(
        default_factory=lambda: os.getenv("SERVICE_API_KEY", ""),
        description="API key for the service"
    )
    base_url: str = Field(
        default="https://api.service.com/v1",
        description="Base URL for API"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
```

## Error Handling Pattern

Always return error schemas instead of raising exceptions:

```python
def run(self, params: InputSchema) -> OutputSchema | ErrorSchema:
    # Validate configuration
    if not self.config.api_key:
        return ErrorSchema(
            error="API key not configured",
            code="CONFIG_ERROR"
        )

    try:
        # Make external call
        response = requests.get(
            f"{self.config.base_url}/endpoint",
            params={"q": params.query},
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout
        )
        response.raise_for_status()
        data = response.json()

        return OutputSchema(result=data["result"])

    except requests.Timeout:
        return ErrorSchema(error="Request timed out", code="TIMEOUT")
    except requests.HTTPError as e:
        return ErrorSchema(error=f"HTTP error: {e}", code="HTTP_ERROR")
    except Exception as e:
        return ErrorSchema(error=str(e), code="UNKNOWN_ERROR")
```

## Using Tools with Agents

### Direct Tool Usage
```python
from my_tools import search_tool, SearchInputSchema

# Call tool directly
result = search_tool.run(SearchInputSchema(query="atomic agents"))
```

### Tool Orchestration Pattern
```python
from typing import Union
from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig

# Define tool selection schema
class ToolCallSchema(BaseIOSchema):
    tool_name: Literal["search", "calculate", "none"] = Field(
        ..., description="Which tool to use"
    )
    tool_input: Union[SearchInput, CalculateInput, None] = Field(
        ..., description="Input for the selected tool"
    )

# Agent decides which tool to use
agent = AtomicAgent[UserQuerySchema, ToolCallSchema](config=config)

# Orchestration loop
user_input = UserQuerySchema(query="What is 2+2?")
tool_decision = agent.run(user_input)

if tool_decision.tool_name == "calculate":
    result = calculator_tool.run(tool_decision.tool_input)
elif tool_decision.tool_name == "search":
    result = search_tool.run(tool_decision.tool_input)
```

## Pre-Built Tools (Atomic Forge)

Download tools from Atomic Forge:

```bash
atomic download calculator
atomic download searxng
atomic download youtube-transcript
```

Available tools:
- **Calculator** - Mathematical operations
- **SearXNG** - Web search
- **Tavily** - AI-powered search
- **YouTube Transcript** - Video transcripts
- **Webpage Scraper** - HTML content extraction

## Tool Best Practices

1. **Always use BaseToolConfig** - For consistent configuration
2. **Environment variables for secrets** - Never hardcode API keys
3. **Return errors, don't raise** - Caller can handle gracefully
4. **Set timeouts** - Prevent hanging on external calls
5. **Validate inputs** - Check parameters before processing
6. **Include error codes** - Help with debugging and handling
7. **Document thoroughly** - Input/output schemas need descriptions

## References

See `references/` for:
- `api-integration.md` - Patterns for REST API tools
- `database-tools.md` - Database integration patterns

See `examples/` for:
- `simple-tool.py` - Minimal tool implementation
- `api-tool.py` - External API integration
