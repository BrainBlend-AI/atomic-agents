import abc
import asyncio
import contextvars
import gc
import json
import logging
import types
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import entry_points
from typing import Dict, List
from unittest.mock import Mock

import instructor
import pytest
from openinference.instrumentation import OITracer, TraceConfig, using_metadata, using_session
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema, BaseTool
from atomic_agents.context import BaseDynamicContextProvider, SystemPromptGenerator
from atomic_agents.observability import AtomicAgentsInstrumentor
import atomic_agents.observability as observability
from atomic_agents.observability import tracing as tracing


class QuestionSchema(BaseIOSchema):
    """A question for the agent."""

    question: str = Field(...)


class AnswerSchema(BaseIOSchema):
    """An answer from the agent."""

    answer: str = Field(...)


class CalculationInputSchema(BaseIOSchema):
    """Expression to evaluate."""

    expression: str = Field(...)


class CalculationOutputSchema(BaseIOSchema):
    """Result of the evaluation."""

    result: str = Field(...)


class CalculatorTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
    def run(self, params: CalculationInputSchema, precision: int = 2) -> CalculationOutputSchema:
        return CalculationOutputSchema(result=f"{len(params.expression):.{precision}f}")


class AsyncCalculatorTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
    def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
        return asyncio.run(self.arun(params))

    async def arun(self, params: CalculationInputSchema) -> CalculationOutputSchema:
        return CalculationOutputSchema(result=str(len(params.expression)))


class ThreadedCalculatorTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
    def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
        return CalculationOutputSchema(result=str(len(params.expression)))

    async def run_async(self, params: CalculationInputSchema) -> CalculationOutputSchema:
        return await asyncio.to_thread(self.run, params)


class RunMixin:
    def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
        return CalculationOutputSchema(result="mixin")


class MixinCalculatorTool(RunMixin, BaseTool[CalculationInputSchema, CalculationOutputSchema]):
    pass


class StaticRunTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
    @staticmethod
    def run(params: CalculationInputSchema) -> CalculationOutputSchema:
        return CalculationOutputSchema(result="static")


class FailingTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
    def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
        raise ValueError("boom")


class AnswerStore:
    """Container object pydantic cannot serialize to JSON."""

    def __init__(self):
        self.values: List[int] = []


class UnserializableInputSchema(BaseIOSchema):
    """Input carrying an arbitrary object."""

    model_config = {"arbitrary_types_allowed": True}
    store: AnswerStore = Field(...)


class EchoTool(BaseTool[UnserializableInputSchema, CalculationOutputSchema]):
    def run(self, params: UnserializableInputSchema) -> CalculationOutputSchema:
        return CalculationOutputSchema(result="echo")


@pytest.fixture
def exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    exporter.provider = provider
    instrumentor = AtomicAgentsInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    yield exporter
    instrumentor.uninstrument()


@pytest.fixture
def provider_tracer(exporter):
    return exporter.provider.get_tracer("test")


def sync_client(response=None, partials=None):
    client = Mock(spec=instructor.Instructor)
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = Mock(return_value=response or AnswerSchema(answer="42"))

    def create_partial(**kwargs):
        for partial in partials or [AnswerSchema(answer="4"), AnswerSchema(answer="42")]:
            yield partial

    client.chat.completions.create_partial = create_partial
    return client


def async_client(response=None, partials=None):
    client = Mock(spec=instructor.AsyncInstructor)
    client.chat = Mock()
    client.chat.completions = Mock()

    async def create(**kwargs):
        return response or AnswerSchema(answer="42")

    async def create_partial(**kwargs):
        for partial in partials or [AnswerSchema(answer="4"), AnswerSchema(answer="42")]:
            yield partial

    client.chat.completions.create = create
    client.chat.completions.create_partial = create_partial
    return client


def make_agent(client) -> AtomicAgent[QuestionSchema, AnswerSchema]:
    return AtomicAgent[QuestionSchema, AnswerSchema](AgentConfig(client=client, model="test-model"))


def spans_of(exporter) -> List[ReadableSpan]:
    return list(exporter.get_finished_spans())


def kind_of(span: ReadableSpan) -> str:
    return span.attributes[SpanAttributes.OPENINFERENCE_SPAN_KIND]


def input_json(span: ReadableSpan) -> Dict:
    return json.loads(span.attributes[SpanAttributes.INPUT_VALUE])


def output_json(span: ReadableSpan) -> Dict:
    return json.loads(span.attributes[SpanAttributes.OUTPUT_VALUE])


def test_run_emits_agent_span_with_io_and_framework_attributes(exporter):
    agent = make_agent(sync_client())

    response = agent.run(QuestionSchema(question="6*7?"))

    assert response.answer == "42"
    (span,) = spans_of(exporter)
    assert span.name == "invoke_agent AtomicAgent"
    assert kind_of(span) == OpenInferenceSpanKindValues.AGENT.value
    assert span.attributes[SpanAttributes.AGENT_NAME] == "AtomicAgent[QuestionSchema, AnswerSchema]"
    assert input_json(span) == {"question": "6*7?"}
    assert output_json(span) == {"answer": "42"}
    assert span.attributes[SpanAttributes.INPUT_MIME_TYPE] == "application/json"
    assert span.attributes[SpanAttributes.OUTPUT_MIME_TYPE] == "application/json"
    assert span.attributes[tracing.ATTR_MODEL] == "test-model"
    assert span.attributes[tracing.ATTR_MODE] == agent.mode.value
    assert span.attributes[tracing.ATTR_INPUT_SCHEMA] == "QuestionSchema"
    assert span.attributes[tracing.ATTR_OUTPUT_SCHEMA] == "AnswerSchema"
    assert span.attributes[tracing.ATTR_HISTORY_MESSAGE_COUNT] == 0
    assert span.attributes[tracing.ATTR_CONTEXT_PROVIDERS] == ()
    assert len(span.attributes[tracing.ATTR_SYSTEM_PROMPT_SHA256]) == 64
    assert span.status.status_code == StatusCode.OK


def test_second_turn_reports_history_size_entering_the_turn(exporter):
    agent = make_agent(sync_client())
    agent.run(QuestionSchema(question="first"))

    agent.run(QuestionSchema(question="second"))

    first, second = spans_of(exporter)
    assert first.attributes[tracing.ATTR_HISTORY_MESSAGE_COUNT] == 0
    assert second.attributes[tracing.ATTR_HISTORY_MESSAGE_COUNT] == 2


def test_agent_without_system_role_has_no_prompt_hash(exporter):
    agent = AtomicAgent[QuestionSchema, AnswerSchema](AgentConfig(client=sync_client(), model="m", system_role=None))

    agent.run(QuestionSchema(question="?"))

    (span,) = spans_of(exporter)
    assert tracing.ATTR_SYSTEM_PROMPT_SHA256 not in span.attributes


def test_abstract_intermediate_tool_base_is_not_wrapped(exporter):
    class AbstractCalculator(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        @abc.abstractmethod
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            raise NotImplementedError

    assert not hasattr(AbstractCalculator.__dict__["run"], tracing.TRACED_MARKER)


def test_run_without_input_sets_no_input_attribute(exporter):
    agent = make_agent(sync_client())

    agent.run()

    (span,) = spans_of(exporter)
    assert SpanAttributes.INPUT_VALUE not in span.attributes
    assert output_json(span) == {"answer": "42"}


def test_run_failure_propagates_and_marks_span_error(exporter):
    client = sync_client()
    client.chat.completions.create = Mock(side_effect=RuntimeError("provider down"))
    agent = make_agent(client)

    with pytest.raises(RuntimeError, match="provider down"):
        agent.run(QuestionSchema(question="?"))

    (span,) = spans_of(exporter)
    assert span.status.status_code == StatusCode.ERROR
    assert [event.name for event in span.events] == ["exception"]


def test_subclassed_agent_is_named_after_the_subclass_and_emits_one_span(exporter):
    class ResearchAgent(AtomicAgent[QuestionSchema, AnswerSchema]):
        def run(self, user_input=None):
            return super().run(user_input)

    agent = ResearchAgent(AgentConfig(client=sync_client(), model="test-model"))

    agent.run(QuestionSchema(question="?"))

    (span,) = spans_of(exporter)
    assert span.name == "invoke_agent ResearchAgent"


def test_agent_span_nests_under_a_user_chain_span(exporter, provider_tracer):
    agent = make_agent(sync_client())

    with provider_tracer.start_as_current_span("turn") as turn:
        agent.run(QuestionSchema(question="?"))

    agent_span, turn_span = spans_of(exporter)
    assert agent_span.parent.span_id == turn.get_span_context().span_id
    assert turn_span.name == "turn"


def test_manual_setup_from_the_guide_groups_agents_and_tools_under_one_chain_span():
    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace_config = TraceConfig()
    instrumentor = AtomicAgentsInstrumentor()
    instrumentor.instrument(tracer_provider=tracer_provider, config=trace_config)
    tracer = OITracer(tracer_provider.get_tracer(__name__), config=trace_config)
    planner = make_agent(sync_client())
    answerer = make_agent(sync_client())
    calculator = CalculatorTool()
    try:
        with tracer.start_as_current_span("answer_question", openinference_span_kind="chain") as turn:
            turn.set_input("what is 2 + 2?")
            plan = planner.run(QuestionSchema(question="what is 2 + 2?"))
            calculation = calculator.run(CalculationInputSchema(expression=plan.answer))
            answer = answerer.run(QuestionSchema(question=str(calculation.result)))
            turn.set_output(answer.answer)
    finally:
        instrumentor.uninstrument()

    spans = spans_of(exporter)
    chain_span = next(span for span in spans if kind_of(span) == OpenInferenceSpanKindValues.CHAIN.value)
    children = [span for span in spans if span is not chain_span]
    assert [kind_of(span) for span in children] == ["AGENT", "TOOL", "AGENT"]
    assert all(span.parent.span_id == chain_span.get_span_context().span_id for span in children)
    assert chain_span.attributes[SpanAttributes.INPUT_VALUE] == "what is 2 + 2?"
    assert chain_span.attributes[SpanAttributes.OUTPUT_VALUE] == answer.answer


def test_llm_call_inside_run_becomes_child_of_agent_span(exporter, provider_tracer):
    def create(**kwargs):
        with provider_tracer.start_as_current_span("llm"):
            return AnswerSchema(answer="42")

    client = sync_client()
    client.chat.completions.create = create
    agent = make_agent(client)

    agent.run(QuestionSchema(question="?"))

    llm_span, agent_span = spans_of(exporter)
    assert llm_span.parent.span_id == agent_span.context.span_id


def test_run_stream_records_final_output_and_keeps_child_context_per_step(exporter, provider_tracer):
    current_between_yields = []

    def create_partial(**kwargs):
        yield AnswerSchema(answer="4")
        with provider_tracer.start_as_current_span("llm-chunk"):
            yield AnswerSchema(answer="42")

    client = sync_client()
    client.chat.completions.create_partial = create_partial
    agent = make_agent(client)

    partials = []
    for partial in agent.run_stream(QuestionSchema(question="?")):
        partials.append(partial.answer)
        current_between_yields.append(trace_api.get_current_span())

    assert partials == ["4", "42"]
    assert all(span is trace_api.INVALID_SPAN for span in current_between_yields)
    chunk_span, agent_span = spans_of(exporter)
    assert agent_span.name == "invoke_agent AtomicAgent"
    assert chunk_span.parent.span_id == agent_span.context.span_id
    assert output_json(agent_span) == {"answer": "42"}
    assert agent_span.status.status_code == StatusCode.OK


def test_run_stream_preserves_the_generator_return_value(exporter):
    agent = make_agent(sync_client())

    def consume():
        final = yield from agent.run_stream(QuestionSchema(question="?"))
        return final

    generator = consume()
    with pytest.raises(StopIteration) as stop:
        while True:
            next(generator)

    assert stop.value.value.answer == "42"


def test_run_stream_with_no_partials_ends_ok_without_output(exporter):
    client = sync_client()
    client.chat.completions.create_partial = lambda **kwargs: iter([])
    agent = make_agent(client)

    assert list(agent.run_stream(QuestionSchema(question="?"))) == []

    (span,) = spans_of(exporter)
    assert span.status.status_code == StatusCode.OK
    assert SpanAttributes.OUTPUT_VALUE not in span.attributes


def test_run_stream_closed_early_ends_span_and_closes_inner_generator(exporter):
    inner_closed = []

    def create_partial(**kwargs):
        try:
            yield AnswerSchema(answer="4")
            yield AnswerSchema(answer="42")
        finally:
            inner_closed.append(True)

    client = sync_client()
    client.chat.completions.create_partial = create_partial
    agent = make_agent(client)

    for partial in agent.run_stream(QuestionSchema(question="?")):
        break

    assert inner_closed == [True]
    (span,) = spans_of(exporter)
    assert span.attributes[tracing.ATTR_STREAM_CLOSED_EARLY] is True
    assert output_json(span) == {"answer": "4"}
    assert span.status.status_code == StatusCode.OK


def test_run_stream_failure_mid_stream_marks_error(exporter):
    def create_partial(**kwargs):
        yield AnswerSchema(answer="4")
        raise RuntimeError("stream broke")

    client = sync_client()
    client.chat.completions.create_partial = create_partial
    agent = make_agent(client)

    with pytest.raises(RuntimeError, match="stream broke"):
        list(agent.run_stream(QuestionSchema(question="?")))

    (span,) = spans_of(exporter)
    assert span.status.status_code == StatusCode.ERROR


@pytest.mark.asyncio
async def test_run_async_emits_agent_span(exporter):
    agent = make_agent(async_client())

    response = await agent.run_async(QuestionSchema(question="?"))

    assert response.answer == "42"
    (span,) = spans_of(exporter)
    assert span.name == "invoke_agent AtomicAgent"
    assert output_json(span) == {"answer": "42"}
    assert span.status.status_code == StatusCode.OK


@pytest.mark.asyncio
async def test_run_async_stream_records_last_partial_and_nests_children(exporter, provider_tracer):
    async def create_partial(**kwargs):
        yield AnswerSchema(answer="4")
        with provider_tracer.start_as_current_span("llm-chunk"):
            yield AnswerSchema(answer="42")

    client = async_client()
    client.chat.completions.create_partial = create_partial
    agent = make_agent(client)

    partials = [partial.answer async for partial in agent.run_async_stream(QuestionSchema(question="?"))]

    assert partials == ["4", "42"]
    chunk_span, agent_span = spans_of(exporter)
    assert agent_span.name == "invoke_agent AtomicAgent"
    assert chunk_span.parent.span_id == agent_span.context.span_id
    assert output_json(agent_span) == {"answer": "42"}


@pytest.mark.asyncio
async def test_run_async_stream_closed_early_ends_span(exporter):
    agent = make_agent(async_client())

    stream = agent.run_async_stream(QuestionSchema(question="?"))
    first = await stream.__anext__()
    await stream.aclose()

    assert first.answer == "4"
    (span,) = spans_of(exporter)
    assert span.attributes[tracing.ATTR_STREAM_CLOSED_EARLY] is True
    assert span.status.status_code == StatusCode.OK


@pytest.mark.asyncio
async def test_concurrent_async_runs_keep_separate_spans(exporter):
    first = make_agent(async_client(response=AnswerSchema(answer="one")))
    second = make_agent(async_client(response=AnswerSchema(answer="two")))

    await asyncio.gather(first.run_async(QuestionSchema(question="1")), second.run_async(QuestionSchema(question="2")))

    outputs = {input_json(span)["question"]: output_json(span)["answer"] for span in spans_of(exporter)}
    assert outputs == {"1": "one", "2": "two"}
    assert all(span.parent is None for span in spans_of(exporter))


def test_tool_defined_before_instrumentation_emits_tool_span(exporter):
    tool = CalculatorTool()

    result = tool.run(CalculationInputSchema(expression="6*7"), precision=1)

    assert result.result == "3.0"
    (span,) = spans_of(exporter)
    assert span.name == "execute_tool CalculatorTool"
    assert kind_of(span) == OpenInferenceSpanKindValues.TOOL.value
    assert span.attributes[SpanAttributes.TOOL_NAME] == "CalculationInputSchema"
    assert span.attributes[SpanAttributes.TOOL_DESCRIPTION] == "Expression to evaluate."
    assert json.loads(span.attributes[SpanAttributes.TOOL_PARAMETERS])["title"] == "CalculationInputSchema"
    assert input_json(span) == {"expression": "6*7"}
    assert output_json(span) == {"result": "3.0"}
    assert span.status.status_code == StatusCode.OK


def test_tool_accepts_keyword_params(exporter):
    result = CalculatorTool().run(params=CalculationInputSchema(expression="1+1"))

    assert result.result == "3.00"
    (span,) = spans_of(exporter)
    assert input_json(span) == {"expression": "1+1"}


def test_tool_defined_after_instrumentation_emits_tool_span(exporter):
    class LateTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result="late")

    LateTool().run(CalculationInputSchema(expression="x"))

    (span,) = spans_of(exporter)
    assert span.name == "execute_tool LateTool"
    assert LateTool().input_schema is CalculationInputSchema


def test_subclass_calling_super_run_emits_one_span(exporter):
    class LoudCalculatorTool(CalculatorTool):
        def run(self, params: CalculationInputSchema, precision: int = 2) -> CalculationOutputSchema:
            return super().run(params, precision)

    LoudCalculatorTool().run(CalculationInputSchema(expression="2*2"))

    (span,) = spans_of(exporter)
    assert span.name == "execute_tool LoudCalculatorTool"


def test_sync_run_delegating_to_arun_emits_one_span(exporter):
    AsyncCalculatorTool().run(CalculationInputSchema(expression="2*2"))

    (span,) = spans_of(exporter)
    assert span.name == "execute_tool AsyncCalculatorTool"
    assert output_json(span) == {"result": "3"}


@pytest.mark.asyncio
async def test_run_async_delegating_to_thread_emits_one_span(exporter):
    await ThreadedCalculatorTool().run_async(CalculationInputSchema(expression="3*3"))

    (span,) = spans_of(exporter)
    assert span.name == "execute_tool ThreadedCalculatorTool"
    assert output_json(span) == {"result": "3"}


def test_mixin_defined_run_is_traced(exporter):
    MixinCalculatorTool().run(CalculationInputSchema(expression="x"))

    (span,) = spans_of(exporter)
    assert span.name == "execute_tool MixinCalculatorTool"


def test_static_run_is_left_alone(exporter):
    assert StaticRunTool.run(CalculationInputSchema(expression="x")).result == "static"
    assert spans_of(exporter) == []


def test_tool_failure_propagates_same_exception_and_marks_error(exporter):
    with pytest.raises(ValueError, match="boom") as raised:
        FailingTool().run(CalculationInputSchema(expression="x"))

    (span,) = spans_of(exporter)
    assert span.status.status_code == StatusCode.ERROR
    assert raised.value.args == ("boom",)


def test_unserializable_input_still_returns_result(exporter, caplog):
    with caplog.at_level(logging.WARNING):
        result = EchoTool().run(UnserializableInputSchema(store=AnswerStore()))

    assert result.result == "echo"
    (span,) = spans_of(exporter)
    assert span.status.status_code == StatusCode.OK


def test_agent_run_inside_tool_nests_under_tool_span(exporter):
    agent = make_agent(sync_client())

    class AgentTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result=agent.run(QuestionSchema(question=params.expression)).answer)

    AgentTool().run(CalculationInputSchema(expression="?"))

    agent_span, tool_span = spans_of(exporter)
    assert agent_span.parent.span_id == tool_span.context.span_id


def test_hide_inputs_and_outputs_redacts_values_and_drops_mime_types():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = AtomicAgentsInstrumentor()
    instrumentor.instrument(tracer_provider=provider, config=TraceConfig(hide_inputs=True, hide_outputs=True))
    try:
        make_agent(sync_client()).run(QuestionSchema(question="secret"))
        CalculatorTool().run(CalculationInputSchema(expression="1+1"))
    finally:
        instrumentor.uninstrument()

    for span in spans_of(exporter):
        assert span.attributes[SpanAttributes.INPUT_VALUE] == "__REDACTED__"
        assert span.attributes[SpanAttributes.OUTPUT_VALUE] == "__REDACTED__"
        assert SpanAttributes.INPUT_MIME_TYPE not in span.attributes
        assert SpanAttributes.OUTPUT_MIME_TYPE not in span.attributes


def test_session_and_user_metadata_survive_on_agent_span(exporter):
    agent = make_agent(sync_client())

    with using_session("session-1"), using_metadata({"tenant": "acme"}):
        agent.run(QuestionSchema(question="?"))

    (span,) = spans_of(exporter)
    assert span.attributes[SpanAttributes.SESSION_ID] == "session-1"
    assert json.loads(span.attributes[SpanAttributes.METADATA]) == {"tenant": "acme"}


def test_second_instrument_with_other_settings_warns_and_keeps_first(exporter, caplog):
    other_provider = TracerProvider()

    with caplog.at_level(logging.WARNING):
        AtomicAgentsInstrumentor().instrument(tracer_provider=other_provider)

    assert "already installed" in caplog.text
    make_agent(sync_client()).run(QuestionSchema(question="?"))
    assert len(spans_of(exporter)) == 1


def test_uninstrument_restores_originals_and_stops_tracing():
    original_run = AtomicAgent.__dict__["run"]
    original_tool_run = CalculatorTool.__dict__["run"]
    original_init_subclass = BaseTool.__dict__["__init_subclass__"]
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = AtomicAgentsInstrumentor()

    instrumentor.instrument(tracer_provider=provider)
    assert instrumentor.is_instrumented_by_opentelemetry
    instrumentor.uninstrument()
    instrumentor.uninstrument()

    assert not instrumentor.is_instrumented_by_opentelemetry
    assert AtomicAgent.__dict__["run"] is original_run
    assert CalculatorTool.__dict__["run"] is original_tool_run
    assert BaseTool.__dict__["__init_subclass__"] is original_init_subclass
    assert "run" not in MixinCalculatorTool.__dict__

    class AfterwardsTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result="plain")

    assert AfterwardsTool().input_schema is CalculationInputSchema
    make_agent(sync_client()).run(QuestionSchema(question="?"))
    AfterwardsTool().run(CalculationInputSchema(expression="x"))
    assert spans_of(exporter) == []


def test_phoenix_entry_point_loads_and_instruments_with_only_a_tracer_provider():
    (entry_point,) = [point for point in entry_points(group="openinference_instrumentor") if point.name == "atomic_agents"]
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    instrumentor = entry_point.load()()
    instrumentor.instrument(tracer_provider=provider)
    try:
        make_agent(sync_client()).run(QuestionSchema(question="?"))
    finally:
        instrumentor.uninstrument()

    assert isinstance(instrumentor, AtomicAgentsInstrumentor)
    assert len(spans_of(exporter)) == 1


@pytest.mark.parametrize("options", [{}, {"skip_dep_check": False}])
def test_instrument_without_opentelemetry_raises_install_hint(monkeypatch: pytest.MonkeyPatch, options: dict[str, object]):
    monkeypatch.setattr(observability, "_opentelemetry_is_installed", lambda: False)

    with pytest.raises(ImportError, match="atomic-agents\\[observability\\]"):
        AtomicAgentsInstrumentor().instrument(**options)


def test_uninstrument_without_opentelemetry_is_a_no_op(monkeypatch):
    monkeypatch.setattr(observability, "_opentelemetry_is_installed", lambda: False)

    AtomicAgentsInstrumentor().uninstrument()

    assert not AtomicAgentsInstrumentor().is_instrumented_by_opentelemetry


def test_openinference_below_the_floor_only_disables_context_with_a_warning(monkeypatch, caplog):
    monkeypatch.setattr(observability, "version", lambda distribution: "0.1.20")

    with caplog.at_level(logging.WARNING):
        AtomicAgentsInstrumentor().instrument()

    assert "0.1.38 or newer is required" in caplog.text
    assert AtomicAgentsInstrumentor().is_instrumented_by_opentelemetry
    assert tracing._context_attributes() == {}
    AtomicAgentsInstrumentor().uninstrument()


class CountingProvider(BaseDynamicContextProvider):
    def __init__(self):
        super().__init__(title="Counter")
        self.calls = 0

    def get_info(self) -> str:
        self.calls += 1
        return f"call {self.calls}"


def test_prompt_hash_identifies_static_sections_despite_dynamic_providers(exporter):
    generator = SystemPromptGenerator(background=["v1"], context_providers={"counter": CountingProvider()})
    agent = AtomicAgent[QuestionSchema, AnswerSchema](
        AgentConfig(client=sync_client(), model="m", system_prompt_generator=generator)
    )

    agent.run(QuestionSchema(question="a"))
    agent.run(QuestionSchema(question="b"))

    first, second = spans_of(exporter)
    assert first.attributes[tracing.ATTR_SYSTEM_PROMPT_SHA256] == second.attributes[tracing.ATTR_SYSTEM_PROMPT_SHA256]
    assert first.attributes[tracing.ATTR_CONTEXT_PROVIDERS] == ("counter",)


def test_prompt_hash_changes_when_static_sections_change(exporter):
    agent = make_agent(sync_client())
    agent.run(QuestionSchema(question="a"))
    agent.system_prompt_generator.background = ["v2"]

    agent.run(QuestionSchema(question="b"))

    first, second = spans_of(exporter)
    assert first.attributes[tracing.ATTR_SYSTEM_PROMPT_SHA256] != second.attributes[tracing.ATTR_SYSTEM_PROMPT_SHA256]


def test_run_stream_dropped_without_close_still_ends_span(exporter):
    agent = make_agent(sync_client())
    stream = agent.run_stream(QuestionSchema(question="?"))
    next(stream)

    del stream
    gc.collect()

    (span,) = spans_of(exporter)
    assert span.attributes[tracing.ATTR_STREAM_CLOSED_EARLY] is True


@pytest.mark.asyncio
async def test_run_async_stream_cancelled_mid_await_is_not_an_error(exporter):
    release = asyncio.Event()

    async def create_partial(**kwargs):
        yield AnswerSchema(answer="4")
        await release.wait()
        yield AnswerSchema(answer="42")

    client = async_client()
    client.chat.completions.create_partial = create_partial
    agent = make_agent(client)

    async def consume():
        async for _ in agent.run_async_stream(QuestionSchema(question="?")):
            pass

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    (span,) = spans_of(exporter)
    assert span.attributes[tracing.ATTR_STREAM_CLOSED_EARLY] is True
    assert output_json(span) == {"answer": "4"}
    assert span.status.status_code != StatusCode.ERROR


def test_forge_style_thread_pool_tool_emits_one_span_in_the_callers_trace(exporter, provider_tracer):
    class ForgeStyleTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            with ThreadPoolExecutor() as executor:
                return executor.submit(contextvars.copy_context().run, asyncio.run, self.run_async(params)).result()

        async def run_async(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result="pooled")

    with provider_tracer.start_as_current_span("root") as root:
        ForgeStyleTool().run(CalculationInputSchema(expression="x"))

    tool_span, root_span = spans_of(exporter)
    assert tool_span.name == "execute_tool ForgeStyleTool"
    assert tool_span.parent.span_id == root.get_span_context().span_id
    assert tool_span.context.trace_id == root_span.context.trace_id


def test_mcp_style_generated_tool_class_emits_one_span(exporter):
    async def arun(self, params):
        return CalculationOutputSchema(result="mcp")

    def run(self, params):
        return asyncio.run(self.arun(params))

    GeneratedTool = types.new_class(
        "GeneratedTool",
        (BaseTool[CalculationInputSchema, CalculationOutputSchema],),
        {},
        lambda namespace: namespace.update({"run": run, "arun": arun}),
    )

    GeneratedTool().run(CalculationInputSchema(expression="x"))

    (span,) = spans_of(exporter)
    assert span.name == "execute_tool GeneratedTool"
    assert output_json(span) == {"result": "mcp"}


def test_async_generator_tool_method_is_left_alone(exporter):
    class StreamingTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result="x")

        async def run_async(self, params: CalculationInputSchema):
            yield CalculationOutputSchema(result="chunk")

    assert not hasattr(StreamingTool.__dict__["run_async"], tracing.TRACED_MARKER)
    assert hasattr(StreamingTool.__dict__["run"], tracing.TRACED_MARKER)


def test_instrument_uninstrument_instrument_cycle_traces_tools_defined_between_cycles():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = AtomicAgentsInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    instrumentor.uninstrument()

    class BetweenCyclesTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result="between")

    original_run = BetweenCyclesTool.__dict__["run"]
    instrumentor.instrument(tracer_provider=provider)
    try:
        BetweenCyclesTool().run(CalculationInputSchema(expression="x"))
    finally:
        instrumentor.uninstrument()

    assert [span.name for span in spans_of(exporter)] == ["execute_tool BetweenCyclesTool"]
    assert BetweenCyclesTool.__dict__["run"] is original_run


@pytest.fixture
def configured_tracing():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    yield provider, exporter
    AtomicAgentsInstrumentor().uninstrument()
    provider.shutdown()


@pytest.mark.parametrize("openinference_enabled", [False, True])
def test_genai_attributes_survive_without_openinference(monkeypatch, configured_tracing, openinference_enabled):
    provider, exporter = configured_tracing
    monkeypatch.setattr(tracing, "_import_context_attributes", lambda: None)
    config = tracing.TracingConfig(openinference_attributes=True if openinference_enabled else None)
    AtomicAgentsInstrumentor().instrument(tracer_provider=provider, config=config)
    client = sync_client()
    client.provider = types.SimpleNamespace(value="openai")
    make_agent(client).run(QuestionSchema(question="question"))
    CalculatorTool().run(CalculationInputSchema(expression="1+1"))

    agent_span, tool_span = spans_of(exporter)
    assert [agent_span.name, tool_span.name] == ["invoke_agent AtomicAgent", "execute_tool CalculatorTool"]
    assert agent_span.attributes["gen_ai.operation.name"] == "invoke_agent"
    assert agent_span.attributes["gen_ai.agent.name"] == "AtomicAgent"
    assert agent_span.attributes["gen_ai.request.model"] == "test-model"
    assert agent_span.attributes["gen_ai.provider.name"] == "openai"
    assert agent_span.attributes["atomic_agents.agent.class"] == "AtomicAgent[QuestionSchema, AnswerSchema]"
    assert json.loads(agent_span.attributes["atomic_agents.input"]) == {"question": "question"}
    assert json.loads(agent_span.attributes["atomic_agents.output"]) == {"answer": "42"}
    assert tool_span.attributes["gen_ai.operation.name"] == "execute_tool"
    assert tool_span.attributes["gen_ai.tool.name"] == "CalculatorTool"
    assert tool_span.attributes["gen_ai.tool.description"] == "Expression to evaluate."
    assert tool_span.attributes["gen_ai.tool.type"] == "function"
    assert json.loads(tool_span.attributes["gen_ai.tool.call.arguments"]) == {"expression": "1+1"}
    assert json.loads(tool_span.attributes["gen_ai.tool.call.result"]) == {"result": "3.00"}
    assert ("openinference.span.kind" in agent_span.attributes) is openinference_enabled
    assert ("openinference.span.kind" in tool_span.attributes) is openinference_enabled
    if openinference_enabled:
        assert agent_span.attributes["input.value"] == agent_span.attributes["atomic_agents.input"]
        assert tool_span.attributes["input.value"] == tool_span.attributes["gen_ai.tool.call.arguments"]
        assert tool_span.attributes["output.value"] == tool_span.attributes["gen_ai.tool.call.result"]
    else:
        assert not ({"input.value", "output.value", "agent.name"} & agent_span.attributes.keys())
        assert not ({"input.value", "output.value", "tool.name", "tool.parameters"} & tool_span.attributes.keys())


@pytest.mark.parametrize("config_class", [tracing.TracingConfig, TraceConfig])
def test_both_visibility_configs_redact_primary_payloads(configured_tracing, config_class):
    provider, exporter = configured_tracing
    AtomicAgentsInstrumentor().instrument(tracer_provider=provider, config=config_class(hide_inputs=True, hide_outputs=True))
    make_agent(sync_client()).run(QuestionSchema(question="secret"))
    CalculatorTool().run(CalculationInputSchema(expression="secret"))

    agent_span, tool_span = spans_of(exporter)
    assert agent_span.attributes["atomic_agents.input"] == "__REDACTED__"
    assert agent_span.attributes["atomic_agents.output"] == "__REDACTED__"
    assert tool_span.attributes["gen_ai.tool.call.arguments"] == "__REDACTED__"
    assert tool_span.attributes["gen_ai.tool.call.result"] == "__REDACTED__"


@pytest.mark.parametrize("hide_outputs", [False, True])
def test_large_tool_result_is_truncated_unless_hidden(configured_tracing, hide_outputs):
    provider, exporter = configured_tracing
    AtomicAgentsInstrumentor().instrument(
        tracer_provider=provider, config=tracing.TracingConfig(hide_outputs=hide_outputs, openinference_attributes=True)
    )

    class LargeResultTool(BaseTool[CalculationInputSchema, CalculationOutputSchema]):
        def run(self, params: CalculationInputSchema) -> CalculationOutputSchema:
            return CalculationOutputSchema(result="x" * 10240)

    result = LargeResultTool().run(CalculationInputSchema(expression="large"))
    (span,) = spans_of(exporter)
    serialized = result.model_dump_json()
    expected = "__REDACTED__" if hide_outputs else serialized[:4096] + "...[truncated]"
    assert span.attributes["gen_ai.tool.call.result"] == expected
    assert span.attributes["output.value"] == expected
    if hide_outputs:
        assert "gen_ai.tool.call.result.original_length" not in span.attributes
        assert "output.value.original_length" not in span.attributes
    else:
        assert span.attributes["gen_ai.tool.call.result.original_length"] == len(serialized)
        assert span.attributes["output.value.original_length"] == len(serialized)


@pytest.mark.parametrize("agent_method", ["run", "run_async", "run_stream", "run_async_stream"])
@pytest.mark.asyncio
async def test_suppression_skips_agent_and_tool_spans(exporter, agent_method):
    from opentelemetry import context

    client = async_client() if "async" in agent_method else sync_client()
    agent = make_agent(client)
    token = context.attach(context.set_value("suppress_instrumentation", True))
    try:
        result = getattr(agent, agent_method)(QuestionSchema(question="suppressed"))
        assert await final_agent_answer(agent_method, result) == "42"
        assert CalculatorTool().run(CalculationInputSchema(expression="1+1")).result == "3.00"
        assert (await ThreadedCalculatorTool().run_async(CalculationInputSchema(expression="1+1"))).result == "3"
    finally:
        context.detach(token)
    assert spans_of(exporter) == []


def test_failures_record_qualified_error_type(exporter):
    client = sync_client()
    client.chat.completions.create.side_effect = ValueError("agent failure")
    with pytest.raises(ValueError, match="agent failure"):
        make_agent(client).run(QuestionSchema(question="fail"))
    with pytest.raises(ValueError, match="boom"):
        FailingTool().run(CalculationInputSchema(expression="fail"))
    for span in spans_of(exporter):
        assert span.attributes["error.type"] == "ValueError"
        assert span.status.status_code == StatusCode.ERROR
        assert len(span.events) == 1


def test_tracing_config_environment_and_coercion(monkeypatch):
    monkeypatch.setenv("OPENINFERENCE_HIDE_INPUTS", "TrUe")
    monkeypatch.setenv("OPENINFERENCE_HIDE_OUTPUTS", "1")
    monkeypatch.setenv("ATOMIC_AGENTS_TRACE_MAX_ATTRIBUTE_LENGTH", "128")
    from atomic_agents.observability import TracingConfig

    config = TracingConfig.from_environment()
    assert config == TracingConfig(hide_inputs=True, hide_outputs=True, max_attribute_length=128)
    assert TracingConfig.coerce(None) == config
    assert TracingConfig.coerce(config) is config
    assert TracingConfig.coerce(TraceConfig(hide_inputs=True)) == TracingConfig(hide_inputs=True)


def test_session_is_mirrored_to_genai_conversation(exporter):
    with using_session("session-1"):
        make_agent(sync_client()).run(QuestionSchema(question="?"))
        CalculatorTool().run(CalculationInputSchema(expression="?"))
    for span in spans_of(exporter):
        assert span.attributes["gen_ai.conversation.id"] == "session-1"


async def final_agent_answer(agent_method, result):
    if agent_method == "run_async":
        return (await result).answer
    elif agent_method == "run_stream":
        return list(result)[-1].answer
    elif agent_method == "run_async_stream":
        return [partial async for partial in result][-1].answer
    else:
        return result.answer
