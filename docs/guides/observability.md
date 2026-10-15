# Observability with Arize Phoenix and OpenTelemetry

Atomic Agents ships an optional [OpenInference](https://github.com/Arize-ai/openinference) instrumentor. Once it
is installed, every `AtomicAgent` run and every `BaseTool` run becomes a span that
[Arize Phoenix](https://github.com/Arize-ai/phoenix), Arize AX, Langfuse, or any other OpenTelemetry backend can
display. Nothing changes for applications that do not opt in.

## What you get

| Call | Span | Attributes |
|------|------|------------|
| `agent.run`, `run_async`, `run_stream`, `run_async_stream` | `AGENT`, named `AtomicAgent[InputSchema, OutputSchema].run` (a subclass reports its own name) | `agent.name`, `input.value` / `output.value` as JSON, `atomic_agents.model`, `atomic_agents.mode`, `atomic_agents.input_schema`, `atomic_agents.output_schema`, `atomic_agents.history.message_count` (history size entering the turn), `atomic_agents.context_providers`, `atomic_agents.system_prompt.sha256` (hash of the static prompt sections: background, steps, output instructions) |
| `tool.run`, `run_async`, `arun` on any `BaseTool` subclass, including MCP tools | `TOOL`, named after the tool class | `tool.name`, `tool.description`, `tool.parameters` (the input JSON schema), `input.value` / `output.value` as JSON |

Spans carry `session.id`, `user.id`, `metadata` and tags when you wrap calls in the OpenInference context
managers (`using_session`, `using_user`, `using_metadata`, `using_attributes`). Exceptions set the span status to
`ERROR` and are recorded as span events. Streaming spans record the final response when the stream completes,
or the last partial plus `atomic_agents.stream.closed_early = true` when the consumer stops early or the task
is cancelled (a cancelled stream is not reported as an error).

LLM spans are not produced by Atomic Agents. Install exactly one LLM instrumentor for the provider SDK you use
(`openinference-instrumentation-openai`, `-anthropic`, `-litellm`, ...). Installing both a provider instrumentor and
`openinference-instrumentation-instructor` gives you two layers of LLM spans. Because the agent span is the current
span while the provider call runs, the LLM span (with prompts, tokens and the model name) nests under it. Instructor
retries show up as several LLM spans under one agent span.

## Install

```bash
pip install "atomic-agents[observability]" arize-phoenix-otel openinference-instrumentation-openai
```

The `observability` extra installs `openinference-instrumentation`, `openinference-semantic-conventions` and
`opentelemetry-api`. The Phoenix path below works without the extra because `arize-phoenix-otel` already depends on
those packages; the manual path needs the extra plus an OpenTelemetry SDK and exporter:

```bash
pip install "atomic-agents[observability]" opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

## Setup with Phoenix (automatic)

```python
from phoenix.otel import register

tracer_provider = register(project_name="my-app", auto_instrument=True)
```

`register(auto_instrument=True)` discovers the Atomic Agents instrumentor through the `openinference_instrumentor`
entry point and activates it together with every other OpenInference instrumentor in the environment. Do this once,
at import time or in your service's startup hook, before any agent runs. Phoenix reads `PHOENIX_COLLECTOR_ENDPOINT`,
`PHOENIX_PROJECT` (alias `PHOENIX_PROJECT_NAME`) and `PHOENIX_API_KEY` from the environment. With no endpoint set,
`register()` exports over gRPC to `localhost:4317`; set `PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006` to send
HTTP to the port the Phoenix UI serves on.

Two things to know about the automatic path:

- Phoenix imports `atomic_agents` to load the entry point. That import is the same as any `import atomic_agents` in
  your application, including the Instructor streaming patch the framework applies at import.
- Existing `auto_instrument=True` users start exporting agent and tool payloads when they upgrade to a version with the
  instrumentor. Use the privacy controls below if that is not wanted.

## Setup with any OpenTelemetry backend (manual)

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation import TraceConfig
from openinference.instrumentation.openai import OpenAIInstrumentor

from atomic_agents.observability import AtomicAgentsInstrumentor

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter("http://localhost:6006/v1/traces")))

AtomicAgentsInstrumentor().instrument(tracer_provider=tracer_provider, config=TraceConfig())
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
```

`instrument()` is idempotent. Calling it again with a different provider or config logs a warning and keeps the first
installation; call `uninstrument()` first to change it. `uninstrument()` restores the original methods on
`AtomicAgent` and on every tool class.

## Grouping agent and tool calls into one trace

Atomic Agents has no tool-calling loop: your code calls `agent.run(...)`, then `tool.run(...)`, then another agent.
Each of those is a root span, so without a parent they become separate traces. Open one parent span per unit of work:

```python
tracer = tracer_provider.get_tracer(__name__)

with tracer.start_as_current_span("answer_question", openinference_span_kind="chain") as turn:
    turn.set_input(question)
    plan = planner.run(BasicChatInputSchema(chat_message=question))
    calculation = calculator.run(CalculatorToolInputSchema(expression=plan.expression))
    answer = answerer.run(CalculationResultSchema(question=question, expression=plan.expression, result=calculation.result))
    turn.set_output(answer.chat_message)
```

The [phoenix-tracing example](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/phoenix-tracing)
is exactly this flow.

## Sessions, users and metadata

```python
from openinference.instrumentation import using_session, using_user, using_metadata

with using_session(session_id=conversation_id), using_user(user_id=user.id), using_metadata({"tenant": tenant}):
    response = agent.run(user_message)
```

Phoenix groups spans that share a `session.id` into a conversation view. For a streaming endpoint, put the context
manager inside the generator that yields the chunks, not around the endpoint function; the generator runs after the
endpoint returned, so a context manager around the endpoint body no longer applies.

## Privacy

Agent and tool payloads are exported as `input.value` / `output.value`. To redact them:

- On the automatic Phoenix path, set `OPENINFERENCE_HIDE_INPUTS=true` and/or `OPENINFERENCE_HIDE_OUTPUTS=true`.
  `TraceConfig()` reads these variables.
- On the manual path, pass `TraceConfig(hide_inputs=True, hide_outputs=True)` to `instrument()`.

Redacted values are exported as `__REDACTED__`. `atomic_agents.system_prompt.sha256` stays available either way. It
hashes the static sections of a `SystemPromptGenerator` (background, steps, output instructions) and ignores what
context providers add per call, so it identifies the prompt version even when inputs are hidden. Multimodal inputs (images, audio, PDFs) are serialized into
`input.value` in full; cap attribute size with `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT` if that is too much.

## Services and async

- Call `register(...)` (or `instrument(...)`) at import or in the startup hook so every worker process is instrumented.
- Use `register(batch=True)` (or a `BatchSpanProcessor`) in services so span export does not block request handling.
- Concurrent `run_async` calls, including `asyncio.gather` over several agents, get independent spans.
- Streaming token counts need `model_api_parameters={"stream_options": {"include_usage": True}}` for OpenAI.

## Limitations

- Methods bound before instrumentation stay untraced: `callback = agent.run` taken before `instrument()` keeps
  calling the original.
- An `AtomicAgent` subclass that overrides `run` (or a stream method) without calling `super()` bypasses the wrapper
  and emits no span; add `@tracer.agent` to such overrides yourself.
- Tool methods that are async generators are left untraced.
- A plain `ThreadPoolExecutor` starts its worker with an empty context, so a tool that submits work to one loses the
  current span and the re-entrancy guard inside the pool. Submit through a copied context instead, as the forge tools
  do: `executor.submit(contextvars.copy_context().run, asyncio.run, self.run_async(params))`. `asyncio.to_thread` and
  `asyncio.run` already copy the context.
- The AGENT span records the final (or last partial) response of a stream, not every chunk.
- The system prompt text is not on the AGENT span; it is the first message on the LLM span. The AGENT span carries its
  SHA-256 instead.
