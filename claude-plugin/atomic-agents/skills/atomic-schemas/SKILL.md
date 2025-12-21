---
description: This skill should be used when the user asks to "create a schema", "define input/output", "add fields", "validate data", "Pydantic schema", "BaseIOSchema", or needs guidance on schema design patterns, field definitions, validators, and type constraints for Atomic Agents applications.
---

# Atomic Agents Schema Design

Schemas are the foundation of Atomic Agents applications. They define the contracts between agents, tools, and external systems using Pydantic models.

## Core Principle: Always Use BaseIOSchema

```python
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field

class MySchema(BaseIOSchema):
    """Schema description."""
    field: str = Field(..., description="Field description")
```

**Never use plain `BaseModel`** - `BaseIOSchema` provides Atomic Agents integration features.

## Field Definitions

### Required Fields
```python
name: str = Field(..., description="The user's full name")
```

### Optional Fields
```python
from typing import Optional
nickname: Optional[str] = Field(default=None, description="Optional nickname")
```

### Fields with Defaults
```python
count: int = Field(default=10, description="Number of items to return")
```

### Constrained Fields
```python
# Numeric constraints
age: int = Field(..., ge=0, le=150, description="Age in years")
score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")

# String constraints
name: str = Field(..., min_length=1, max_length=100, description="Name")

# List constraints
tags: List[str] = Field(default_factory=list, max_length=10, description="Tags")
```

### Literal Types (Fixed Options)
```python
from typing import Literal
status: Literal["pending", "approved", "rejected"] = Field(..., description="Status")
```

### Enums
```python
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
```

## Validators

### Field Validators
```python
from pydantic import field_validator

class EmailSchema(BaseIOSchema):
    email: str = Field(..., description="Email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()
```

### Model Validators
```python
from pydantic import model_validator

class DateRangeSchema(BaseIOSchema):
    start: str = Field(..., description="Start date")
    end: str = Field(..., description="End date")

    @model_validator(mode="after")
    def validate_range(self) -> "DateRangeSchema":
        if self.end < self.start:
            raise ValueError("end must be after start")
        return self
```

## Common Patterns

### Chat Input/Output
```python
class ChatInputSchema(BaseIOSchema):
    """User message input."""
    message: str = Field(..., min_length=1, description="User's message")

class ChatOutputSchema(BaseIOSchema):
    """Agent response output."""
    response: str = Field(..., description="Agent's response")
```

### Structured Analysis Output
```python
class AnalysisOutputSchema(BaseIOSchema):
    """Structured analysis result."""
    summary: str = Field(..., description="Brief summary")
    findings: List[str] = Field(default_factory=list, description="Key findings")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
```

### Tool Schemas
```python
class ToolInputSchema(BaseIOSchema):
    """Tool input parameters."""
    query: str = Field(..., description="Search query")

class ToolOutputSchema(BaseIOSchema):
    """Successful tool result."""
    result: str = Field(..., description="Tool result")

class ToolErrorSchema(BaseIOSchema):
    """Tool error result."""
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")
```

### Nested Schemas
```python
class AddressSchema(BaseIOSchema):
    """Mailing address."""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country code")

class PersonSchema(BaseIOSchema):
    """Person with address."""
    name: str = Field(..., description="Full name")
    address: AddressSchema = Field(..., description="Mailing address")
```

### Union Types
```python
from typing import Union

class TextContent(BaseIOSchema):
    type: Literal["text"] = "text"
    text: str = Field(..., description="Text content")

class ImageContent(BaseIOSchema):
    type: Literal["image"] = "image"
    url: str = Field(..., description="Image URL")

class MessageSchema(BaseIOSchema):
    content: Union[TextContent, ImageContent] = Field(..., description="Content")
```

## Best Practices

1. **Always provide descriptions** - LLMs use them to understand field purpose
2. **Constrain appropriately** - Use ge, le, min_length, max_length, Literal
3. **Validate business rules** - Use field_validator and model_validator
4. **Use Optional sparingly** - Only when truly optional
5. **Provide sensible defaults** - When there's a clear default value
6. **Document with docstrings** - Explain the schema's purpose
7. **Compose for complexity** - Nest schemas for structured data

## References

See `references/` for:
- `advanced-patterns.md` - Complex schema patterns
- `validation-patterns.md` - Advanced validator examples

See `examples/` for:
- `common-schemas.py` - Ready-to-use schema templates
