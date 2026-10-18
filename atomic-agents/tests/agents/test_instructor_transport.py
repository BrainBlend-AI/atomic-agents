"""Drive a real Instructor client through a mocked HTTP transport.

The rest of the suite mocks the Instructor client itself, so it never sees how Instructor wraps the
response model or which keyword arguments it forwards into streaming. Both broke on Instructor 1.17
without any mocked test noticing.
"""

import json

import httpx
import instructor
import openai
import pytest

from atomic_agents import AgentConfig, AtomicAgent, BasicChatInputSchema, BasicChatOutputSchema

ASSISTANT_ARGUMENTS = json.dumps({"chat_message": "hi there"})


def tool_call_chunk(arguments_piece: str) -> str:
    delta = {
        "tool_calls": [
            {
                "index": 0,
                "id": "call-1",
                "type": "function",
                "function": {"name": "BasicChatOutputSchema", "arguments": arguments_piece},
            }
        ]
    }
    chunk = {"id": "chunk", "object": "chat.completion.chunk", "created": 0, "model": "m"}
    chunk["choices"] = [{"index": 0, "delta": delta, "finish_reason": None}]
    return "data: " + json.dumps(chunk) + "\n\n"


def respond_with_tool_call(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    if body.get("stream"):
        frames = tool_call_chunk(ASSISTANT_ARGUMENTS[:10]) + tool_call_chunk(ASSISTANT_ARGUMENTS[10:]) + "data: [DONE]\n\n"
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=frames.encode())
    message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {"name": "BasicChatOutputSchema", "arguments": ASSISTANT_ARGUMENTS},
            }
        ],
    }
    completion = {"id": "completion", "object": "chat.completion", "created": 0, "model": "m"}
    completion["choices"] = [{"index": 0, "message": message, "finish_reason": "tool_calls"}]
    completion["usage"] = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
    return httpx.Response(200, json=completion)


def agent_over_mock_transport(**model_api_parameters) -> AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema]:
    raw_client = openai.OpenAI(api_key="test", http_client=httpx.Client(transport=httpx.MockTransport(respond_with_tool_call)))
    config = AgentConfig(client=instructor.from_openai(raw_client), model="m", model_api_parameters=model_api_parameters)
    return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config=config)


def async_agent_over_mock_transport() -> AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema]:
    raw_client = openai.AsyncOpenAI(
        api_key="test", http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond_with_tool_call))
    )
    config = AgentConfig(client=instructor.from_openai(raw_client), model="m")
    return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config=config)


def test_run_parses_the_tool_call_through_instructor():
    response = agent_over_mock_transport().run(BasicChatInputSchema(chat_message="hey"))

    assert response.chat_message == "hi there"


@pytest.mark.asyncio
async def test_run_async_parses_the_tool_call_through_instructor():
    response = await async_agent_over_mock_transport().run_async(BasicChatInputSchema(chat_message="hey"))

    assert response.chat_message == "hi there"


def test_run_stream_yields_partials_then_the_complete_response():
    partials = list(agent_over_mock_transport().run_stream(BasicChatInputSchema(chat_message="hey")))

    assert partials[-1].chat_message == "hi there"


def test_run_stream_honors_a_caller_strict_setting():
    partials = list(agent_over_mock_transport(strict=True).run_stream(BasicChatInputSchema(chat_message="hey")))

    assert partials[-1].chat_message == "hi there"
