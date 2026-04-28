# Hooks

## Contents
- The five events
- Registration and management
- Telemetry pattern
- Validation-error inspection
- Retry pattern
- Production logging
- Common mistakes

Atomic Agents surfaces Instructor's hook system on every agent. Use hooks for telemetry, validation-error inspection, retries, and logging rather than wrapping `run()` in `try/except`.

Full working example in the repo: `atomic-examples/hooks-example/hooks_example/main.py`.

## The five events

| Event | Fires | Handler receives |
|---|---|---|
| `completion:kwargs` | Before the model call | Full kwargs dict (model, messages, `response_model`, tools, …) |
| `completion:response` | After a successful model response | Raw completion object |
| `completion:error` | On any provider/HTTP error | Exception instance |
| `parse:error` | When Pydantic validation fails on the parsed response | `ValidationError` instance |
| `completion:last_attempt` | On the final retry before `run()` raises | Exception instance |

`parse:error` fires *before* Instructor retries. If Instructor's built-in retry succeeds, `completion:response` fires and `parse:error` does not re-fire for that call.

## Registration and management

```python
def on_response(resp): ...
def on_error(err):     ...

agent.register_hook("completion:response", on_response)
agent.register_hook("completion:error",    on_error)

# Remove one handler
agent.unregister_hook("completion:error", on_error)

# Clear all handlers for an event
agent.clear_hooks("completion:error")

# Clear every registered handler
agent.clear_hooks()

# Toggle without unregistering
agent.disable_hooks()
agent.run(input_data)          # hooks skipped
agent.enable_hooks()

agent.hooks_enabled            # bool property, not a method
```

Keep handlers cheap. They run synchronously in the request path — a slow logger delays every `run()`.

## Telemetry pattern

```python
import time

metrics = {"requests": 0, "errors": 0, "parse_errors": 0, "total_ms": 0.0}
_t0: float | None = None

def on_kwargs(**_):
    global _t0
    _t0 = time.perf_counter()
    metrics["requests"] += 1

def on_response(_resp, **_):
    metrics["total_ms"] += (time.perf_counter() - _t0) * 1000

def on_parse_error(_err, **_):
    metrics["parse_errors"] += 1

def on_error(_err, **_):
    metrics["errors"] += 1

agent.register_hook("completion:kwargs",   on_kwargs)
agent.register_hook("completion:response", on_response)
agent.register_hook("parse:error",         on_parse_error)
agent.register_hook("completion:error",    on_error)
```

## Validation-error inspection

```python
from pydantic import ValidationError

def on_parse_error(error):
    if isinstance(error, ValidationError):
        for err in error.errors():
            loc  = ".".join(map(str, err["loc"]))
            kind = err["type"]
            msg  = err["msg"]
            logger.warning("LLM produced invalid field %s (%s): %s", loc, kind, msg)
```

Pydantic's `err["type"]` (`"missing"`, `"string_too_short"`, `"literal_error"`, …) identifies what the model got wrong. Use it to sharpen field `description=` text or tighten `Literal` sets.

## Retry pattern

Instructor already retries `parse:error` internally (`max_retries` on the client). For provider-level failures (429, 5xx, timeouts) use hooks + an outer loop:

```python
import time

class Retrier:
    def __init__(self, max_attempts=3, base_delay=1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.attempt = 0

    def on_error(self, error):
        self.attempt += 1
        msg = str(error).lower()
        if self.attempt < self.max_attempts and any(
            t in msg for t in ("rate limit", "timeout", "503", "502", "504")
        ):
            time.sleep(self.base_delay * (2 ** (self.attempt - 1)))

    def on_success(self, _resp):
        self.attempt = 0

def run_with_retry(agent, inp, r: Retrier):
    r.attempt = 0
    while True:
        try:
            return agent.run(inp)
        except Exception:
            if r.attempt >= r.max_attempts:
                raise

r = Retrier()
agent.register_hook("completion:error",    r.on_error)
agent.register_hook("completion:response", r.on_success)
```

## Production logging

One handler per concern; register them at agent construction time.

```python
import logging, uuid
log = logging.getLogger("agent")

class RequestLogger:
    def __init__(self):
        self.request_id: str = ""

    def on_kwargs(self, **kwargs):
        self.request_id = str(uuid.uuid4())
        log.info("agent.call", extra={"request_id": self.request_id, "model": kwargs.get("model")})

    def on_response(self, _resp):
        log.info("agent.ok", extra={"request_id": self.request_id})

    def on_error(self, error):
        log.error("agent.error", extra={"request_id": self.request_id, "error": str(error)})

rl = RequestLogger()
agent.register_hook("completion:kwargs",   rl.on_kwargs)
agent.register_hook("completion:response", rl.on_response)
agent.register_hook("completion:error",    rl.on_error)
```

Don't log full request/response payloads — they can contain user PII and inflate log volume. Log the `request_id` + model + timing and correlate with upstream logs.

## Common mistakes

- Raising from inside a hook — hook exceptions propagate and can mask the original error. Log and return.
- Doing slow I/O in a hook — blocks every `run()`. Push to a queue if the work is heavy.
- Assuming `parse:error` fires on every validation failure — Instructor's internal retry may resolve it before the handler sees a definitive failure. Pair with `completion:last_attempt` for final-failure signals.
- Using `agent.hooks_enabled()` — it is a read-only **property**, not a method. Drop the parentheses.
- Registering the same handler twice — duplicates run twice. `unregister_hook` the old one first.
