import os
import instructor
import openai
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from typing import List
from pydantic import Field
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
    )

# Initialize a Rich Console for pretty console outputs
console = Console()

# Memory setup
memory = AgentMemory()


# Custom output schema
class CustomOutputSchema(BaseIOSchema):
    """This schema represents the response generated by the chat agent, including suggested follow-up questions."""

    chat_message: str = Field(
        ...,
        description="The chat message exchanged between the user and the chat agent.",
    )
    suggested_user_questions: List[str] = Field(
        ...,
        description="A list of suggested follow-up questions the user could ask the agent.",
    )


# Initialize memory with an initial message from the assistant
initial_message = CustomOutputSchema(
    chat_message="Hello! How can I assist you today?",
    suggested_user_questions=["What can you do?", "Tell me a joke", "Tell me about how you were made"],
)
memory.add_message("assistant", initial_message)

# OpenAI client setup using the Instructor library for async operations
client = instructor.from_openai(openai.AsyncOpenAI(api_key=API_KEY))

# Custom system prompt
system_prompt_generator = SystemPromptGenerator(
    background=[
        "This assistant is a knowledgeable AI designed to be helpful, friendly, and informative.",
        "It has a wide range of knowledge on various topics and can engage in diverse conversations.",
    ],
    steps=[
        "Analyze the user's input to understand the context and intent.",
        "Formulate a relevant and informative response based on the assistant's knowledge.",
        "Generate 3 suggested follow-up questions for the user to explore the topic further.",
    ],
    output_instructions=[
        "Provide clear, concise, and accurate information in response to user queries.",
        "Maintain a friendly and professional tone throughout the conversation.",
        "Conclude each response with 3 relevant suggested questions for the user.",
    ],
)
console.print(Panel(system_prompt_generator.generate_prompt(), width=console.width, style="bold cyan"), style="bold cyan")

# Agent setup with specified configuration and custom output schema
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        system_prompt_generator=system_prompt_generator,
        memory=memory,
        output_schema=CustomOutputSchema,
    )
)

# Display the initial message from the assistant
console.print(Text("Agent:", style="bold green"), end=" ")
console.print(Text(initial_message.chat_message, style="green"))

# Display initial suggested questions
console.print("\n[bold cyan]Suggested questions you could ask:[/bold cyan]")
for i, question in enumerate(initial_message.suggested_user_questions, 1):
    console.print(f"[cyan]{i}. {question}[/cyan]")
console.print()  # Add an empty line for better readability


async def main():
    # Start an infinite loop to handle user inputs and agent responses
    while True:
        # Prompt the user for input with a styled prompt
        user_input = console.input("[bold blue]You:[/bold blue] ")
        # Check if the user wants to exit the chat
        if user_input.lower() in ["/exit", "/quit"]:
            console.print("Exiting chat...")
            break

        # Process the user's input through the agent and get the streaming response
        input_schema = BaseAgentInputSchema(chat_message=user_input)
        console.print()  # Add newline before response

        # Use Live display to show streaming response
        with Live("", refresh_per_second=10, auto_refresh=True) as live:
            current_response = ""
            current_questions: List[str] = []

            async for partial_response in agent.run_async_stream(input_schema):
                if hasattr(partial_response, "chat_message") and partial_response.chat_message:
                    # Update the message part
                    if partial_response.chat_message != current_response:
                        current_response = partial_response.chat_message

                    # Update questions if available
                    if hasattr(partial_response, "suggested_user_questions"):
                        current_questions = partial_response.suggested_user_questions

                    # Combine all elements for display
                    display_text = Text.assemble(("Agent: ", "bold green"), (current_response, "green"))

                    # Add questions if we have them
                    if current_questions:
                        display_text.append("\n\n")
                        display_text.append("Suggested questions you could ask:\n", style="bold cyan")
                        for i, question in enumerate(current_questions, 1):
                            display_text.append(f"{i}. {question}\n", style="cyan")

                    live.update(display_text)

        console.print()  # Add an empty line for better readability


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
