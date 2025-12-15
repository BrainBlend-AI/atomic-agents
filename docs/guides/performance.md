# Performance Optimization Guide

This guide covers strategies for optimizing Atomic Agents performance, including response times, token usage, and resource efficiency.

## Overview

Performance optimization focuses on:

- **Latency**: Reducing response times
- **Token Efficiency**: Minimizing API costs
- **Concurrency**: Handling multiple requests
- **Memory**: Efficient resource usage
- **Streaming**: Improving perceived performance

## Streaming for Better UX

Streaming responses improves perceived performance significantly:

```python
import asyncio
from rich.console import Console
from rich.live import Live
import instructor
from openai import AsyncOpenAI
from atomic_agents import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from atomic_agents.context import ChatHistory


console = Console()


async def stream_response(agent: AtomicAgent, message: str):
    """Stream response with live display."""
    input_data = BasicChatInputSchema(chat_message=message)

    with Live("", refresh_per_second=10, console=console) as live:
        current_text = ""
        async for partial in agent.run_async_stream(input_data):
            if partial.chat_message:
                current_text = partial.chat_message
                live.update(current_text)

    return current_text


# Create async agent
async_client = instructor.from_openai(AsyncOpenAI())
agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(
        client=async_client,
        model="gpt-4o-mini",
        history=ChatHistory()
    )
)

# Usage
asyncio.run(stream_response(agent, "Explain quantum computing"))
```

## Concurrent Request Handling

Process multiple requests efficiently:

```python
import asyncio
from typing import List
from atomic_agents import BasicChatInputSchema


async def process_batch(
    agent: AtomicAgent,
    messages: List[str],
    max_concurrent: int = 5
) -> List[str]:
    """Process multiple messages with controlled concurrency."""

    semaphore = asyncio.Semaphore(max_concurrent)
    results = []

    async def process_one(message: str) -> str:
        async with semaphore:
            response = await agent.run_async(
                BasicChatInputSchema(chat_message=message)
            )
            return response.chat_message

    # Create tasks for all messages
    tasks = [process_one(msg) for msg in messages]

    # Execute concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed = []
    for result in results:
        if isinstance(result, Exception):
            processed.append(f"Error: {result}")
        else:
            processed.append(result)

    return processed


# Usage
messages = [
    "What is Python?",
    "Explain machine learning",
    "What is cloud computing?",
    "Describe REST APIs",
    "What is Docker?"
]

results = asyncio.run(process_batch(agent, messages, max_concurrent=3))
```

## Token Optimization

### Efficient System Prompts

Keep system prompts concise:

```python
from atomic_agents.context import SystemPromptGenerator


# Good: Concise, focused prompt
efficient_prompt = SystemPromptGenerator(
    background=["Expert Python developer."],
    steps=["Analyze request.", "Provide solution."],
    output_instructions=["Be concise.", "Include code."]
)

# Avoid: Verbose, redundant prompt
verbose_prompt = SystemPromptGenerator(
    background=[
        "You are an extremely knowledgeable and highly skilled Python developer.",
        "You have many years of experience with Python programming.",
        "You are very helpful and always provide the best answers.",
        "You know all Python libraries and frameworks.",
        # ... more redundant content
    ],
    # ... more verbose content
)
```

### Dynamic Token Limits

Adjust token limits based on query complexity:

```python
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema


class SmartTokenConfig:
    """Dynamically adjusts token limits."""

    SIMPLE_QUERY_TOKENS = 500
    MEDIUM_QUERY_TOKENS = 1500
    COMPLEX_QUERY_TOKENS = 4000

    @classmethod
    def estimate_complexity(cls, message: str) -> int:
        """Estimate appropriate token limit based on query."""
        word_count = len(message.split())

        # Simple heuristics
        if word_count < 10:
            return cls.SIMPLE_QUERY_TOKENS
        elif word_count < 50:
            return cls.MEDIUM_QUERY_TOKENS
        else:
            return cls.COMPLEX_QUERY_TOKENS


def create_optimized_agent(client, message: str) -> AtomicAgent:
    """Create agent with optimized token limit."""
    max_tokens = SmartTokenConfig.estimate_complexity(message)

    return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
        config=AgentConfig(
            client=client,
            model="gpt-4o-mini",
            model_api_parameters={"max_tokens": max_tokens}
        )
    )
```

### Compact Schemas

Design schemas that minimize token usage:

```python
from typing import List
from pydantic import Field
from atomic_agents import BaseIOSchema


# Good: Compact field descriptions
class EfficientOutput(BaseIOSchema):
    answer: str = Field(..., description="Answer")
    confidence: float = Field(..., ge=0, le=1, description="0-1")


# Avoid: Verbose descriptions
class VerboseOutput(BaseIOSchema):
    answer: str = Field(
        ...,
        description="The complete and comprehensive answer to the user's question, including all relevant details and explanations"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="A floating point number between 0.0 and 1.0 representing how confident the model is in its response"
    )
```

## Response Caching

Cache responses for repeated queries:

```python
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class ResponseCache:
    """Simple in-memory response cache."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def _make_key(self, input_data: BaseIOSchema) -> str:
        """Create cache key from input."""
        data_str = json.dumps(input_data.model_dump(), sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def get(self, input_data: BaseIOSchema) -> Optional[Any]:
        """Get cached response if valid."""
        key = self._make_key(input_data)

        if key in self.cache:
            response, timestamp = self.cache[key]
            if datetime.utcnow() - timestamp < self.ttl:
                return response
            else:
                del self.cache[key]

        return None

    def set(self, input_data: BaseIOSchema, response: Any):
        """Cache a response."""
        key = self._make_key(input_data)
        self.cache[key] = (response, datetime.utcnow())

    def clear_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired = [
            k for k, (_, ts) in self.cache.items()
            if now - ts >= self.ttl
        ]
        for k in expired:
            del self.cache[k]


class CachedAgent:
    """Agent wrapper with response caching."""

    def __init__(self, agent: AtomicAgent, cache: ResponseCache = None):
        self.agent = agent
        self.cache = cache or ResponseCache()

    def run(self, input_data: BasicChatInputSchema):
        """Run with caching."""
        # Check cache first
        cached = self.cache.get(input_data)
        if cached is not None:
            return cached

        # Get fresh response
        response = self.agent.run(input_data)

        # Cache the response
        self.cache.set(input_data, response)

        return response


# Usage
cache = ResponseCache(ttl_seconds=1800)  # 30 minute cache
cached_agent = CachedAgent(agent, cache)
```

## Model Selection Strategy

Choose the right model for the task:

```python
from enum import Enum
from typing import Callable


class TaskComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ModelSelector:
    """Selects appropriate model based on task complexity."""

    MODEL_MAP = {
        TaskComplexity.SIMPLE: "gpt-4o-mini",
        TaskComplexity.MEDIUM: "gpt-4o-mini",
        TaskComplexity.COMPLEX: "gpt-4o",
    }

    @classmethod
    def classify_task(cls, message: str) -> TaskComplexity:
        """Classify task complexity."""
        # Simple heuristics (customize based on your use case)
        word_count = len(message.split())

        # Check for complexity indicators
        complex_keywords = ["analyze", "compare", "synthesize", "evaluate", "design"]
        has_complex_keywords = any(kw in message.lower() for kw in complex_keywords)

        if has_complex_keywords or word_count > 100:
            return TaskComplexity.COMPLEX
        elif word_count > 30:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE

    @classmethod
    def get_model(cls, message: str) -> str:
        """Get appropriate model for the message."""
        complexity = cls.classify_task(message)
        return cls.MODEL_MAP[complexity]


def create_adaptive_agent(client, message: str) -> AtomicAgent:
    """Create agent with model selected for task complexity."""
    model = ModelSelector.get_model(message)

    return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
        config=AgentConfig(
            client=client,
            model=model
        )
    )
```

## Connection Pooling

Reuse connections for better performance:

```python
import httpx
import instructor
from openai import AsyncOpenAI


class ConnectionPool:
    """Manages HTTP connection pooling for OpenAI client."""

    def __init__(
        self,
        max_connections: int = 100,
        max_keepalive_connections: int = 20
    ):
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections
            ),
            timeout=httpx.Timeout(30.0)
        )

    def create_openai_client(self, api_key: str) -> AsyncOpenAI:
        """Create OpenAI client with pooled connections."""
        return AsyncOpenAI(
            api_key=api_key,
            http_client=self.http_client
        )

    async def close(self):
        """Close all connections."""
        await self.http_client.aclose()


# Usage
pool = ConnectionPool(max_connections=50)
openai_client = pool.create_openai_client(api_key)
client = instructor.from_openai(openai_client)

# Create multiple agents sharing the connection pool
agent1 = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(client=client, model="gpt-4o-mini")
)
agent2 = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(client=client, model="gpt-4o-mini")
)
```

## Memory Management

### History Pruning

Prevent unbounded history growth:

```python
from atomic_agents.context import ChatHistory


class BoundedHistory(ChatHistory):
    """Chat history with automatic pruning."""

    def __init__(self, max_messages: int = 20):
        super().__init__()
        self.max_messages = max_messages

    def add_message(self, role: str, content):
        """Add message with automatic pruning."""
        super().add_message(role, content)

        # Prune oldest messages if over limit
        history = self.get_history()
        if len(history) > self.max_messages:
            # Keep most recent messages
            self._history = history[-self.max_messages:]

    def get_token_estimate(self) -> int:
        """Estimate tokens in history."""
        total_chars = sum(
            len(str(msg.get("content", "")))
            for msg in self.get_history()
        )
        # Rough estimate: 4 chars per token
        return total_chars // 4


# Usage
bounded_history = BoundedHistory(max_messages=10)
agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(
        client=client,
        model="gpt-4o-mini",
        history=bounded_history
    )
)
```

### Lazy Loading

Load resources only when needed:

```python
from functools import cached_property


class LazyAgentPool:
    """Lazily initializes agents on first use."""

    def __init__(self, client):
        self.client = client
        self._agents = {}

    @cached_property
    def chat_agent(self) -> AtomicAgent:
        """Chat agent - created on first access."""
        return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
            config=AgentConfig(
                client=self.client,
                model="gpt-4o-mini"
            )
        )

    @cached_property
    def analysis_agent(self) -> AtomicAgent:
        """Analysis agent - created on first access."""
        return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
            config=AgentConfig(
                client=self.client,
                model="gpt-4o"
            )
        )


# Agents are only created when first accessed
pool = LazyAgentPool(client)
# No agents created yet

response = pool.chat_agent.run(input_data)  # chat_agent created here
```

## Profiling and Benchmarking

### Request Timing

Measure and track request performance:

```python
import time
from dataclasses import dataclass, field
from typing import List
from statistics import mean, median, stdev


@dataclass
class RequestMetrics:
    """Collects request timing metrics."""

    times: List[float] = field(default_factory=list)

    def record(self, duration: float):
        self.times.append(duration)

    @property
    def count(self) -> int:
        return len(self.times)

    @property
    def avg(self) -> float:
        return mean(self.times) if self.times else 0

    @property
    def p50(self) -> float:
        return median(self.times) if self.times else 0

    @property
    def p95(self) -> float:
        if len(self.times) < 20:
            return max(self.times) if self.times else 0
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]

    def summary(self) -> dict:
        return {
            "count": self.count,
            "avg_ms": self.avg * 1000,
            "p50_ms": self.p50 * 1000,
            "p95_ms": self.p95 * 1000,
        }


class TimedAgent:
    """Agent wrapper with timing metrics."""

    def __init__(self, agent: AtomicAgent):
        self.agent = agent
        self.metrics = RequestMetrics()

    def run(self, input_data):
        start = time.perf_counter()
        try:
            return self.agent.run(input_data)
        finally:
            duration = time.perf_counter() - start
            self.metrics.record(duration)

    def print_metrics(self):
        summary = self.metrics.summary()
        print(f"Requests: {summary['count']}")
        print(f"Avg: {summary['avg_ms']:.0f}ms")
        print(f"P50: {summary['p50_ms']:.0f}ms")
        print(f"P95: {summary['p95_ms']:.0f}ms")


# Usage
timed_agent = TimedAgent(agent)
for _ in range(10):
    timed_agent.run(BasicChatInputSchema(chat_message="test"))

timed_agent.print_metrics()
```

## Performance Checklist

| Optimization | Impact | Effort |
|--------------|--------|--------|
| Streaming responses | High UX impact | Low |
| Concurrent requests | High throughput | Medium |
| Response caching | High for repeated queries | Low |
| Model selection | Cost optimization | Medium |
| Token optimization | Cost reduction | Medium |
| Connection pooling | Latency reduction | Low |
| History pruning | Memory efficiency | Low |

## Summary

Key performance strategies:

1. **Use streaming** for better perceived performance
2. **Process concurrently** when handling multiple requests
3. **Cache responses** for repeated queries
4. **Choose appropriate models** based on task complexity
5. **Optimize tokens** in prompts and schemas
6. **Manage memory** with bounded histories
7. **Profile and measure** to identify bottlenecks
