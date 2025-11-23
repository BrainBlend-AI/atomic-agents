"""Chat agent configuration and initialization."""

import instructor
import openai
from atomic_agents import AgentConfig, AtomicAgent
from atomic_agents.context import SystemPromptGenerator

from fastapi_memory.lib.config import MODEL_NAME, NUM_SUGGESTED_QUESTIONS, get_api_key
from fastapi_memory.lib.schemas import ChatRequest, ChatResponse


def _create_system_prompt() -> SystemPromptGenerator:
    """Create the system prompt configuration for chat agents.

    Returns:
        SystemPromptGenerator configured for conversational assistance
    """
    return SystemPromptGenerator(
        background=["You are a helpful AI assistant that maintains conversation context."],
        steps=[
            "Understand the user's message",
            "Provide a clear and helpful response",
            f"Generate {NUM_SUGGESTED_QUESTIONS} example questions that the user could type to continue the conversation",
        ],
        output_instructions=[
            "Be concise and friendly",
            "Reference previous context when relevant",
            "Suggested questions must be phrased as if the user is asking them (e.g., 'Tell me more about X', 'How does Y work?', 'What is Z?')",
        ],
    )


def create_chat_agent() -> AtomicAgent[ChatRequest, ChatResponse]:
    """Create a new synchronous chat agent.

    Returns:
        AtomicAgent configured for synchronous chat operations

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = get_api_key()
    client = instructor.from_openai(openai.OpenAI(api_key=api_key))
    config = AgentConfig(
        client=client,
        model=MODEL_NAME,
        model_api_parameters={"reasoning_effort": "minimal"},
        system_prompt_generator=_create_system_prompt(),
    )
    return AtomicAgent[ChatRequest, ChatResponse](config=config)


def create_async_chat_agent() -> AtomicAgent[ChatRequest, ChatResponse]:
    """Create a new asynchronous chat agent.

    Returns:
        AtomicAgent configured for asynchronous streaming operations

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = get_api_key()
    client = instructor.from_openai(openai.AsyncOpenAI(api_key=api_key))
    config = AgentConfig(
        client=client,
        model=MODEL_NAME,
        model_api_parameters={"reasoning_effort": "minimal"},
        system_prompt_generator=_create_system_prompt(),
    )
    return AtomicAgent[ChatRequest, ChatResponse](config=config)
