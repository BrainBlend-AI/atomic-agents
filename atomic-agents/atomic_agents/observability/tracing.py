"""
OpenTelemetry span emission for ``AtomicAgent`` runs and ``BaseTool`` runs.

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
from contextlib import contextmanager
from dataclasses import dataclass, replace
import os
from types import FunctionType
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Dict, Generator, List, Optional, Type, Protocol, Iterator

from opentelemetry import context as context_api
from opentelemetry import trace as trace_api
from opentelemetry.trace import Span, Status, StatusCode, Tracer
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

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

ATTR_OPERATION = "gen_ai.operation.name"
ATTR_AGENT_NAME = "gen_ai.agent.name"
ATTR_REQUEST_MODEL = "gen_ai.request.model"
ATTR_PROVIDER_NAME = "gen_ai.provider.name"
ATTR_CONVERSATION_ID = "gen_ai.conversation.id"
ATTR_TOOL_NAME = "gen_ai.tool.name"
ATTR_TOOL_DESCRIPTION = "gen_ai.tool.description"
ATTR_TOOL_TYPE = "gen_ai.tool.type"
ATTR_TOOL_ARGUMENTS = "gen_ai.tool.call.arguments"
ATTR_TOOL_RESULT = "gen_ai.tool.call.result"
ATTR_SPAN_KIND = "openinference.span.kind"
ATTR_INPUT_VALUE = "input.value"
ATTR_INPUT_MIME_TYPE = "input.mime_type"
ATTR_OUTPUT_VALUE = "output.value"
ATTR_OUTPUT_MIME_TYPE = "output.mime_type"
ATTR_OI_AGENT_NAME = "agent.name"
ATTR_OI_TOOL_NAME = "tool.name"
ATTR_OI_TOOL_DESCRIPTION = "tool.description"
ATTR_TOOL_PARAMETERS = "tool.parameters"
ATTR_SESSION_ID = "session.id"
ATTR_INPUT = "atomic_agents.input"
ATTR_OUTPUT = "atomic_agents.output"
ATTR_AGENT_CLASS = "atomic_agents.agent.class"
ATTR_ERROR_TYPE = "error.type"


class PayloadVisibility(Protocol):
    hide_inputs: bool
    hide_outputs: bool


@dataclass(frozen=True)
class TracingConfig:
    hide_inputs: bool = False
    hide_outputs: bool = False
    max_attribute_length: int = 4096
    openinference_attributes: bool | None = None
    llm_spans: bool = True

    @classmethod
    def from_environment(cls) -> "TracingConfig":
        return cls(
            hide_inputs=os.environ.get("OPENINFERENCE_HIDE_INPUTS", "").lower() in ("true", "1"),
            hide_outputs=os.environ.get("OPENINFERENCE_HIDE_OUTPUTS", "").lower() in ("true", "1"),
            max_attribute_length=int(os.environ.get("ATOMIC_AGENTS_TRACE_MAX_ATTRIBUTE_LENGTH", "4096")),
        )

    @classmethod
    def coerce(cls, config: "TracingConfig | PayloadVisibility | None") -> "TracingConfig":
        if config is None:
            return cls.from_environment()
        if isinstance(config, cls):
            return config
        return cls(hide_inputs=config.hide_inputs, hide_outputs=config.hide_outputs)


def _import_context_attributes() -> Callable[[], dict[str, AttributeValue]] | None:
    try:
        from openinference.instrumentation import get_attributes_from_context
    except ImportError:
        return None
    from atomic_agents.observability import _openinference_is_too_old

    if _openinference_is_too_old():
        logger.warning("OpenInference context attributes disabled: 0.1.38 or newer is required.")
        return None
    return lambda: dict(get_attributes_from_context())


def _context_attributes() -> dict[str, AttributeValue]:
    reader = _current_installation().context_attributes
    return reader() if reader is not None else {}


def _current_installation() -> "_Installation":
    assert _installation is not None
    return _installation


def _suppressed() -> bool:
    return bool(context_api.get_value("suppress_instrumentation"))


_conversation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("atomic_agents_conversation_id", default=None)
_active_agent_span: contextvars.ContextVar[Span | None] = contextvars.ContextVar(
    "atomic_agents_active_agent_span", default=None
)


@contextmanager
def using_conversation(conversation_id: str) -> Iterator[None]:
    token = _conversation_id.set(conversation_id)
    try:
        yield
    finally:
        _conversation_id.reset(token)


_active_tool: contextvars.ContextVar[Optional[BaseTool]] = contextvars.ContextVar("atomic_agents_active_tool", default=None)


class _Installation:
    def __init__(
        self,
        tracer: Tracer,
        tracer_provider: Optional["TracerProvider"],
        config: TracingConfig,
        original_init_subclass: classmethod,
        context_attributes: Callable[[], dict[str, AttributeValue]] | None,
    ):
        self.context_attributes = context_attributes
        self.tracer = tracer
        self.tracer_provider = tracer_provider
        self.config = config
        self.original_init_subclass = original_init_subclass


_installation: Optional[_Installation] = None


def is_installed() -> bool:
    return _installation is not None


def install(
    *, tracer_provider: Optional["TracerProvider"] = None, config: TracingConfig | PayloadVisibility | None = None
) -> None:
    global _installation
    config = TracingConfig.coerce(config)
    if _installation is not None:
        if config.openinference_attributes is None:
            config = replace(config, openinference_attributes=_installation.config.openinference_attributes)
        _replace_installation(_installation, tracer_provider, config)
        return
    context_attributes = _import_context_attributes()
    if config.openinference_attributes is None:
        config = replace(config, openinference_attributes=context_attributes is not None)
    tracer = trace_api.get_tracer(TRACER_NAME, __version__, tracer_provider)
    original_init_subclass = BaseTool.__dict__["__init_subclass__"]
    _installation = _Installation(tracer, tracer_provider, config, original_init_subclass, context_attributes)
    _instrument_agent_class()
    _instrument_existing_tool_classes()
    _hook_future_tool_classes(original_init_subclass)


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


def _replace_installation(
    installed: _Installation, tracer_provider: Optional["TracerProvider"], config: TracingConfig
) -> None:
    if tracer_provider is installed.tracer_provider and config == installed.config:
        return
    installed.tracer = trace_api.get_tracer(TRACER_NAME, __version__, tracer_provider)
    installed.tracer_provider = tracer_provider
    installed.config = config
    installed.context_attributes = _import_context_attributes()
    logger.warning(
        "AtomicAgentsInstrumentor tracer provider/config replaced; "
        "in-flight spans finish on the provider they started with."
    )


def _instrument_agent_class() -> None:
    for method_name, wrap in _AGENT_WRAPPERS.items():
        original = AtomicAgent.__dict__[method_name]
        if not getattr(original, TRACED_MARKER, False):
            setattr(AtomicAgent, method_name, _mark_traced(wrap(method_name, original), original, False))


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


def _instrument_existing_tool_classes() -> None:
    for tool_class in _all_subclasses(BaseTool):
        _instrument_tool_class(tool_class)


def _hook_future_tool_classes(original_init_subclass: classmethod) -> None:
    def traced_init_subclass(cls, **kwargs):
        original_init_subclass.__func__(cls, **kwargs)
        _instrument_tool_class(cls)

    setattr(BaseTool, "__init_subclass__", classmethod(traced_init_subclass))


def _instrument_tool_class(tool_class: Type) -> None:
    for method_name in TOOL_METHOD_NAMES:
        method = inspect.getattr_static(tool_class, method_name, None)
        if _is_traceable_function(method):
            inherited = method_name not in tool_class.__dict__
            setattr(tool_class, method_name, _mark_traced(_trace_tool_method(method), method, inherited))


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
    return agent.name or type(agent).__name__


def _agent_class_name(agent: AtomicAgent) -> str:
    return f"{type(agent).__name__}[{agent.input_schema.__name__}, {agent.output_schema.__name__}]"


def _agent_start_attributes(agent: AtomicAgent) -> Dict[str, Any]:
    try:
        return {
            ATTR_OPERATION: "invoke_agent",
            ATTR_AGENT_NAME: _agent_display_name(agent),
            ATTR_AGENT_CLASS: _agent_class_name(agent),
            ATTR_REQUEST_MODEL: agent.model,
            **_provider_attributes(agent),
            **_optional_attributes("AGENT", {ATTR_OI_AGENT_NAME: _agent_display_name(agent)}),
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


def _provider_attributes(agent: AtomicAgent) -> dict[str, str]:
    provider = getattr(getattr(agent.client, "provider", None), "value", None)
    return {ATTR_PROVIDER_NAME: provider} if isinstance(provider, str) else {}


def _optional_attributes(kind: str, attributes: dict[str, AttributeValue]) -> dict[str, AttributeValue]:
    context = _context_attributes()
    conversation = _conversation_attributes(context)
    if not _current_installation().config.openinference_attributes:
        return conversation
    return {ATTR_SPAN_KIND: kind, **attributes, **context, **conversation}


def _conversation_attributes(context: dict[str, AttributeValue]) -> dict[str, AttributeValue]:
    conversation_id: AttributeValue | None = _conversation_id.get()
    if conversation_id is None:
        conversation_id = context.get(ATTR_SESSION_ID)
    if conversation_id is None:
        return {}
    attributes = {ATTR_CONVERSATION_ID: conversation_id}
    if _current_installation().config.openinference_attributes:
        attributes[ATTR_SESSION_ID] = conversation_id
    return attributes


def _record_payload(
    span: Span, key_pairs: tuple[tuple[str, str | None], ...], value: object, hide: bool, config: TracingConfig
) -> None:
    if value is None:
        return
    try:
        serialized = value.model_dump_json() if isinstance(value, BaseModel) else json.dumps(value, default=str)
    except Exception as error:
        logger.warning("Could not serialize tracing payload: %s", error)
        return
    for key, mime_key in key_pairs:
        _write_payload(span, key, mime_key, serialized, hide, config)


def _write_payload(span: Span, key: str, mime_key: str | None, serialized: str, hide: bool, config: TracingConfig) -> None:
    if hide:
        span.set_attribute(key, "__REDACTED__")
        return
    if len(serialized) > config.max_attribute_length:
        span.set_attribute(key + ".original_length", len(serialized))
        serialized = serialized[: config.max_attribute_length] + "...[truncated]"
    span.set_attribute(key, serialized)
    if mime_key is not None:
        span.set_attribute(mime_key, "application/json")


def _payload_keys(primary: str, output: bool) -> tuple[tuple[str, str | None], ...]:
    keys: tuple[tuple[str, str | None], ...] = ((primary, None),)
    if _current_installation().config.openinference_attributes:
        keys += ((ATTR_OUTPUT_VALUE, ATTR_OUTPUT_MIME_TYPE),) if output else ((ATTR_INPUT_VALUE, ATTR_INPUT_MIME_TYPE),)
    return keys


def _set_input_safely(span: Span, value: object, primary: str = ATTR_INPUT) -> None:
    config = _current_installation().config
    _record_payload(span, _payload_keys(primary, False), value, config.hide_inputs, config)


def _set_output_safely(span: Span, value: object, primary: str = ATTR_OUTPUT) -> None:
    config = _current_installation().config
    _record_payload(span, _payload_keys(primary, True), value, config.hide_outputs, config)


def _finish_agent_span(span: Any, output: Any) -> None:
    _set_output_safely(span, output)
    span.set_status(Status(StatusCode.OK))


def _mark_closed_early(span: Any, output: Any) -> None:
    span.set_attribute(ATTR_STREAM_CLOSED_EARLY, True)
    _set_output_safely(span, output)


def _record_failure(span: Any, error: BaseException) -> None:
    span.set_attribute(ATTR_ERROR_TYPE, type(error).__qualname__)
    span.record_exception(error)
    span.set_status(Status(StatusCode.ERROR, str(error)))


@contextmanager
def _agent_span(agent: AtomicAgent, args: tuple, kwargs: dict) -> Iterator[Span]:
    installed = _current_installation()
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
    span = _current_installation().tracer.start_span(
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


def _tool_start_attributes(tool: BaseTool) -> dict[str, AttributeValue]:
    attributes: dict[str, AttributeValue] = {
        ATTR_OPERATION: "execute_tool",
        ATTR_TOOL_NAME: type(tool).__name__,
        ATTR_TOOL_TYPE: "function",
        **_optional_attributes("TOOL", {}),
    }
    try:
        attributes[ATTR_TOOL_DESCRIPTION] = tool.tool_description
        if _current_installation().config.openinference_attributes:
            attributes.update(
                {
                    ATTR_OI_TOOL_NAME: tool.tool_name,
                    ATTR_OI_TOOL_DESCRIPTION: tool.tool_description,
                    ATTR_TOOL_PARAMETERS: json.dumps(tool.input_schema.model_json_schema()),
                }
            )
    except Exception as error:
        logger.warning("Could not describe tool %s for tracing: %s", type(tool).__name__, error)
    return attributes


@contextmanager
def _tool_span(tool: BaseTool, args: tuple, kwargs: dict) -> Iterator[Span]:
    with _current_installation().tracer.start_as_current_span(
        f"execute_tool {type(tool).__name__}",
        attributes=_tool_start_attributes(tool),
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        _set_input_safely(span, _tool_input_from_call(args, kwargs), ATTR_TOOL_ARGUMENTS)
        try:
            yield span
        except BaseException as error:
            _record_failure(span, error)
            raise


def _tool_input_from_call(args: tuple, kwargs: dict) -> Any:
    return args[0] if args else kwargs.get("params")


def _trace_tool_method(wrapped: Callable) -> Callable:
    if inspect.iscoroutinefunction(wrapped):
        return _trace_tool_async_method(wrapped)

    @functools.wraps(wrapped)
    def traced(tool, *args, **kwargs):
        if _active_tool.get() is tool or _suppressed():
            return wrapped(tool, *args, **kwargs)
        with _tool_span(tool, args, kwargs) as span:
            result = _run_as_active_tool(tool, wrapped, args, kwargs)
            _set_output_safely(span, result, ATTR_TOOL_RESULT)
            span.set_status(Status(StatusCode.OK))
            return result

    return traced


def _trace_tool_async_method(wrapped: Callable) -> Callable:
    @functools.wraps(wrapped)
    async def traced(tool, *args, **kwargs):
        if _active_tool.get() is tool or _suppressed():
            return await wrapped(tool, *args, **kwargs)
        with _tool_span(tool, args, kwargs) as span:
            result = await _await_as_active_tool(tool, wrapped, args, kwargs)
            _set_output_safely(span, result, ATTR_TOOL_RESULT)
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


_AGENT_WRAPPERS: Dict[str, Callable[[str, Callable], Callable]] = {
    AGENT_SYNC_METHOD: _trace_agent_call,
    AGENT_ASYNC_METHOD: _trace_agent_async_call,
    AGENT_SYNC_STREAM_METHOD: _trace_agent_stream,
    AGENT_ASYNC_STREAM_METHOD: _trace_agent_async_stream,
}
