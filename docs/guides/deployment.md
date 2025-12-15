# Deployment Guide

This guide covers best practices for deploying Atomic Agents applications to production environments.

## Overview

Deploying AI agents requires attention to:

- **Configuration Management**: Environment-specific settings
- **API Key Security**: Secure credential handling
- **Scaling**: Handling concurrent requests
- **Monitoring**: Observability and alerting
- **Error Handling**: Graceful degradation

## Environment Configuration

### Using Environment Variables

Store configuration in environment variables:

```python
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentDeploymentConfig:
    """Production configuration for agents."""

    # Required
    openai_api_key: str
    model: str

    # Optional with defaults
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: float = 30.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "AgentDeploymentConfig":
        """Load configuration from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        return cls(
            openai_api_key=api_key,
            model=os.getenv("AGENT_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "2048")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            timeout=float(os.getenv("AGENT_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
        )


# Usage
config = AgentDeploymentConfig.from_env()
```

### Configuration File Pattern

For complex deployments, use configuration files:

```python
import os
import json
from pathlib import Path


def load_config(env: str = None) -> dict:
    """Load environment-specific configuration."""
    env = env or os.getenv("DEPLOYMENT_ENV", "development")

    config_path = Path(f"config/{env}.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    # Override with environment variables
    if os.getenv("OPENAI_API_KEY"):
        config["openai_api_key"] = os.getenv("OPENAI_API_KEY")

    return config


# config/production.json example:
# {
#     "model": "gpt-4o",
#     "max_tokens": 4096,
#     "timeout": 60,
#     "rate_limit": {
#         "requests_per_minute": 100,
#         "tokens_per_minute": 100000
#     }
# }
```

## Creating Production-Ready Agents

### Agent Factory Pattern

Create agents with production configuration:

```python
import instructor
import openai
from atomic_agents import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator


class ProductionAgentFactory:
    """Factory for creating production-configured agents."""

    def __init__(self, config: AgentDeploymentConfig):
        self.config = config
        self.client = instructor.from_openai(
            openai.OpenAI(
                api_key=config.openai_api_key,
                timeout=config.timeout,
                max_retries=config.max_retries
            )
        )

    def create_chat_agent(
        self,
        system_prompt: str = None,
        with_history: bool = True
    ) -> AtomicAgent:
        """Create a production chat agent."""

        history = ChatHistory() if with_history else None

        system_prompt_gen = None
        if system_prompt:
            system_prompt_gen = SystemPromptGenerator(
                background=[system_prompt]
            )

        return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
            config=AgentConfig(
                client=self.client,
                model=self.config.model,
                history=history,
                system_prompt_generator=system_prompt_gen,
                model_api_parameters={
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }
            )
        )


# Usage
config = AgentDeploymentConfig.from_env()
factory = ProductionAgentFactory(config)
agent = factory.create_chat_agent(
    system_prompt="You are a helpful customer service agent."
)
```

## FastAPI Integration

Deploy agents as REST APIs:

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from contextlib import asynccontextmanager
import instructor
from openai import AsyncOpenAI
from atomic_agents import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from atomic_agents.context import ChatHistory


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


# Session management (use Redis in production)
sessions: dict[str, ChatHistory] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, ChatHistory]:
    """Get existing session or create new one."""
    import uuid

    if session_id and session_id in sessions:
        return session_id, sessions[session_id]

    new_id = session_id or str(uuid.uuid4())
    sessions[new_id] = ChatHistory()
    return new_id, sessions[new_id]


# Global agent (created on startup)
agent: AtomicAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global agent
    import os

    client = instructor.from_openai(
        AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    )

    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
        config=AgentConfig(
            client=client,
            model="gpt-4o-mini"
        )
    )
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with session management."""
    session_id, history = get_or_create_session(request.session_id)

    # Create agent with session history
    agent.history = history

    try:
        response = await agent.run_async(
            BasicChatInputSchema(chat_message=request.message)
        )
        return ChatResponse(
            response=response.chat_message,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent_loaded": agent is not None}
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for faster dependency installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEPLOYMENT_ENV=production

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AGENT_MODEL=gpt-4o-mini
      - DEPLOYMENT_ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Rate Limiting

Implement rate limiting to control API costs:

```python
import time
from collections import deque
from threading import Lock
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100000
    ):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: deque = deque()
        self.token_usage: deque = deque()  # (timestamp, tokens)
        self.lock = Lock()

    def _clean_old_entries(self, queue: deque, window_seconds: float = 60):
        """Remove entries older than the window."""
        cutoff = time.time() - window_seconds
        while queue and queue[0] < cutoff:
            queue.popleft()

    def can_make_request(self, estimated_tokens: int = 1000) -> tuple[bool, Optional[float]]:
        """Check if request is allowed, return wait time if not."""
        with self.lock:
            now = time.time()

            # Clean old entries
            self._clean_old_entries(self.request_times)

            # Check request rate
            if len(self.request_times) >= self.requests_per_minute:
                wait_time = 60 - (now - self.request_times[0])
                return False, wait_time

            # Check token rate
            self._clean_old_token_entries()
            current_tokens = sum(t[1] for t in self.token_usage)
            if current_tokens + estimated_tokens > self.tokens_per_minute:
                wait_time = 60 - (now - self.token_usage[0][0])
                return False, wait_time

            return True, None

    def _clean_old_token_entries(self):
        """Remove token entries older than 60 seconds."""
        cutoff = time.time() - 60
        while self.token_usage and self.token_usage[0][0] < cutoff:
            self.token_usage.popleft()

    def record_request(self, tokens_used: int = 0):
        """Record a completed request."""
        with self.lock:
            now = time.time()
            self.request_times.append(now)
            if tokens_used > 0:
                self.token_usage.append((now, tokens_used))


class RateLimitedAgent:
    """Agent wrapper with rate limiting."""

    def __init__(self, agent: AtomicAgent, rate_limiter: RateLimiter):
        self.agent = agent
        self.rate_limiter = rate_limiter

    def run(self, input_data, estimated_tokens: int = 1000):
        """Run with rate limiting."""
        can_proceed, wait_time = self.rate_limiter.can_make_request(estimated_tokens)

        if not can_proceed:
            print(f"Rate limited, waiting {wait_time:.1f}s")
            time.sleep(wait_time)

        response = self.agent.run(input_data)
        self.rate_limiter.record_request(estimated_tokens)
        return response


# Usage
rate_limiter = RateLimiter(requests_per_minute=60, tokens_per_minute=100000)
limited_agent = RateLimitedAgent(agent, rate_limiter)
```

## Graceful Shutdown

Handle shutdown signals properly:

```python
import signal
import asyncio
from contextlib import asynccontextmanager


class GracefulShutdown:
    """Manages graceful shutdown for agent services."""

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.active_requests = 0

    def setup_signal_handlers(self):
        """Register signal handlers."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()

    async def wait_for_shutdown(self, timeout: float = 30.0):
        """Wait for active requests to complete."""
        print(f"Waiting for {self.active_requests} active requests...")

        start = asyncio.get_event_loop().time()
        while self.active_requests > 0:
            if asyncio.get_event_loop().time() - start > timeout:
                print(f"Timeout reached, {self.active_requests} requests still active")
                break
            await asyncio.sleep(0.1)

        print("Shutdown complete")

    @asynccontextmanager
    async def request_context(self):
        """Context manager for tracking active requests."""
        self.active_requests += 1
        try:
            yield
        finally:
            self.active_requests -= 1


# Usage with FastAPI
shutdown_handler = GracefulShutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    shutdown_handler.setup_signal_handlers()
    yield
    await shutdown_handler.wait_for_shutdown()


@app.post("/chat")
async def chat(request: ChatRequest):
    async with shutdown_handler.request_context():
        # Process request
        pass
```

## Health Checks

Implement comprehensive health checks:

```python
from datetime import datetime
from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    checks: dict[str, bool]
    details: dict[str, str] | None = None


class HealthChecker:
    """Performs health checks for agent deployments."""

    def __init__(self, agent: AtomicAgent):
        self.agent = agent
        self.last_successful_request: datetime | None = None

    async def check_agent_health(self) -> bool:
        """Verify agent can process requests."""
        try:
            # Simple test request
            response = await self.agent.run_async(
                BasicChatInputSchema(chat_message="health check")
            )
            self.last_successful_request = datetime.utcnow()
            return bool(response.chat_message)
        except Exception:
            return False

    def check_api_key_valid(self) -> bool:
        """Verify API key is configured."""
        import os
        return bool(os.getenv("OPENAI_API_KEY"))

    async def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status."""
        checks = {
            "api_key_configured": self.check_api_key_valid(),
            "agent_responsive": await self.check_agent_health(),
        }

        status = "healthy" if all(checks.values()) else "unhealthy"

        details = {}
        if self.last_successful_request:
            details["last_success"] = self.last_successful_request.isoformat()

        return HealthStatus(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            checks=checks,
            details=details if details else None
        )


# Health check endpoint
@app.get("/health", response_model=HealthStatus)
async def health_check():
    return await health_checker.get_health_status()
```

## Best Practices Summary

| Area | Recommendation |
|------|----------------|
| Configuration | Use environment variables, never hardcode secrets |
| API Keys | Store in secrets manager (AWS Secrets Manager, Vault) |
| Scaling | Use async clients, implement connection pooling |
| Monitoring | Add health checks, log request/response metrics |
| Error Handling | Implement retries, circuit breakers, fallbacks |
| Rate Limiting | Respect API limits, implement client-side limiting |
| Shutdown | Handle signals, drain connections gracefully |

## Deployment Checklist

- [ ] Environment variables configured
- [ ] API keys stored securely
- [ ] Health check endpoint implemented
- [ ] Rate limiting configured
- [ ] Error handling and retries implemented
- [ ] Logging and monitoring set up
- [ ] Graceful shutdown handling
- [ ] Docker/container configuration
- [ ] Load balancing configured (if scaling)
- [ ] Backup/fallback providers configured
