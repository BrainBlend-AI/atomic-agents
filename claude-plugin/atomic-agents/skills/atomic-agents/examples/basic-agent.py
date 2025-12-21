"""Basic Atomic Agent example with complete setup."""

import os
import instructor
import openai
from dotenv import load_dotenv

from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.chat_history import ChatHistory
from pydantic import Field

# Load environment variables
load_dotenv()


# ============================================================
# Schemas
# ============================================================

class QuestionInputSchema(BaseIOSchema):
    """User question input."""

    question: str = Field(
        ...,
        min_length=1,
        description="The user's question to answer"
    )


class AnswerOutputSchema(BaseIOSchema):
    """Agent answer output."""

    answer: str = Field(
        ...,
        description="The answer to the user's question"
    )
    confidence: str = Field(
        default="medium",
        description="Confidence level: low, medium, or high"
    )


# ============================================================
# Agent Configuration
# ============================================================

def create_qa_agent() -> AtomicAgent[QuestionInputSchema, AnswerOutputSchema]:
    """Create and configure the Q&A agent."""

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Create instructor-wrapped client
    client = instructor.from_openai(openai.OpenAI(api_key=api_key))

    # Configure system prompt
    system_prompt = SystemPromptGenerator(
        background=[
            "You are a helpful assistant that answers questions clearly and accurately.",
            "You provide concise answers while being thorough.",
            "You acknowledge when you're unsure about something.",
        ],
        steps=[
            "1. Carefully read and understand the question.",
            "2. Consider what information is needed to answer it.",
            "3. Formulate a clear, accurate response.",
            "4. Assess your confidence in the answer.",
        ],
        output_instructions=[
            "Provide direct answers without unnecessary preamble.",
            "Use simple language when possible.",
            "If uncertain, set confidence to 'low' and explain why.",
        ],
    )

    # Create agent config
    config = AgentConfig(
        client=client,
        model="gpt-4o-mini",
        history=ChatHistory(),
        system_prompt_generator=system_prompt,
    )

    # Return typed agent
    return AtomicAgent[QuestionInputSchema, AnswerOutputSchema](config=config)


# ============================================================
# Usage
# ============================================================

def main():
    """Run the Q&A agent."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    # Create agent
    agent = create_qa_agent()

    console.print(Panel("Q&A Agent Ready! Type 'quit' to exit.", style="bold green"))

    while True:
        # Get user input
        question = console.input("\n[bold blue]Question:[/bold blue] ").strip()

        if question.lower() in ("quit", "exit", "q"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        if not question:
            continue

        try:
            # Run agent
            response = agent.run(QuestionInputSchema(question=question))

            # Display response
            console.print(f"\n[bold green]Answer:[/bold green] {response.answer}")
            console.print(f"[dim]Confidence: {response.confidence}[/dim]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    main()
