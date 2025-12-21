---
description: This skill should be used when the user asks to "write system prompt", "configure SystemPromptGenerator", "prompt engineering", "background steps output_instructions", "improve agent prompt", or needs guidance on structuring system prompts, writing effective instructions, and optimizing agent behavior in Atomic Agents applications.
---

# Atomic Agents System Prompt Design

The `SystemPromptGenerator` creates structured, effective system prompts for agents. It combines static instructions with dynamic context from providers.

## SystemPromptGenerator Structure

```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

system_prompt = SystemPromptGenerator(
    background=[
        # WHO the agent is
        "You are an expert data analyst.",
        "You specialize in financial data interpretation.",
    ],
    steps=[
        # HOW to process requests
        "1. Understand the user's question about the data.",
        "2. Identify relevant data points and trends.",
        "3. Analyze patterns and correlations.",
        "4. Formulate clear, actionable insights.",
    ],
    output_instructions=[
        # WHAT to produce
        "Provide insights in clear, non-technical language.",
        "Include specific numbers and percentages.",
        "Highlight key takeaways at the beginning.",
    ],
)
```

## Three-Part Structure

### Background (WHO)
Establishes the agent's identity, expertise, and role:

```python
background=[
    "You are an expert [role] with deep knowledge in [domain].",
    "Your purpose is to [primary function].",
    "You have experience with [relevant experience].",
    "You approach problems with [methodology/style].",
]
```

**Examples by domain:**
```python
# Customer Support
background=[
    "You are a helpful customer support specialist.",
    "You represent [Company] and embody its values of helpfulness and clarity.",
    "You have comprehensive knowledge of our products and policies.",
]

# Code Assistant
background=[
    "You are an expert software engineer specializing in Python.",
    "You write clean, maintainable, well-documented code.",
    "You follow best practices and design patterns.",
]

# Research Assistant
background=[
    "You are a research analyst with expertise in synthesizing information.",
    "You excel at finding patterns across multiple sources.",
    "You prioritize accuracy and cite sources when possible.",
]
```

### Steps (HOW)
Defines the processing workflow:

```python
steps=[
    "1. [First action to take]",
    "2. [Second action to take]",
    "3. [Third action to take]",
    "4. [Final action to take]",
]
```

**Effective step patterns:**

```python
# Analysis Pattern
steps=[
    "1. Parse and understand the input data.",
    "2. Identify key elements and relationships.",
    "3. Apply relevant analysis techniques.",
    "4. Synthesize findings into coherent insights.",
    "5. Validate conclusions against the data.",
]

# Q&A Pattern
steps=[
    "1. Understand the user's question fully.",
    "2. Retrieve relevant information from context.",
    "3. Formulate a clear, accurate answer.",
    "4. Provide supporting details if helpful.",
]

# Task Execution Pattern
steps=[
    "1. Parse the task requirements.",
    "2. Break down into subtasks if complex.",
    "3. Execute each subtask systematically.",
    "4. Validate the output meets requirements.",
]
```

### Output Instructions (WHAT)
Specifies the response format and quality:

```python
output_instructions=[
    "Format your response as [format].",
    "Include [required elements].",
    "Ensure [quality requirements].",
    "Avoid [things to exclude].",
]
```

**Format examples:**

```python
# Structured Output
output_instructions=[
    "Provide your response with a summary first.",
    "Use bullet points for key findings.",
    "Include confidence level (high/medium/low).",
    "End with actionable recommendations.",
]

# Conversational Output
output_instructions=[
    "Respond in a friendly, conversational tone.",
    "Keep responses concise but complete.",
    "Ask clarifying questions if needed.",
]

# Technical Output
output_instructions=[
    "Include code examples where appropriate.",
    "Explain technical concepts clearly.",
    "Reference documentation or sources.",
]
```

## Integrating Context Providers

Context providers add dynamic sections:

```python
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptGenerator,
    BaseDynamicContextProvider,
)

class RAGProvider(BaseDynamicContextProvider):
    def __init__(self):
        super().__init__(title="Relevant Documents")
        self.docs = []

    def get_info(self) -> str:
        return "\n".join(self.docs)

# Create generator
generator = SystemPromptGenerator(
    background=["You answer questions using provided documents."],
    steps=["1. Read the documents.", "2. Answer based on them."],
    output_instructions=["Cite document sources."],
)

# Register provider
rag = RAGProvider()
agent.register_context_provider("rag", rag)
```

The generated prompt will include:
```
[Background section]
[Steps section]
[Output Instructions section]

## Relevant Documents
[Dynamic content from provider]
```

## Prompt Engineering Tips

### Be Specific
```python
# Bad
background=["You are helpful."]

# Good
background=[
    "You are a Python code reviewer.",
    "You identify bugs, security issues, and style violations.",
    "You follow PEP 8 and common best practices.",
]
```

### Use Action Verbs
```python
# Bad
steps=["Think about the problem."]

# Good
steps=[
    "1. Identify the core issue.",
    "2. List possible solutions.",
    "3. Evaluate trade-offs.",
    "4. Recommend the best approach.",
]
```

### Constrain Output
```python
# Bad
output_instructions=["Give a good answer."]

# Good
output_instructions=[
    "Limit response to 3 paragraphs maximum.",
    "Start with the most important point.",
    "Include one specific example.",
]
```

### Handle Edge Cases
```python
background=[
    "If you cannot answer with certainty, say so clearly.",
    "If the question is ambiguous, ask for clarification.",
    "If the request is outside your expertise, acknowledge it.",
]
```

## Common Prompt Patterns

### Expert Assistant
```python
SystemPromptGenerator(
    background=[
        "You are an expert [domain] assistant.",
        "You provide accurate, helpful information.",
        "You acknowledge when you're uncertain.",
    ],
    steps=[
        "1. Understand the user's need.",
        "2. Provide relevant information.",
        "3. Offer follow-up suggestions.",
    ],
    output_instructions=[
        "Be concise but thorough.",
        "Use examples when helpful.",
    ],
)
```

### Analyst
```python
SystemPromptGenerator(
    background=[
        "You are a data analyst.",
        "You find insights in data.",
    ],
    steps=[
        "1. Examine the data carefully.",
        "2. Identify patterns and anomalies.",
        "3. Draw conclusions.",
        "4. Suggest actions.",
    ],
    output_instructions=[
        "Include specific numbers.",
        "Highlight key findings first.",
        "Use simple language.",
    ],
)
```

### Code Generator
```python
SystemPromptGenerator(
    background=[
        "You are an expert programmer.",
        "You write clean, efficient code.",
    ],
    steps=[
        "1. Understand the requirements.",
        "2. Plan the implementation.",
        "3. Write the code.",
        "4. Add comments and documentation.",
    ],
    output_instructions=[
        "Include complete, runnable code.",
        "Add comments for complex logic.",
        "Follow language conventions.",
    ],
)
```

## References

See `references/` for:
- `prompt-patterns.md` - More prompt templates
- `optimization.md` - Token-efficient prompts

See `examples/` for:
- `domain-prompts.py` - Domain-specific examples
