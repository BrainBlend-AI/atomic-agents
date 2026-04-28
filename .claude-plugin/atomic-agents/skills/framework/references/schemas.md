# Schemas (`BaseIOSchema`)

## Contents
- Rules enforced by `BaseIOSchema`
- Field patterns
- Validators
- Composition, unions, enums
- Error-schema pattern
- Common mistakes

## Rules enforced by `BaseIOSchema`

`BaseIOSchema` is a Pydantic `BaseModel` plus a metaclass hook that fails at class-definition time if:

- The class has no docstring, or only whitespace.

`model_json_schema()` is also overridden so the class docstring becomes the schema `description` and the class name becomes the `title`. Instructor uses both when prompting the LLM, so write the docstring for the model, not for humans only.

```python
from pydantic import Field
from atomic_agents import BaseIOSchema

class SearchQuery(BaseIOSchema):
    """Parameters for a web search issued by the agent."""

    query: str = Field(..., description="Natural-language search query.")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return.")
```

## Field patterns

Required, optional, and defaulted — always with `description=`:

```python
from typing import Optional, Literal
from pydantic import Field

name: str = Field(..., description="Full legal name.")
nickname: Optional[str] = Field(default=None, description="Preferred nickname, if any.")
count: int = Field(default=10, ge=1, le=100, description="Items to return (1–100).")
sort: Literal["asc", "desc"] = Field(default="desc", description="Sort order.")
tags: list[str] = Field(default_factory=list, max_length=10, description="Tag filters (≤10).")
```

Use `Literal[...]` for closed sets before reaching for `Enum` — the JSON schema stays flatter, which helps Instructor.

## Validators

Field-level:

```python
from pydantic import field_validator

class EmailSchema(BaseIOSchema):
    """An email address."""
    email: str = Field(..., description="RFC 5322 email address.")

    @field_validator("email")
    @classmethod
    def _lowercase(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email")
        return v.lower()
```

Model-level (cross-field):

```python
from pydantic import model_validator
from datetime import date

class DateRange(BaseIOSchema):
    """An inclusive date range."""
    start: date = Field(..., description="Start date (inclusive).")
    end: date = Field(..., description="End date (inclusive).")

    @model_validator(mode="after")
    def _ordered(self) -> "DateRange":
        if self.end < self.start:
            raise ValueError("end must be on or after start")
        return self
```

Validation errors surface as Instructor retries (up to `max_retries`) and fire the `parse:error` hook. See `agents.md`.

## Composition, unions, enums

Nested:

```python
class Address(BaseIOSchema):
    """A mailing address."""
    street: str = Field(..., description="Street and number.")
    city: str = Field(..., description="City name.")
    country: str = Field(..., description="ISO 3166-1 alpha-2 country code.")

class Person(BaseIOSchema):
    """A person with mailing address."""
    name: str = Field(..., description="Full name.")
    address: Address = Field(..., description="Mailing address.")
```

Discriminated unions — include a `Literal` discriminator on each variant:

```python
from typing import Literal, Union

class TextPart(BaseIOSchema):
    """A text message part."""
    kind: Literal["text"] = "text"
    text: str = Field(..., description="Plain-text body.")

class ImagePart(BaseIOSchema):
    """An image attachment."""
    kind: Literal["image"] = "image"
    url: str = Field(..., description="Publicly accessible image URL.")

class Message(BaseIOSchema):
    """A multimodal message part."""
    part: Union[TextPart, ImagePart] = Field(..., description="Message content.")
```

Enums:

```python
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(BaseIOSchema):
    """A unit of work."""
    title: str = Field(..., description="Task title.")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level.")
```

## Error-schema pattern

When a tool or agent can legitimately fail, model it as a structured alternative output rather than an exception. Two common shapes:

**Pair of success/error schemas** returned via a union on the agent output:

```python
class SearchSuccess(BaseIOSchema):
    """Successful search result."""
    results: list[str] = Field(..., description="Matching items.")

class SearchFailure(BaseIOSchema):
    """Search could not complete."""
    error: str = Field(..., description="Human-readable failure reason.")
    code: Literal["rate_limited", "no_results", "upstream_error"] = Field(
        ..., description="Machine-readable failure code."
    )

class SearchOutput(BaseIOSchema):
    """Search output — either success or typed failure."""
    result: Union[SearchSuccess, SearchFailure] = Field(..., description="Outcome.")
```

**Discriminated status field** on a single schema:

```python
class SearchOutput(BaseIOSchema):
    """Search result envelope."""
    status: Literal["ok", "error"] = Field(..., description="Outcome code.")
    results: list[str] = Field(default_factory=list, description="Items when status='ok'.")
    error: Optional[str] = Field(default=None, description="Message when status='error'.")
```

Prefer the first shape when callers need exhaustive case handling; prefer the second when most code paths just care about `status == "ok"`.

## Common mistakes

- Forgetting the docstring — the framework raises `ValueError("… must have a non-empty docstring …")` at import.
- Plain `BaseModel` — loses the docstring enforcement and the `model_json_schema` override.
- `Field()` without `description=` — Instructor has nothing to tell the LLM about the field.
- `Optional[str]` with no default — becomes required-but-nullable, rarely what's intended.
- Over-broad types (`dict`, `Any`, `object`) — the LLM generates anything, Pydantic can't validate.
