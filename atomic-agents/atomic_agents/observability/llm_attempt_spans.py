"""Instructor attempt spans and cumulative agent usage."""

import contextvars
import functools
import logging
import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterator, ParamSpec, Protocol

from opentelemetry import context as context_api, trace as trace_api
from opentelemetry.trace import Span, Status, StatusCode, Tracer
from opentelemetry.util.types import AttributeValue

from atomic_agents.agents.atomic_agent import AtomicAgent

from . import installation
from .span_attributes import _best_effort_attributes, _optional_attributes, _provider_attributes, _without_none
from .span_payloads import _bounded_text, _failure_message, _write_payload
from .tracing_config import TracingConfig

logger = logging.getLogger("atomic_agents.observability.tracing")
_PARAMETERS = ParamSpec("_PARAMETERS")
_RESPONSE_MODEL = "gen_ai.response.model"
_ATTEMPT = "atomic_agents.llm.attempt"
_VALIDATION_ERROR = "atomic_agents.llm.last_validation_error"


class _Usage(Protocol):
    input_tokens: int
    output_tokens: int


class _Response(Protocol):
    model: str
    usage: _Usage


class _HookClient(Protocol):
    def on(self, event: str, handler: Callable[..., None]) -> object:
        """Append a handler without replacing application hooks."""

    def off(self, event: str, handler: Callable[..., None]) -> object:
        """Remove only this handler, preserving application hooks."""


@dataclass
class _AgentRun:
    span: Span
    tracer: Tracer
    config: TracingConfig
    provider: dict[str, AttributeValue]
    attempt_count: int = 0
    open_attempt: Span | None = None
    context_token: contextvars.Token | None = None


_active_run: contextvars.ContextVar[_AgentRun | None] = contextvars.ContextVar("atomic_agents_llm_run", default=None)
_clients: weakref.WeakSet[_HookClient] = weakref.WeakSet()


def _never_raise(handler: Callable[_PARAMETERS, None]) -> Callable[_PARAMETERS, None]:
    @functools.wraps(handler)
    def guarded(*args: _PARAMETERS.args, **kwargs: _PARAMETERS.kwargs) -> None:
        try:
            handler(*args, **kwargs)
        except Exception:
            logger.warning("Instructor tracing hook failed: %s", handler.__name__, exc_info=True)

    return guarded


@_never_raise
def register_client(client: _HookClient) -> None:
    if not hasattr(client, "on") or client in _clients:
        return
    for event, handler in _HANDLERS.items():
        client.on(event, handler)
    _clients.add(client)


@_never_raise
def unregister_clients() -> None:
    for client in list(_clients):
        _unregister_client(client)
    _clients.clear()


@_never_raise
def _unregister_client(client: _HookClient) -> None:
    for event, handler in _HANDLERS.items():
        client.off(event, handler)


def new_run(span: Span, agent: AtomicAgent) -> _AgentRun:
    installed = installation._current_installation()
    register_client(getattr(agent, "client"))
    provider = _best_effort_attributes(
        {"gen_ai.provider.name": lambda: _provider_attributes(agent).get("gen_ai.provider.name")}
    )
    return _AgentRun(span, installed.tracer, installed.config, provider)


@contextmanager
def active_run(run: _AgentRun) -> Iterator[None]:
    token = _active_run.set(None if run.span is trace_api.INVALID_SPAN else run)
    _attach_attempt(run)
    try:
        yield
    finally:
        _detach_attempt(run)
        _active_run.reset(token)


def _attach_attempt(run: _AgentRun) -> None:
    if run.open_attempt is not None:
        run.context_token = context_api.attach(trace_api.set_span_in_context(run.open_attempt))


def _detach_attempt(run: _AgentRun) -> None:
    if run.context_token is not None:
        context_api.detach(run.context_token)
        run.context_token = None


@_never_raise
def finish_attempt(run: _AgentRun, status: Status = Status(StatusCode.UNSET)) -> None:
    if run.open_attempt is None:
        return
    run.open_attempt.set_status(status)
    run.open_attempt.end()
    run.open_attempt = None
    _detach_attempt(run)


@_never_raise
def _completion_kwargs(*args: object, **kwargs: object) -> None:
    run = _active_run.get()
    if run is None:
        return
    finish_attempt(run)
    run.attempt_count += 1
    if not run.config.llm_spans:
        return
    model = str(kwargs["model"]) if kwargs.get("model") is not None else None
    attributes: dict[str, AttributeValue | None] = {
        "gen_ai.operation.name": "chat",
        "gen_ai.request.model": model,
        _ATTEMPT: run.attempt_count,
    }
    attributes.update(run.provider)
    attributes.update(_optional_attributes("LLM", {}))
    run.open_attempt = run.tracer.start_span(f"chat {model}", attributes=_without_none(attributes))
    _attach_attempt(run)


def _usage_attributes(usage: _Usage | None) -> dict[str, int]:
    readers = {
        "input_tokens": getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", None)),
        "output_tokens": getattr(usage, "output_tokens", getattr(usage, "completion_tokens", None)),
        "cache_read.input_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
        "reasoning.output_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
    }
    return {"gen_ai.usage." + key: value for key, value in readers.items() if isinstance(value, int)}


@_never_raise
def _completion_response(response: _Response, **kwargs: object) -> None:
    run = _active_run.get()
    if run is None:
        return
    attributes = _without_none({_RESPONSE_MODEL: getattr(response, "model", None)})
    run.span.set_attributes(attributes)
    _complete_response_attempt(run, response, attributes)


def _complete_response_attempt(run: _AgentRun, response: _Response, attributes: dict[str, AttributeValue]) -> None:
    if run.open_attempt is None:
        return
    run.open_attempt.set_attributes(attributes)
    run.open_attempt.set_attributes(_usage_attributes(getattr(response, "usage", None)))
    finish_attempt(run, Status(StatusCode.OK))


@_never_raise
def _completion_error(error: BaseException, **kwargs: object) -> None:
    run = _active_run.get()
    if run is None or run.open_attempt is None:
        return
    message = _bounded_text(_failure_message(error, run.config), run.config)
    run.open_attempt.set_attribute("error.type", type(error).__qualname__)
    run.open_attempt.record_exception(error, attributes={"exception.message": message, "exception.stacktrace": message})
    finish_attempt(run, Status(StatusCode.ERROR, message))


@_never_raise
def _parse_error(error: BaseException, **kwargs: object) -> None:
    run = _active_run.get()
    if run is None:
        return
    text = "__REDACTED__" if run.config.hide_outputs else _failure_message(error, run.config)
    _write_payload(run.span, _VALIDATION_ERROR, None, text, run.config.hide_outputs, run.config)
    run.span.add_event("validation_error", {_ATTEMPT: run.attempt_count, _VALIDATION_ERROR: _bounded_text(text, run.config)})


@_never_raise
def _completion_usage(usage: _Usage, *, attempt_number: int, **kwargs: object) -> None:
    run = _active_run.get()
    if run is None:
        return
    run.span.set_attributes(_usage_attributes(usage))
    run.span.set_attribute("atomic_agents.llm.attempts", attempt_number)


_HANDLERS: dict[str, Callable[..., None]] = {
    "completion:kwargs": _completion_kwargs,
    "completion:response": _completion_response,
    "completion:error": _completion_error,
    "parse:error": _parse_error,
    "completion:usage": _completion_usage,
}
