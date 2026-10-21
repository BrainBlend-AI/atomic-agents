"""
OpenInference span emission for ``AtomicAgent`` runs and ``BaseTool`` runs.

Loaded lazily by :class:`atomic_agents.observability.AtomicAgentsInstrumentor`; importing this module
requires the ``observability`` extra.
"""

import asyncio
import contextvars
import functools
import hashlib
import inspect
import json
import logging
from types import FunctionType
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Dict, Generator, List, Optional, Type

from openinference.instrumentation import OITracer, TraceConfig
from openinference.semconv.trace import SpanAttributes
from opentelemetry import context as context_api
from opentelemetry import trace as trace_api
from opentelemetry.trace import Status, StatusCode

from atomic_agents import __version__
from atomic_agents.agents.atomic_agent import AtomicAgent
from atomic_agents.base.base_tool import BaseTool

if TYPE_CHECKING:
    from opentelemetry.trace import TracerProvider

logger = logging.getLogger(__name__)

TRACED_MARKER = "__atomic_agents_traced__"
INHERITED_MARKER = "__atomic_agents_inherited__"
TRACER_NAME = "atomic_agents"

AGENT_SYNC_METHOD = "run"
AGENT_ASYNC_METHOD = "run_async"
AGENT_SYNC_STREAM_METHOD = "run_stream"
AGENT_ASYNC_STREAM_METHOD = "run_async_stream"
TOOL_METHOD_NAMES = ("run", "run_async", "arun")

ATTR_MODEL = "atomic_agents.model"
ATTR_MODE = "atomic_agents.mode"
ATTR_INPUT_SCHEMA = "atomic_agents.input_schema"
ATTR_OUTPUT_SCHEMA = "atomic_agents.output_schema"
ATTR_HISTORY_MESSAGE_COUNT = "atomic_agents.history.message_count"
ATTR_CONTEXT_PROVIDERS = "atomic_agents.context_providers"
ATTR_SYSTEM_PROMPT_SHA256 = "atomic_agents.system_prompt.sha256"
ATTR_STREAM_CLOSED_EARLY = "atomic_agents.stream.closed_early"

_active_tool: contextvars.ContextVar[Optional[BaseTool]] = contextvars.ContextVar("atomic_agents_active_tool", default=None)


class _Installation:
    def __init__(
        self,
        tracer: OITracer,
        tracer_provider: Optional["TracerProvider"],
        config: TraceConfig,
        original_init_subclass: classmethod,
    ):
        self.tracer = tracer
        self.tracer_provider = tracer_provider
        self.config = config
        self.original_init_subclass = original_init_subclass


_installation: Optional[_Installation] = None


def is_installed() -> bool:
    return _installation is not None


def install(*, tracer_provider: Optional["TracerProvider"] = None, config: Optional[TraceConfig] = None) -> None:
    global _installation
    config = config or TraceConfig()
    if _installation is not None:
        _warn_if_reinstalled_differently(_installation, tracer_provider, config)
        return
    tracer = OITracer(trace_api.get_tracer(TRACER_NAME, __version__, tracer_provider), config=config)
    original_init_subclass = BaseTool.__dict__["__init_subclass__"]
    _installation = _Installation(tracer, tracer_provider, config, original_init_subclass)
    _instrument_agent_class(tracer)
    _instrument_existing_tool_classes(tracer)
    _hook_future_tool_classes(tracer, original_init_subclass)


def uninstall() -> None:
    global _installation
    if _installation is None:
        return
    setattr(BaseTool, "__init_subclass__", _installation.original_init_subclass)
    for tool_class in _all_subclasses(BaseTool):
        _restore_tool_class(tool_class)
    for method_name in _AGENT_WRAPPERS:
        _restore_method(AtomicAgent, method_name)
    _installation = None


def _warn_if_reinstalled_differently(
    installed: _Installation, tracer_provider: Optional["TracerProvider"], config: TraceConfig
) -> None:
    same_provider = tracer_provider is None or tracer_provider is installed.tracer_provider
    same_config = config == installed.config
    if not (same_provider and same_config):
        logger.warning(
            "AtomicAgentsInstrumentor is already installed; the new tracer_provider/config are ignored. "
            "Call uninstrument() first to change them."
        )


def _instrument_agent_class(tracer: OITracer) -> None:
    for method_name, wrap in _AGENT_WRAPPERS.items():
        original = AtomicAgent.__dict__[method_name]
        if not getattr(original, TRACED_MARKER, False):
            setattr(AtomicAgent, method_name, _mark_traced(wrap(tracer, method_name, original), original, False))


def _mark_traced(wrapper: Callable, original: Callable, inherited: bool) -> Callable:
    setattr(wrapper, TRACED_MARKER, True)
    setattr(wrapper, INHERITED_MARKER, inherited)
    setattr(wrapper, "__wrapped__", original)
    return wrapper


def _restore_method(owner: Type, method_name: str) -> None:
    current = owner.__dict__.get(method_name)
    if current is None or not getattr(current, TRACED_MARKER, False):
        return
    if getattr(current, INHERITED_MARKER, False):
        delattr(owner, method_name)
    else:
        setattr(owner, method_name, current.__wrapped__)


def _all_subclasses(base: Type) -> List[Type]:
    found: List[Type] = []
    pending = list(base.__subclasses__())
    while pending:
        current = pending.pop(0)
        if current not in found:
            found.append(current)
            pending.extend(current.__subclasses__())
    return found


def _instrument_existing_tool_classes(tracer: OITracer) -> None:
    for tool_class in _all_subclasses(BaseTool):
        _instrument_tool_class(tool_class, tracer)


def _hook_future_tool_classes(tracer: OITracer, original_init_subclass: classmethod) -> None:
    def traced_init_subclass(cls, **kwargs):
        original_init_subclass.__func__(cls, **kwargs)
        _instrument_tool_class(cls, tracer)

    setattr(BaseTool, "__init_subclass__", classmethod(traced_init_subclass))


def _instrument_tool_class(tool_class: Type, tracer: OITracer) -> None:
    for method_name in TOOL_METHOD_NAMES:
        method = inspect.getattr_static(tool_class, method_name, None)
        if _is_traceable_function(method):
            inherited = method_name not in tool_class.__dict__
            setattr(tool_class, method_name, _mark_traced(_trace_tool_method(tracer, method), method, inherited))


def _is_traceable_function(method: Any) -> bool:
    if not isinstance(method, FunctionType) or inspect.isasyncgenfunction(method):
        return False
    if getattr(method, "__isabstractmethod__", False):
        return False
    return not getattr(method, TRACED_MARKER, False)


def _restore_tool_class(tool_class: Type) -> None:
    for method_name in TOOL_METHOD_NAMES:
        _restore_method(tool_class, method_name)


def _agent_display_name(agent: AtomicAgent) -> str:
    return f"{type(agent).__name__}[{agent.input_schema.__name__}, {agent.output_schema.__name__}]"


def _agent_start_attributes(agent: AtomicAgent) -> Dict[str, Any]:
    try:
        return {
            SpanAttributes.AGENT_NAME: _agent_display_name(agent),
            ATTR_MODEL: agent.model,
            ATTR_MODE: getattr(agent.mode, "value", str(agent.mode)),
            ATTR_INPUT_SCHEMA: agent.input_schema.__name__,
            ATTR_OUTPUT_SCHEMA: agent.output_schema.__name__,
            ATTR_HISTORY_MESSAGE_COUNT: len(agent.history.history),
            ATTR_CONTEXT_PROVIDERS: _context_provider_names(agent),
            **_system_prompt_version(agent),
        }
    except Exception as error:
        logger.warning("Could not describe agent for tracing: %s", error)
        return {}


def _context_provider_names(agent: AtomicAgent) -> List[str]:
    providers = getattr(agent.system_prompt_generator, "context_providers", None) or {}
    return sorted(str(name) for name in providers)


def _system_prompt_version(agent: AtomicAgent) -> Dict[str, str]:
    """Hashes only the static prompt sections, so the value identifies the prompt version across turns
    even though context providers change the rendered prompt on every call."""
    generator = agent.system_prompt_generator
    sections = {name: getattr(generator, name, None) for name in ("background", "steps", "output_instructions")}
    if agent.system_role is None or all(value is None for value in sections.values()):
        return {}
    digest = hashlib.sha256(json.dumps(sections, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return {ATTR_SYSTEM_PROMPT_SHA256: digest}


def _user_input_from_call(args: tuple, kwargs: dict) -> Any:
    return args[0] if args else kwargs.get("user_input")


def _set_input_safely(span: Any, value: Any) -> None:
    if value is None:
        return
    try:
        span.set_input(value)
    except Exception as error:
        logger.warning("Could not record span input: %s", error)


def _set_output_safely(span: Any, value: Any) -> None:
    if value is None:
        return
    try:
        span.set_output(value)
    except Exception as error:
        logger.warning("Could not record span output: %s", error)


def _finish_agent_span(span: Any, output: Any) -> None:
    _set_output_safely(span, output)
    span.set_status(Status(StatusCode.OK))


def _mark_closed_early(span: Any, output: Any) -> None:
    span.set_attribute(ATTR_STREAM_CLOSED_EARLY, True)
    _set_output_safely(span, output)


def _record_failure(span: Any, error: BaseException) -> None:
    span.record_exception(error)
    span.set_status(Status(StatusCode.ERROR, str(error)))


def _trace_agent_call(tracer: OITracer, method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    def traced(agent, *args, **kwargs):
        span_name = f"{_agent_display_name(agent)}.{method_name}"
        with tracer.start_as_current_span(
            span_name, openinference_span_kind="agent", attributes=_agent_start_attributes(agent)
        ) as span:
            _set_input_safely(span, _user_input_from_call(args, kwargs))
            response = wrapped(agent, *args, **kwargs)
            _finish_agent_span(span, response)
            return response

    return traced


def _trace_agent_async_call(tracer: OITracer, method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    async def traced(agent, *args, **kwargs):
        span_name = f"{_agent_display_name(agent)}.{method_name}"
        with tracer.start_as_current_span(
            span_name, openinference_span_kind="agent", attributes=_agent_start_attributes(agent)
        ) as span:
            _set_input_safely(span, _user_input_from_call(args, kwargs))
            response = await wrapped(agent, *args, **kwargs)
            _finish_agent_span(span, response)
            return response

    return traced


def _start_agent_span(tracer: OITracer, agent: AtomicAgent, method_name: str, args: tuple, kwargs: dict) -> Any:
    span = tracer.start_span(
        f"{_agent_display_name(agent)}.{method_name}",
        openinference_span_kind="agent",
        attributes=_agent_start_attributes(agent),
    )
    _set_input_safely(span, _user_input_from_call(args, kwargs))
    return span


def _call_within_span(span: Any, function: Callable, *args: Any) -> Any:
    token = context_api.attach(trace_api.set_span_in_context(span))
    try:
        return function(*args)
    finally:
        context_api.detach(token)


async def _await_within_span(span: Any, awaitable: Any) -> Any:
    token = context_api.attach(trace_api.set_span_in_context(span))
    try:
        return await awaitable
    finally:
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


def _trace_agent_stream(tracer: OITracer, method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    def traced(agent, *args, **kwargs):
        span = _start_agent_span(tracer, agent, method_name, args, kwargs)
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


def _trace_agent_async_stream(tracer: OITracer, method_name: str, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    async def traced(agent, *args, **kwargs):
        span = _start_agent_span(tracer, agent, method_name, args, kwargs)
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


def _describe_tool(span: Any, tool: BaseTool) -> None:
    try:
        span.set_tool(
            name=tool.tool_name,
            description=tool.tool_description,
            parameters=tool.input_schema.model_json_schema(),
        )
    except Exception as error:
        logger.warning("Could not describe tool %s for tracing: %s", type(tool).__name__, error)


def _tool_input_from_call(args: tuple, kwargs: dict) -> Any:
    return args[0] if args else kwargs.get("params")


def _trace_tool_method(tracer: OITracer, wrapped: Callable) -> Callable:
    if inspect.iscoroutinefunction(wrapped):
        return _trace_tool_async_method(tracer, wrapped)

    @functools.wraps(wrapped)
    def traced(tool, *args, **kwargs):
        if _active_tool.get() is tool:
            return wrapped(tool, *args, **kwargs)
        with tracer.start_as_current_span(type(tool).__name__, openinference_span_kind="tool") as span:
            _describe_tool(span, tool)
            _set_input_safely(span, _tool_input_from_call(args, kwargs))
            result = _run_as_active_tool(tool, wrapped, args, kwargs)
            _set_output_safely(span, result)
            span.set_status(Status(StatusCode.OK))
            return result

    return traced


def _trace_tool_async_method(tracer: OITracer, wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    async def traced(tool, *args, **kwargs):
        if _active_tool.get() is tool:
            return await wrapped(tool, *args, **kwargs)
        with tracer.start_as_current_span(type(tool).__name__, openinference_span_kind="tool") as span:
            _describe_tool(span, tool)
            _set_input_safely(span, _tool_input_from_call(args, kwargs))
            result = await _await_as_active_tool(tool, wrapped, args, kwargs)
            _set_output_safely(span, result)
            span.set_status(Status(StatusCode.OK))
            return result

    return traced


def _run_as_active_tool(tool: BaseTool, wrapped: Callable, args: tuple, kwargs: dict) -> Any:
    token = _active_tool.set(tool)
    try:
        return wrapped(tool, *args, **kwargs)
    finally:
        _active_tool.reset(token)


async def _await_as_active_tool(tool: BaseTool, wrapped: Callable, args: tuple, kwargs: dict) -> Any:
    token = _active_tool.set(tool)
    try:
        return await wrapped(tool, *args, **kwargs)
    finally:
        _active_tool.reset(token)


_AGENT_WRAPPERS: Dict[str, Callable[[OITracer, str, Callable], Callable]] = {
    AGENT_SYNC_METHOD: _trace_agent_call,
    AGENT_ASYNC_METHOD: _trace_agent_async_call,
    AGENT_SYNC_STREAM_METHOD: _trace_agent_stream,
    AGENT_ASYNC_STREAM_METHOD: _trace_agent_async_stream,
}
