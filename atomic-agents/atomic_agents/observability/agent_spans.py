"""Agent call and stream spans."""

import asyncio
import contextvars
import functools
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Generator, Iterator

from opentelemetry import context as context_api
from opentelemetry import trace as trace_api
from opentelemetry.trace import Span, Status, StatusCode

from atomic_agents.agents.atomic_agent import AtomicAgent

from . import installation
from .span_attributes import ATTR_STREAM_CLOSED_EARLY, _agent_display_name, _agent_start_attributes, _suppressed
from .span_payloads import _record_failure, _set_input_safely, _set_output_safely

AGENT_SYNC_METHOD = "run"
AGENT_ASYNC_METHOD = "run_async"
AGENT_SYNC_STREAM_METHOD = "run_stream"
AGENT_ASYNC_STREAM_METHOD = "run_async_stream"


_active_agent_span: contextvars.ContextVar[Span | None] = contextvars.ContextVar(
    "atomic_agents_active_agent_span", default=None
)


def _user_input_from_call(args: tuple, kwargs: dict) -> Any:
    return args[0] if args else kwargs.get("user_input")


def _finish_agent_span(span: Any, output: Any) -> None:
    _set_output_safely(span, output)
    span.set_status(Status(StatusCode.OK))


def _mark_closed_early(span: Any, output: Any) -> None:
    span.set_attribute(ATTR_STREAM_CLOSED_EARLY, True)
    _set_output_safely(span, output)


@contextmanager
def _agent_span(agent: AtomicAgent, args: tuple, kwargs: dict) -> Iterator[Span]:
    installed = installation._current_installation()
    with installed.tracer.start_as_current_span(
        f"invoke_agent {_agent_display_name(agent)}",
        attributes=_agent_start_attributes(agent),
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        _set_input_safely(span, _user_input_from_call(args, kwargs))
        token = _active_agent_span.set(span)
        try:
            yield span
        except BaseException as error:
            _record_failure(span, error)
            raise
        finally:
            _active_agent_span.reset(token)


def _trace_agent_call(method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    def traced(agent, *args, **kwargs):
        if _suppressed():
            return wrapped(agent, *args, **kwargs)
        with _agent_span(agent, args, kwargs) as span:
            response = wrapped(agent, *args, **kwargs)
            _finish_agent_span(span, response)
            return response

    return traced


def _trace_agent_async_call(method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    async def traced(agent, *args, **kwargs):
        if _suppressed():
            return await wrapped(agent, *args, **kwargs)
        with _agent_span(agent, args, kwargs) as span:
            response = await wrapped(agent, *args, **kwargs)
            _finish_agent_span(span, response)
            return response

    return traced


def _start_agent_span(agent: AtomicAgent, method_name: str, args: tuple, kwargs: dict) -> Span:
    if _suppressed():
        return trace_api.INVALID_SPAN
    span = installation._current_installation().tracer.start_span(
        f"invoke_agent {_agent_display_name(agent)}",
        attributes=_agent_start_attributes(agent),
    )
    _set_input_safely(span, _user_input_from_call(args, kwargs))
    return span


def _call_within_span(span: Any, function: Callable, *args: Any) -> Any:
    token = context_api.attach(trace_api.set_span_in_context(span))
    agent_token = _active_agent_span.set(span)
    try:
        return function(*args)
    finally:
        _active_agent_span.reset(agent_token)
        context_api.detach(token)


async def _await_within_span(span: Any, awaitable: Any) -> Any:
    token = context_api.attach(trace_api.set_span_in_context(span))
    agent_token = _active_agent_span.set(span)
    try:
        return await awaitable
    finally:
        _active_agent_span.reset(agent_token)
        context_api.detach(token)


class _SyncStreamCursor:
    def __init__(self, span: Any, inner: Generator):
        self.span = span
        self.inner = inner
        self.last: Any = None
        self.final: Any = None

    def advance(self) -> bool:
        try:
            self.last = _call_within_span(self.span, next, self.inner)
        except StopIteration as stop:
            self.final = stop.value
            return False
        return True

    def close_early(self) -> None:
        _call_within_span(self.span, self.inner.close)
        _mark_closed_early(self.span, self.last)
        self.span.set_status(Status(StatusCode.OK))


class _AsyncStreamCursor:
    """Async twin of :class:`_SyncStreamCursor`; async generators carry no return value, so the last partial is the output."""

    def __init__(self, span: Any, inner: AsyncGenerator):
        self.span = span
        self.inner = inner
        self.last: Any = None

    async def advance(self) -> bool:
        try:
            self.last = await _await_within_span(self.span, self.inner.__anext__())
        except StopAsyncIteration:
            return False
        return True

    async def close_early(self) -> None:
        await _await_within_span(self.span, self.inner.aclose())
        _mark_closed_early(self.span, self.last)
        self.span.set_status(Status(StatusCode.OK))

    def mark_cancelled(self) -> None:
        _mark_closed_early(self.span, self.last)


def _trace_agent_stream(method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    def traced(agent, *args, **kwargs):
        span = _start_agent_span(agent, method_name, args, kwargs)
        cursor = _SyncStreamCursor(span, wrapped(agent, *args, **kwargs))
        try:
            while cursor.advance():
                yield cursor.last
            _finish_agent_span(span, cursor.final)
            return cursor.final
        except GeneratorExit:
            cursor.close_early()
            raise
        except BaseException as error:
            _record_failure(span, error)
            raise
        finally:
            span.end()

    return traced


def _trace_agent_async_stream(method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    async def traced(agent, *args, **kwargs):
        span = _start_agent_span(agent, method_name, args, kwargs)
        cursor = _AsyncStreamCursor(span, wrapped(agent, *args, **kwargs))
        try:
            while await cursor.advance():
                yield cursor.last
            _finish_agent_span(span, cursor.last)
        except GeneratorExit:
            await cursor.close_early()
            raise
        except asyncio.CancelledError:
            cursor.mark_cancelled()
            raise
        except BaseException as error:
            _record_failure(span, error)
            raise
        finally:
            span.end()

    return traced


_AGENT_WRAPPERS: Dict[str, Callable[[str, Callable], Callable]] = {
    AGENT_SYNC_METHOD: _trace_agent_call,
    AGENT_ASYNC_METHOD: _trace_agent_async_call,
    AGENT_SYNC_STREAM_METHOD: _trace_agent_stream,
    AGENT_ASYNC_STREAM_METHOD: _trace_agent_async_stream,
}
