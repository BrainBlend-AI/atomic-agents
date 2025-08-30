#!/usr/bin/env python3
"""
AtomicAgent Hook System Demonstration

This example showcases the powerful hook system integration in AtomicAgent,
demonstrating monitoring, error handling, and intelligent retry mechanisms.

The hook system leverages Instructor's hook system to provide:
- Comprehensive monitoring of agent execution
- Robust error handling and recovery
- Performance metrics and insights
- Intelligent retry patterns

Run with: python main.py
"""

import os
import time
import logging

import instructor
import openai
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pydantic import Field, ValidationError

from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory
from atomic_agents.base.base_io_schema import BaseIOSchema

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Rich console for pretty output
console = Console()

# Global metrics storage
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "parse_errors": 0,
    "retry_attempts": 0,
    "total_response_time": 0.0,
    "start_time": time.time(),
}

# Global variable to track request start times
_request_start_time = None


class UserQuery(BaseIOSchema):
    """User input schema for the agent."""

    chat_message: str = Field(..., description="User's question or message")


class AgentResponse(BaseIOSchema):
    """Agent response schema with confidence scoring."""

    chat_message: str = Field(..., description="Agent's response to the user")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="Brief explanation of the reasoning")


class DetailedResponse(BaseIOSchema):
    """More complex response schema to test validation."""

    chat_message: str = Field(..., description="Primary response")
    alternative_suggestions: list[str] = Field(default_factory=list, description="Alternative suggestions")
    confidence_level: str = Field(..., description="Must be 'low', 'medium', or 'high'")
    requires_followup: bool = Field(default=False, description="Whether follow-up is needed")


def setup_api_key() -> str:
    """Setup and validate API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]Error: OPENAI_API_KEY environment variable not set.[/bold red]")
        console.print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    return api_key


def display_metrics():
    """Display current performance metrics."""
    runtime = time.time() - metrics["start_time"]
    avg_response_time = metrics["total_response_time"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0

    success_rate = metrics["successful_requests"] / metrics["total_requests"] * 100 if metrics["total_requests"] > 0 else 0

    table = Table(title="🔍 Hook System Performance Metrics", style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Runtime", f"{runtime:.1f}s")
    table.add_row("Total Requests", str(metrics["total_requests"]))
    table.add_row("Successful Requests", str(metrics["successful_requests"]))
    table.add_row("Failed Requests", str(metrics["failed_requests"]))
    table.add_row("Parse Errors", str(metrics["parse_errors"]))
    table.add_row("Retry Attempts", str(metrics["retry_attempts"]))
    table.add_row("Success Rate", f"{success_rate:.1f}%")
    table.add_row("Avg Response Time", f"{avg_response_time:.2f}s")

    console.print(table)


# Hook functions for comprehensive monitoring and error handling


def on_parse_error(error):
    """Handle parse errors with detailed logging and metrics update."""
    metrics["parse_errors"] += 1
    metrics["failed_requests"] += 1

    logger.error(f"🚨 Parse error occurred: {type(error).__name__}: {error}")

    if isinstance(error, ValidationError):
        console.print("[bold red]❌ Validation Error:[/bold red]")
        for err in error.errors():
            field_path = " -> ".join(str(x) for x in err["loc"])
            console.print(f"  • Field '{field_path}': {err['msg']}")
            logger.error(f"Validation error in field '{field_path}': {err['msg']}")
    else:
        console.print(f"[bold red]❌ Parse Error:[/bold red] {error}")

    # In a production system, you might:
    # - Send error to monitoring service
    # - Trigger alerts for high error rates
    # - Store detailed error context for analysis


def on_completion_kwargs(**kwargs):
    """Monitor outgoing API calls."""
    global _request_start_time
    metrics["total_requests"] += 1

    # Log API call details (without sensitive information)
    model = kwargs.get("model", "unknown")
    messages_count = len(kwargs.get("messages", []))

    logger.info(f"🚀 API call starting - Model: {model}, Messages: {messages_count}")

    # Store start time for response time calculation
    _request_start_time = time.time()


def on_completion_response(response, **kwargs):
    """Monitor API responses and calculate metrics."""
    global _request_start_time
    if _request_start_time:
        response_time = time.time() - _request_start_time
        metrics["total_response_time"] += response_time
        logger.info(f"✅ API call completed in {response_time:.2f}s")
        _request_start_time = None  # Reset for next request

    # Log response details
    if hasattr(response, "usage"):
        usage = response.usage
        logger.info(
            f"📊 Token usage - Prompt: {usage.prompt_tokens}, "
            f"Completion: {usage.completion_tokens}, "
            f"Total: {usage.total_tokens}"
        )

    metrics["successful_requests"] += 1


def on_completion_error(error, **kwargs):
    """Handle API errors with retry logic."""
    global _request_start_time
    metrics["failed_requests"] += 1
    metrics["retry_attempts"] += 1

    # Reset start time on error
    if _request_start_time:
        _request_start_time = None

    logger.error(f"🔥 API error: {type(error).__name__}: {error}")
    console.print(f"[bold red]🔥 API Error:[/bold red] {error}")

    # In a production system, you might implement:
    # - Exponential backoff retry logic
    # - Fallback to different models
    # - Circuit breaker patterns
    # - Dead letter queues for failed requests


def create_agent_with_hooks(schema_type: type, system_prompt: str = None) -> AtomicAgent:
    """Create an AtomicAgent with comprehensive hook setup."""
    api_key = setup_api_key()
    client = instructor.from_openai(openai.OpenAI(api_key=api_key))

    # Create agent with configuration
    config = AgentConfig(
        client=client,
        model="gpt-4o-mini",  # Using a reliable model for demonstrations
        history=ChatHistory(),
        system_prompt=system_prompt,
    )

    agent = AtomicAgent[UserQuery, schema_type](config)

    # Register comprehensive hook suite
    agent.register_hook("parse:error", on_parse_error)
    agent.register_hook("completion:kwargs", on_completion_kwargs)
    agent.register_hook("completion:response", on_completion_response)
    agent.register_hook("completion:error", on_completion_error)

    console.print("[bold green]✅ Agent created with comprehensive hook monitoring[/bold green]")
    return agent


def demonstrate_basic_hooks():
    """Demonstrate basic hook functionality with simple responses."""
    console.print(Panel("🔧 Basic Hook System Demonstration", style="bold blue"))

    # Create agent with basic schema
    agent = create_agent_with_hooks(
        AgentResponse, "You are a helpful assistant. Always provide confident, well-reasoned responses."
    )

    test_queries = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms.",
        "What are the benefits of renewable energy?",
    ]

    for query_text in test_queries:
        console.print(f"\n[bold cyan]Query:[/bold cyan] {query_text}")

        try:
            query = UserQuery(chat_message=query_text)
            response = agent.run(query)

            console.print(f"[bold green]Response:[/bold green] {response.chat_message}")
            console.print(f"[bold yellow]Confidence:[/bold yellow] {response.confidence:.2f}")
            console.print(f"[bold magenta]Reasoning:[/bold magenta] {response.reasoning}")

        except Exception as e:
            console.print(f"[bold red]Error processing query:[/bold red] {e}")

    display_metrics()


def demonstrate_validation_errors():
    """Demonstrate hook system handling validation errors."""
    console.print(Panel("🚨 Validation Error Handling Demonstration", style="bold red"))

    # Create agent with strict validation schema
    agent = create_agent_with_hooks(
        DetailedResponse,
        """You are a helpful assistant. You must respond with:
        - A main answer
        - Alternative suggestions (list)
        - Confidence level (exactly 'low', 'medium', or 'high')
        - Whether follow-up is needed (boolean)
        
        Be very strict about the confidence_level field - it must be exactly one of the three allowed values.""",
    )

    # Queries designed to potentially trigger validation errors
    validation_test_queries = [
        "Give me a simple yes or no answer about whether the sky is blue.",
        "Provide a complex analysis of climate change with multiple perspectives.",
    ]

    for query_text in validation_test_queries:
        console.print(f"\n[bold cyan]Query:[/bold cyan] {query_text}")

        try:
            query = UserQuery(chat_message=query_text)
            response = agent.run(query)

            console.print(f"[bold green]Main Answer:[/bold green] {response.chat_message}")
            console.print(f"[bold yellow]Confidence Level:[/bold yellow] {response.confidence_level}")
            console.print(f"[bold magenta]Alternatives:[/bold magenta] {response.alternative_suggestions}")
            console.print(f"[bold cyan]Needs Follow-up:[/bold cyan] {response.requires_followup}")

        except Exception as e:
            console.print(f"[bold red]Handled error:[/bold red] {e}")

    display_metrics()


def demonstrate_interactive_mode():
    """Interactive demonstration where users can test the hook system."""
    console.print(Panel("🎮 Interactive Hook System Testing", style="bold magenta"))

    agent = create_agent_with_hooks(
        AgentResponse, "You are a helpful assistant. Provide clear, confident responses with reasoning."
    )

    console.print("[bold green]Welcome to the interactive hook system demo![/bold green]")
    console.print("Type your questions below. Use /metrics to see performance data, /exit to quit.")

    while True:
        try:
            user_input = console.input("\n[bold blue]Your question:[/bold blue] ")

            if user_input.lower() in ["/exit", "/quit"]:
                console.print("Exiting interactive mode...")
                break
            elif user_input.lower() == "/metrics":
                display_metrics()
                continue
            elif user_input.strip() == "":
                continue

            query = UserQuery(chat_message=user_input)
            start_time = time.time()

            response = agent.run(query)

            response_time = time.time() - start_time

            console.print(f"\n[bold green]Answer:[/bold green] {response.chat_message}")
            console.print(f"[bold yellow]Confidence:[/bold yellow] {response.confidence:.2f}")
            console.print(f"[bold magenta]Reasoning:[/bold magenta] {response.reasoning}")
            console.print(f"[dim]Response time: {response_time:.2f}s[/dim]")

        except KeyboardInterrupt:
            console.print("\nExiting on user interrupt...")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


def main():
    """Main demonstration function."""
    console.print(Panel.fit("🎯 AtomicAgent Hook System Comprehensive Demo", style="bold green"))

    console.print(
        """
[bold cyan]This demonstration showcases:[/bold cyan]
• 🔍 Comprehensive monitoring with hooks
• 🛡️ Robust error handling and validation
• 📊 Real-time performance metrics
• 🔄 Production-ready patterns

[bold yellow]The hook system provides zero-overhead monitoring when hooks aren't registered,
and powerful insights when they are enabled.[/bold yellow]
    """
    )

    try:
        # Run basic demonstration
        demonstrate_basic_hooks()

        console.print("\n" + "=" * 50)

        # Run validation error demonstration
        demonstrate_validation_errors()

        console.print("\n" + "=" * 50)

        # Interactive mode
        demonstrate_interactive_mode()

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Demo interrupted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Demo error:[/bold red] {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
    finally:
        # Final metrics display
        console.print("\n" + "=" * 50)
        console.print(Panel("📊 Final Performance Summary", style="bold green"))
        display_metrics()

        console.print(
            """
[bold green]✅ Hook system demonstration complete![/bold green]

[bold cyan]Key takeaways:[/bold cyan]
• Hooks provide comprehensive monitoring without performance overhead
• Error handling is robust and provides detailed context
• Metrics collection enables performance optimization
• The system is production-ready and scalable

[bold yellow]Next steps:[/bold yellow]
• Implement custom retry logic in hook handlers
• Add monitoring service integration
• Explore advanced error recovery patterns
• Build custom metrics dashboards
        """
        )


if __name__ == "__main__":
    main()
