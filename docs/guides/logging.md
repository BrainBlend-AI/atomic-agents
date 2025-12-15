# Logging and Monitoring Guide

This guide covers logging, monitoring, and observability best practices for Atomic Agents applications.

## Overview

Effective logging and monitoring enables:

- **Debugging**: Trace issues in agent behavior
- **Performance Tracking**: Identify bottlenecks
- **Cost Monitoring**: Track API usage and costs
- **Alerting**: Detect anomalies and failures
- **Auditing**: Maintain records for compliance

## Basic Logging Setup

### Configure Python Logging

Set up structured logging for agents:

```python
import logging
import json
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    json_format: bool = True
):
    """Configure logging for agent applications."""

    # Create logger
    logger = logging.getLogger("atomic_agents")
    logger.setLevel(getattr(logging, level.upper()))

    # JSON formatter for structured logs
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_data)

    # Console handler
    console_handler = logging.StreamHandler()
    if json_format:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger


# Usage
logger = setup_logging(level="INFO", json_format=True)
logger.info("Agent initialized", extra={"model": "gpt-4o-mini"})
```

## Agent Logging with Hooks

### Comprehensive Request Logging

Use hooks to log all agent interactions:

```python
import time
import logging
import json
from typing import Any, Optional
from dataclasses import dataclass, field
from atomic_agents import AtomicAgent


logger = logging.getLogger("atomic_agents")


@dataclass
class RequestContext:
    """Tracks request context for logging."""
    request_id: str
    start_time: float
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class AgentLogger:
    """Comprehensive agent logging using hooks."""

    def __init__(self, agent: AtomicAgent):
        self.agent = agent
        self.current_request: Optional[RequestContext] = None

        # Register hooks
        agent.register_hook("completion:kwargs", self._on_request_start)
        agent.register_hook("completion:response", self._on_request_complete)
        agent.register_hook("completion:error", self._on_request_error)
        agent.register_hook("parse:error", self._on_parse_error)

    def _generate_request_id(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]

    def _on_request_start(self, **kwargs):
        """Log request start."""
        self.current_request = RequestContext(
            request_id=self._generate_request_id(),
            start_time=time.time(),
            model=kwargs.get("model")
        )

        logger.info(json.dumps({
            "event": "request_start",
            "request_id": self.current_request.request_id,
            "model": self.current_request.model,
            "message_count": len(kwargs.get("messages", []))
        }))

    def _on_request_complete(self, response, **kwargs):
        """Log successful request."""
        if not self.current_request:
            return

        duration = time.time() - self.current_request.start_time

        log_data = {
            "event": "request_complete",
            "request_id": self.current_request.request_id,
            "duration_ms": round(duration * 1000, 2),
            "model": self.current_request.model
        }

        # Add token usage if available
        if hasattr(response, "usage"):
            log_data["tokens"] = {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            }

        logger.info(json.dumps(log_data))
        self.current_request = None

    def _on_request_error(self, error, **kwargs):
        """Log request error."""
        log_data = {
            "event": "request_error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }

        if self.current_request:
            log_data["request_id"] = self.current_request.request_id
            log_data["duration_ms"] = round(
                (time.time() - self.current_request.start_time) * 1000, 2
            )

        logger.error(json.dumps(log_data))
        self.current_request = None

    def _on_parse_error(self, error):
        """Log validation error."""
        logger.warning(json.dumps({
            "event": "parse_error",
            "request_id": self.current_request.request_id if self.current_request else None,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }))


# Usage
agent_logger = AgentLogger(agent)
# Logs are automatically created for all agent operations
```

## Metrics Collection

### Token and Cost Tracking

Track API usage and costs:

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
import threading


@dataclass
class UsageMetrics:
    """Tracks API usage metrics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    errors: int = 0
    total_latency_ms: float = 0

    # Cost per 1K tokens (example rates)
    COST_PER_1K_INPUT = 0.00015  # gpt-4o-mini input
    COST_PER_1K_OUTPUT = 0.0006  # gpt-4o-mini output

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.requests if self.requests > 0 else 0

    @property
    def estimated_cost(self) -> float:
        input_cost = (self.prompt_tokens / 1000) * self.COST_PER_1K_INPUT
        output_cost = (self.completion_tokens / 1000) * self.COST_PER_1K_OUTPUT
        return input_cost + output_cost

    @property
    def error_rate(self) -> float:
        return self.errors / self.requests if self.requests > 0 else 0


class MetricsCollector:
    """Collects and aggregates agent metrics."""

    def __init__(self):
        self.current_metrics = UsageMetrics()
        self.hourly_metrics: Dict[str, UsageMetrics] = {}
        self.lock = threading.Lock()

    def record_request(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        error: bool = False
    ):
        """Record a request's metrics."""
        with self.lock:
            # Update current metrics
            self.current_metrics.prompt_tokens += prompt_tokens
            self.current_metrics.completion_tokens += completion_tokens
            self.current_metrics.total_tokens += prompt_tokens + completion_tokens
            self.current_metrics.requests += 1
            self.current_metrics.total_latency_ms += latency_ms
            if error:
                self.current_metrics.errors += 1

            # Update hourly bucket
            hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
            if hour_key not in self.hourly_metrics:
                self.hourly_metrics[hour_key] = UsageMetrics()

            hourly = self.hourly_metrics[hour_key]
            hourly.prompt_tokens += prompt_tokens
            hourly.completion_tokens += completion_tokens
            hourly.total_tokens += prompt_tokens + completion_tokens
            hourly.requests += 1
            hourly.total_latency_ms += latency_ms
            if error:
                hourly.errors += 1

    def get_summary(self) -> dict:
        """Get metrics summary."""
        with self.lock:
            return {
                "total_requests": self.current_metrics.requests,
                "total_tokens": self.current_metrics.total_tokens,
                "avg_latency_ms": round(self.current_metrics.avg_latency_ms, 2),
                "error_rate": round(self.current_metrics.error_rate * 100, 2),
                "estimated_cost_usd": round(self.current_metrics.estimated_cost, 4)
            }

    def get_hourly_summary(self, hours: int = 24) -> List[dict]:
        """Get hourly metrics for the last N hours."""
        with self.lock:
            summaries = []
            for hour_key, metrics in sorted(self.hourly_metrics.items())[-hours:]:
                summaries.append({
                    "hour": hour_key,
                    "requests": metrics.requests,
                    "tokens": metrics.total_tokens,
                    "cost_usd": round(metrics.estimated_cost, 4)
                })
            return summaries


# Global metrics collector
metrics = MetricsCollector()


def on_completion_response(response, **kwargs):
    """Hook to record metrics."""
    if hasattr(response, "usage"):
        metrics.record_request(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=0  # Calculate from request timing
        )


# Register with agent
agent.register_hook("completion:response", on_completion_response)
```

## Monitoring Dashboard

### FastAPI Metrics Endpoint

Expose metrics via HTTP:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


app = FastAPI()


class MetricsSummary(BaseModel):
    total_requests: int
    total_tokens: int
    avg_latency_ms: float
    error_rate: float
    estimated_cost_usd: float


class HourlySummary(BaseModel):
    hour: str
    requests: int
    tokens: int
    cost_usd: float


@app.get("/metrics", response_model=MetricsSummary)
async def get_metrics():
    """Get current metrics summary."""
    return metrics.get_summary()


@app.get("/metrics/hourly", response_model=List[HourlySummary])
async def get_hourly_metrics(hours: int = 24):
    """Get hourly metrics breakdown."""
    return metrics.get_hourly_summary(hours)


@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    summary = metrics.get_summary()

    output = []
    output.append(f"# HELP agent_requests_total Total agent requests")
    output.append(f"# TYPE agent_requests_total counter")
    output.append(f"agent_requests_total {summary['total_requests']}")

    output.append(f"# HELP agent_tokens_total Total tokens used")
    output.append(f"# TYPE agent_tokens_total counter")
    output.append(f"agent_tokens_total {summary['total_tokens']}")

    output.append(f"# HELP agent_latency_ms Average latency in ms")
    output.append(f"# TYPE agent_latency_ms gauge")
    output.append(f"agent_latency_ms {summary['avg_latency_ms']}")

    output.append(f"# HELP agent_error_rate Error rate percentage")
    output.append(f"# TYPE agent_error_rate gauge")
    output.append(f"agent_error_rate {summary['error_rate']}")

    return "\n".join(output)
```

## Distributed Tracing

### OpenTelemetry Integration

Add distributed tracing for complex systems:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def setup_tracing(service_name: str = "atomic-agents"):
    """Configure OpenTelemetry tracing."""

    # Set up tracer provider
    provider = TracerProvider()

    # Add OTLP exporter (for Jaeger, Zipkin, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",
        insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(provider)

    # Instrument HTTP client (used by OpenAI SDK)
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer(service_name)


tracer = setup_tracing()


class TracedAgent:
    """Agent wrapper with distributed tracing."""

    def __init__(self, agent: AtomicAgent):
        self.agent = agent

    def run(self, input_data):
        """Run with tracing span."""
        with tracer.start_as_current_span("agent.run") as span:
            span.set_attribute("agent.model", self.agent.model)
            span.set_attribute("input.length", len(str(input_data)))

            try:
                response = self.agent.run(input_data)
                span.set_attribute("output.length", len(str(response)))
                span.set_status(trace.Status(trace.StatusCode.OK))
                return response
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# Usage
traced_agent = TracedAgent(agent)
```

## Alerting

### Alert Conditions

Define alert conditions for monitoring:

```python
from dataclasses import dataclass
from typing import Callable, List, Optional
from datetime import datetime
import logging


logger = logging.getLogger("alerts")


@dataclass
class AlertCondition:
    """Defines an alert condition."""
    name: str
    check: Callable[[], bool]
    message: str
    severity: str = "warning"  # warning, error, critical


class AlertManager:
    """Manages alert conditions and notifications."""

    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.conditions: List[AlertCondition] = []
        self.last_alerts: dict = {}  # Prevent alert spam

    def add_condition(self, condition: AlertCondition):
        """Add an alert condition."""
        self.conditions.append(condition)

    def check_alerts(self) -> List[AlertCondition]:
        """Check all conditions and return triggered alerts."""
        triggered = []
        now = datetime.utcnow()

        for condition in self.conditions:
            # Check cooldown (don't alert more than once per 5 minutes)
            last_alert = self.last_alerts.get(condition.name)
            if last_alert and (now - last_alert).seconds < 300:
                continue

            if condition.check():
                triggered.append(condition)
                self.last_alerts[condition.name] = now
                self._send_alert(condition)

        return triggered

    def _send_alert(self, condition: AlertCondition):
        """Send alert notification."""
        logger.warning(f"ALERT [{condition.severity}]: {condition.name} - {condition.message}")
        # Add integration with Slack, PagerDuty, etc.


# Create alert manager with conditions
alerts = AlertManager(metrics)

# High error rate alert
alerts.add_condition(AlertCondition(
    name="high_error_rate",
    check=lambda: metrics.current_metrics.error_rate > 0.1,
    message="Error rate exceeds 10%",
    severity="error"
))

# High latency alert
alerts.add_condition(AlertCondition(
    name="high_latency",
    check=lambda: metrics.current_metrics.avg_latency_ms > 5000,
    message="Average latency exceeds 5 seconds",
    severity="warning"
))

# Cost threshold alert
alerts.add_condition(AlertCondition(
    name="cost_threshold",
    check=lambda: metrics.current_metrics.estimated_cost > 100,
    message="Estimated cost exceeds $100",
    severity="warning"
))
```

## Log Analysis Patterns

### Structured Log Queries

Design logs for easy querying:

```python
import json
from datetime import datetime


class StructuredLogger:
    """Logger optimized for log analysis tools."""

    def __init__(self, service: str, environment: str):
        self.service = service
        self.environment = environment
        self.logger = logging.getLogger(service)

    def _log(self, level: str, event: str, **extra):
        """Create structured log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service,
            "environment": self.environment,
            "level": level,
            "event": event,
            **extra
        }

        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))

    def info(self, event: str, **extra):
        self._log("INFO", event, **extra)

    def warning(self, event: str, **extra):
        self._log("WARNING", event, **extra)

    def error(self, event: str, **extra):
        self._log("ERROR", event, **extra)

    # Specialized log methods
    def log_request(self, request_id: str, model: str, user_id: str = None):
        self.info(
            "agent_request_start",
            request_id=request_id,
            model=model,
            user_id=user_id
        )

    def log_response(
        self,
        request_id: str,
        duration_ms: float,
        tokens: int,
        cost: float
    ):
        self.info(
            "agent_request_complete",
            request_id=request_id,
            duration_ms=duration_ms,
            tokens=tokens,
            cost_usd=cost
        )

    def log_error(self, request_id: str, error_type: str, error_message: str):
        self.error(
            "agent_request_failed",
            request_id=request_id,
            error_type=error_type,
            error_message=error_message
        )


# Usage
log = StructuredLogger(service="my-agent", environment="production")
log.log_request(request_id="abc123", model="gpt-4o-mini", user_id="user456")
```

## Best Practices

### Logging Guidelines

| What to Log | Why | Example |
|-------------|-----|---------|
| Request IDs | Trace requests | `request_id: "abc123"` |
| Timestamps | Timeline analysis | `timestamp: "2024-01-15T10:30:00Z"` |
| Model used | Cost attribution | `model: "gpt-4o-mini"` |
| Token counts | Usage tracking | `tokens: {"prompt": 100, "completion": 50}` |
| Latency | Performance monitoring | `duration_ms: 1523` |
| Error types | Debugging | `error_type: "ValidationError"` |
| User IDs | Audit trails | `user_id: "user456"` |

### What NOT to Log

- Full request/response content (privacy)
- API keys or secrets
- Personal identifiable information (PII)
- Sensitive business data

## Summary

| Component | Purpose | Tools |
|-----------|---------|-------|
| Logging | Debug & audit | Python logging, structured JSON |
| Metrics | Performance tracking | Custom collectors, Prometheus |
| Tracing | Request flow | OpenTelemetry, Jaeger |
| Alerting | Issue detection | Custom rules, PagerDuty |
| Dashboards | Visualization | Grafana, custom endpoints |

Implement logging and monitoring from the start - it's much harder to add later.
