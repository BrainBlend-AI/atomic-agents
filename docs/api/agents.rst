Agents
======

Base Agent
----------

The BaseAgent class provides core functionality for building AI agents with structured input/output schemas,
memory management, and streaming capabilities.

Basic Usage
^^^^^^^^^^

.. code-block:: python

    import instructor
    from openai import OpenAI
    from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
    from atomic_agents.lib.components.agent_memory import AgentMemory

    # Initialize with OpenAI
    client = instructor.from_openai(OpenAI())

    # Create basic configuration
    config = BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=AgentMemory()
    )

    # Initialize agent
    agent = BaseAgent(config)

Class Documentation
^^^^^^^^^^^^^^^^^

.. py:class:: BaseAgent

    .. py:method:: __init__(config: BaseAgentConfig)

        Initializes a new BaseAgent instance.

        :param config: Configuration object containing client, model, memory, and other settings
        :type config: BaseAgentConfig

        Example:

        .. code-block:: python

            # Initialize with custom memory and system prompt
            from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

            agent = BaseAgent(
                BaseAgentConfig(
                    client=client,
                    model="gpt-4o-mini",
                    memory=AgentMemory(),
                    system_prompt_generator=SystemPromptGenerator(
                        background=["You are a helpful AI assistant"],
                        steps=["1. Understand the user's request", "2. Provide a clear response"],
                    )
                )
            )

            # Print agent configuration
            print(f"Model: {agent.model}")
            print(f"Memory: {type(agent.memory).__name__}")
            print(f"System Prompt: {agent.system_prompt_generator.generate_prompt()}")

    .. py:method:: run(user_input: Optional[BaseIOSchema] = None) -> BaseIOSchema

        Runs the chat agent with the given user input synchronously.

        :param user_input: The input from the user
        :type user_input: Optional[BaseIOSchema]
        :return: The response from the chat agent
        :rtype: BaseIOSchema

        Example:

        .. code-block:: python

            # Basic synchronous interaction
            user_input = agent.input_schema(chat_message="Tell me about quantum computing")
            response = agent.run(user_input)

            # Print the response
            print("\nUser: Tell me about quantum computing")
            print(f"Assistant: {response.chat_message}")

    .. py:method:: run_async(user_input: Optional[BaseIOSchema] = None)

        Runs the chat agent with streaming output asynchronously.

        :param user_input: The input from the user
        :type user_input: Optional[BaseIOSchema]
        :return: An async generator yielding partial responses
        :rtype: AsyncGenerator[BaseIOSchema, None]

        Example:

        .. code-block:: python

            import asyncio
            import json

            async def stream_chat():
                # Initialize with AsyncOpenAI for streaming
                client = instructor.from_openai(AsyncOpenAI())
                agent = BaseAgent(BaseAgentConfig(client=client, model="gpt-4o-mini"))

                # Create input and stream response
                user_input = agent.input_schema(chat_message="Explain streaming")
                print("\nUser: Explain streaming")
                print("Assistant: ", end="", flush=True)

                async for partial_response in agent.run_async(user_input):
                    # Print each new token as it arrives
                    if hasattr(partial_response, "chat_message"):
                        print(partial_response.chat_message, end="", flush=True)
                print()  # New line at end

            asyncio.run(stream_chat())

    .. py:method:: reset_memory()

        Resets the agent's memory to its initial state.

        Example:

        .. code-block:: python

            # Use agent for a conversation
            response1 = agent.run(agent.input_schema(chat_message="Hello!"))
            print(f"First response: {response1.chat_message}")

            response2 = agent.run(agent.input_schema(chat_message="How are you?"))
            print(f"Second response: {response2.chat_message}")

            # Reset memory to start fresh
            agent.reset_memory()
            print("Memory reset to initial state")

    .. py:method:: get_context_provider(provider_name: str) -> Type[SystemPromptContextProviderBase]

        Retrieves a context provider by name.

        :param provider_name: The name of the context provider
        :type provider_name: str
        :return: The context provider if found
        :rtype: SystemPromptContextProviderBase
        :raises KeyError: If the context provider is not found

        Example:

        .. code-block:: python

            # Get a specific context provider
            try:
                provider = agent.get_context_provider("my_provider")
                print(f"Found provider: {provider}")
            except KeyError:
                print("Provider not found")

    .. py:method:: register_context_provider(provider_name: str, provider: SystemPromptContextProviderBase)

        Registers a new context provider.

        :param provider_name: The name of the context provider
        :type provider_name: str
        :param provider: The context provider instance
        :type provider: SystemPromptContextProviderBase

        Example:

        .. code-block:: python

            from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase

            # Create and register a custom context provider
            class MyContextProvider(SystemPromptContextProviderBase):
                def get_context(self) -> str:
                    return "Custom context for the agent"

            agent.register_context_provider("my_provider", MyContextProvider())
            print("Custom context provider registered")

    .. py:method:: unregister_context_provider(provider_name: str)

        Unregisters an existing context provider.

        :param provider_name: The name of the context provider to remove
        :type provider_name: str
        :raises KeyError: If the context provider is not found

        Example:

        .. code-block:: python

            # Remove a context provider
            try:
                agent.unregister_context_provider("my_provider")
                print("Provider unregistered")
            except KeyError:
                print("Provider not found")

Advanced Usage
^^^^^^^^^^^^

Here's a complete example showing how to create an interactive chat interface with streaming support:

.. code-block:: python

    import asyncio
    from openai import AsyncOpenAI, OpenAI
    import instructor
    from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

    async def chat_loop(streaming: bool = False):
        """Interactive chat loop with the AI agent."""
        # Initialize agent based on streaming mode
        if streaming:
            client = instructor.from_openai(AsyncOpenAI())
        else:
            client = instructor.from_openai(OpenAI())

        agent = BaseAgent(BaseAgentConfig(client=client, model="gpt-4o-mini"))
        print("Chat initialized. Type 'exit' to quit.")

        while True:
            # Get user input
            user_message = input("\nYou: ")
            if user_message.lower() == "exit":
                break

            # Process message
            user_input = agent.input_schema(chat_message=user_message)
            print("\nAssistant: ", end="", flush=True)

            if streaming:
                # Stream response token by token
                async for partial_response in agent.run_async(user_input):
                    if hasattr(partial_response, "chat_message"):
                        print(partial_response.chat_message, end="", flush=True)
                print()  # New line after response
            else:
                # Get complete response
                response = agent.run(user_input)
                print(response.chat_message)

    # Run interactive chat with streaming
    asyncio.run(chat_loop(streaming=True))

Input/Output Schemas
^^^^^^^^^^^^^^^^^

The BaseAgent uses Pydantic models for input and output validation. You can use the default schemas or create custom ones.

Default Schemas
"""""""""""""

.. py:class:: BaseAgentInputSchema

    Schema for user input to the agent.

    .. py:attribute:: chat_message
        :type: str

        The chat message sent by the user to the assistant.

.. py:class:: BaseAgentOutputSchema

    Schema for agent responses.

    .. py:attribute:: chat_message
        :type: str

        The chat message generated by the agent, with markdown support.

Custom Schema Example
"""""""""""""""""""

Here's an example of a custom input/output schema pair for an agent that provides suggested follow-up questions:

.. code-block:: python

    from typing import List
    from pydantic import Field
    from atomic_agents.lib.base.base_io_schema import BaseIOSchema

    class CustomInputSchema(BaseIOSchema):
        """Schema for user input with context."""
        chat_message: str = Field(
            ...,
            description="The chat message sent by the user."
        )
        context: str = Field(
            "",
            description="Optional context for the message."
        )

    class CustomOutputSchema(BaseIOSchema):
        """Schema for responses with suggested questions."""
        chat_message: str = Field(
            ...,
            description="The chat message from the agent."
        )
        suggested_questions: List[str] = Field(
            ...,
            description="Follow-up questions the user could ask."
        )

    # Use custom schemas with agent
    agent = BaseAgent(
        config=BaseAgentConfig(
            client=client,
            model="gpt-4o-mini",
            input_schema=CustomInputSchema,
            output_schema=CustomOutputSchema
        )
    )

    # Example usage
    response = agent.run(
        CustomInputSchema(
            chat_message="Tell me about quantum computing",
            context="The user is a beginner"
        )
    )
    print(f"Response: {response.chat_message}")
    print("\nSuggested questions:")
    for question in response.suggested_questions:
        print(f"- {question}")

Configuration
^^^^^^^^^^^

.. py:class:: BaseAgentConfig

    Configuration class for BaseAgent initialization.

    .. py:attribute:: client
        :type: instructor.client.Instructor

        Client for interacting with the language model.

    .. py:attribute:: model
        :type: str

        The model to use for generating responses.

    .. py:attribute:: memory
        :type: Optional[AgentMemory]

        Memory component for storing chat history.

    .. py:attribute:: system_prompt_generator
        :type: Optional[SystemPromptGenerator]

        Component for generating system prompts.

    .. py:attribute:: temperature
        :type: Optional[float]

        Temperature for response generation (0 to 1).

    .. py:attribute:: max_tokens
        :type: Optional[int]

        Maximum number of tokens in responses.
