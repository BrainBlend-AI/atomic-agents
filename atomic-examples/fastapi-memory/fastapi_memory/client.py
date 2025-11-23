"""Interactive command-line client for the FastAPI Atomic Agents example.

This client provides a user-friendly interface to interact with the FastAPI
chat server, supporting both streaming and non-streaming modes, as well as
session management capabilities.
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import List, Optional

import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

console = Console()

# Configuration
BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30.0
USER_ID_FILE = Path.home() / ".fastapi_memory_user_id"


def get_or_create_user_id() -> str:
    """Get existing user ID from file or create a new one.

    Returns:
        User identifier (UUID)
    """
    if USER_ID_FILE.exists():
        user_id = USER_ID_FILE.read_text().strip()
        if user_id:
            return user_id

    # Generate new user ID
    user_id = str(uuid.uuid4())
    USER_ID_FILE.write_text(user_id)
    console.print(f"[dim]Created new user ID: {user_id}[/dim]\n")
    return user_id


def _fetch_user_sessions(user_id: str) -> Optional[List[dict]]:
    """Fetch the list of sessions for the current user.

    Args:
        user_id: User identifier

    Returns:
        List of session dicts with 'session_id' and 'created_at', or None if request failed
    """
    try:
        response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("sessions", [])
    except Exception as e:
        console.print(f"[bold red]Error fetching sessions:[/bold red] {str(e)}")
        return None


def _create_new_session(user_id: str) -> Optional[str]:
    """Create a new session for the user.

    Args:
        user_id: User identifier

    Returns:
        New session ID or None if creation failed
    """
    try:
        response = httpx.post(f"{BASE_URL}/users/{user_id}/sessions", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("session_id")
    except Exception as e:
        console.print(f"[bold red]Error creating session:[/bold red] {str(e)}")
        return None


def _delete_session(user_id: str, session_id: str) -> bool:
    """Delete a session.

    Args:
        user_id: User identifier
        session_id: Session identifier to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        response = httpx.delete(f"{BASE_URL}/users/{user_id}/sessions/{session_id}", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print("\n[bold red]✗ Session not found[/bold red]")
        else:
            console.print(f"\n[bold red]HTTP Error {e.response.status_code}:[/bold red] {str(e)}")
        return False
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        return False


def select_or_create_session(user_id: str) -> Optional[str]:
    """Show user's sessions and let them select one or create new.

    Args:
        user_id: User identifier

    Returns:
        Selected or newly created session ID, or None if cancelled
    """
    console.clear()
    console.print(
        Panel.fit(
            "[bold magenta]Session Selection[/bold magenta]",
            border_style="magenta",
        )
    )
    console.print()

    # Fetch existing sessions
    sessions = _fetch_user_sessions(user_id)
    if sessions is None:
        console.print("[yellow]Could not fetch sessions. Try again?[/yellow]")
        retry = Prompt.ask("Retry", choices=["yes", "no"], default="yes")
        if retry == "yes":
            return select_or_create_session(user_id)
        return None

    # Display sessions
    if sessions:
        console.print("[bold cyan]Your sessions:[/bold cyan]\n")
        table = Table(show_header=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Session ID", style="cyan")
        table.add_column("Created At", style="green")

        for i, session in enumerate(sessions, 1):
            created_at = session.get("created_at", "Unknown")
            # Truncate session ID for display
            display_id = session["session_id"][:8] + "..." if len(session["session_id"]) > 8 else session["session_id"]
            table.add_row(str(i), display_id, created_at)

        console.print(table)
        console.print()

        # Let user select
        console.print("[dim]Options:[/dim]")
        console.print("  [cyan]1-{}[/cyan]: Select existing session".format(len(sessions)))
        console.print("  [cyan]new[/cyan]: Create new session")
        console.print("  [cyan]cancel[/cyan]: Go back")
        console.print()

        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]")

        if choice.lower() == "cancel":
            return None
        elif choice.lower() == "new":
            console.print("\n[dim]Creating new session...[/dim]")
            session_id = _create_new_session(user_id)
            if session_id:
                console.print(f"[bold green]✓ Created session: {session_id[:8]}...[/bold green]\n")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                return session_id
            return None
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(sessions):
                    return sessions[index]["session_id"]
                else:
                    console.print("[bold red]Invalid selection[/bold red]")
                    Prompt.ask("[dim]Press Enter to try again[/dim]", default="")
                    return select_or_create_session(user_id)
            except ValueError:
                console.print("[bold red]Invalid input[/bold red]")
                Prompt.ask("[dim]Press Enter to try again[/dim]", default="")
                return select_or_create_session(user_id)
    else:
        console.print("[yellow]You don't have any sessions yet.[/yellow]\n")
        create = Prompt.ask("Create new session", choices=["yes", "no"], default="yes")
        if create == "yes":
            console.print("\n[dim]Creating new session...[/dim]")
            session_id = _create_new_session(user_id)
            if session_id:
                console.print(f"[bold green]✓ Created session: {session_id[:8]}...[/bold green]\n")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                return session_id
        return None


def _fetch_conversation_history(user_id: str, session_id: str) -> Optional[List[dict]]:
    """Fetch conversation history for a session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        List of message dicts with 'role', 'content', 'timestamp', or None if request failed
    """
    try:
        response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions/{session_id}/history", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("messages", [])
    except Exception as e:
        console.print(f"[bold red]Error fetching history:[/bold red] {str(e)}")
        return None


def _display_conversation_history(messages: List[dict]) -> None:
    """Display conversation history.

    Args:
        messages: List of message dicts with 'role' and 'content'
    """
    if not messages:
        return

    console.print("[dim]─── Conversation History ───[/dim]\n")
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "user":
            console.print(Text("You:", style="bold blue"), end=" ")
            console.print(content)
        elif role == "assistant":
            console.print(Text("Agent:", style="bold green"), end=" ")
            console.print(Text(content, style="green"))

            if msg.get("suggested_questions"):
                _display_suggested_questions(msg["suggested_questions"])
        console.print()

    console.print("[dim]─── End of History ───[/dim]\n")


def _display_suggested_questions(questions: List[str]) -> None:
    """Display suggested follow-up questions.

    Args:
        questions: List of suggested question strings
    """
    if questions:
        console.print("\n[bold cyan]Suggested questions:[/bold cyan]")
        for i, question in enumerate(questions, 1):
            console.print(f"[cyan]{i}. {question}[/cyan]")


def chat_non_streaming(user_id: str, session_id: str) -> None:
    """Run interactive chat in non-streaming mode.

    Args:
        user_id: User identifier
        session_id: Session identifier
    """
    console.clear()
    console.print(Panel("[bold cyan]Non-Streaming Chat Mode[/bold cyan]"))
    console.print(f"[dim]Session: {session_id[:8]}...[/dim]")
    console.print("[dim]Type '/exit' to return to menu[/dim]\n")

    # Fetch and display conversation history
    history = _fetch_conversation_history(user_id, session_id)
    if history and len(history) > 0:
        _display_conversation_history(history)
    else:
        # No history - show welcome message
        console.print(Text("Agent:", style="bold green"), end=" ")
        console.print("Hello! How can I assist you today?")

        # Display initial suggested questions
        initial_questions = [
            "What can you help me with?",
            "Tell me about your capabilities",
            "How does this chat system work?",
        ]
        _display_suggested_questions(initial_questions)
        console.print()

    while True:
        user_input = Prompt.ask("[bold blue]You[/bold blue]")

        if user_input.lower() == "/exit":
            break

        try:
            response = httpx.post(
                f"{BASE_URL}/chat",
                json={"message": user_input, "user_id": user_id, "session_id": session_id},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            console.print()
            console.print(Text("Agent:", style="bold green"), end=" ")
            console.print(Text(data["response"], style="green"))

            _display_suggested_questions(data.get("suggested_questions", []))
            console.print()

        except httpx.HTTPStatusError as e:
            console.print(f"\n[bold red]HTTP Error {e.response.status_code}:[/bold red] {str(e)}\n")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")


async def chat_streaming_async(user_id: str, session_id: str) -> None:
    """Run interactive chat in streaming mode.

    Args:
        user_id: User identifier
        session_id: Session identifier
    """
    console.clear()
    console.print(Panel("[bold cyan]Streaming Chat Mode[/bold cyan]"))
    console.print(f"[dim]Session: {session_id[:8]}...[/dim]")
    console.print("[dim]Type '/exit' to return to menu[/dim]\n")

    # Fetch and display conversation history
    history = _fetch_conversation_history(user_id, session_id)
    if history and len(history) > 0:
        _display_conversation_history(history)
    else:
        # No history - show welcome message
        console.print(Text("Agent:", style="bold green"), end=" ")
        console.print("Hello! How can I assist you today?")

        # Display initial suggested questions
        initial_questions = [
            "What can you help me with?",
            "Tell me about your capabilities",
            "How does this chat system work?",
        ]
        _display_suggested_questions(initial_questions)
        console.print()

    while True:
        user_input = Prompt.ask("[bold blue]You[/bold blue]")

        if user_input.lower() == "/exit":
            break

        try:
            console.print()
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{BASE_URL}/chat/stream",
                    json={"message": user_input, "user_id": user_id, "session_id": session_id},
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    response.raise_for_status()

                    with Live("", refresh_per_second=10, auto_refresh=True) as live:
                        current_response = ""
                        current_questions = []

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip():
                                    data = json.loads(data_str)

                                    if "error" in data:
                                        console.print(f"\n[bold red]Error:[/bold red] {data['error']}\n")
                                        break

                                    if data.get("response"):
                                        current_response = data["response"]
                                    if data.get("suggested_questions"):
                                        current_questions = data["suggested_questions"]

                                    display_text = Text.assemble(("Agent: ", "bold green"), (current_response, "green"))

                                    if current_questions:
                                        display_text.append("\n\n")
                                        display_text.append("Suggested questions:\n", style="bold cyan")
                                        for i, question in enumerate(current_questions, 1):
                                            display_text.append(f"{i}. {question}\n", style="cyan")

                                    live.update(display_text)

            console.print()

        except httpx.HTTPStatusError as e:
            console.print(f"\n[bold red]HTTP Error {e.response.status_code}:[/bold red] {str(e)}\n")
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")


def manage_sessions(user_id: str) -> None:
    """Display and manage user's sessions.

    Args:
        user_id: User identifier
    """
    console.clear()
    console.print(Panel("[bold cyan]Manage Sessions[/bold cyan]"))
    console.print()

    sessions = _fetch_user_sessions(user_id)
    if sessions is None:
        console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return

    if not sessions:
        console.print("[yellow]No active sessions found[/yellow]")
        console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return

    # Display sessions
    console.print("[bold]Your sessions:[/bold]\n")
    table = Table(show_header=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Session ID", style="cyan")
    table.add_column("Created At", style="green")

    for i, session in enumerate(sessions, 1):
        created_at = session.get("created_at", "Unknown")
        display_id = session["session_id"][:16]
        table.add_row(str(i), display_id, created_at)

    console.print(table)
    console.print()

    # Ask which to delete
    console.print("[dim]Enter session number to delete, or 'cancel' to go back[/dim]")
    choice = Prompt.ask("[bold yellow]Delete session[/bold yellow]", default="cancel")

    if choice.lower() != "cancel":
        try:
            index = int(choice) - 1
            if 0 <= index < len(sessions):
                session_to_delete = sessions[index]["session_id"]
                confirm = Prompt.ask(
                    f"\n[bold yellow]Delete session {session_to_delete[:8]}...?[/bold yellow]",
                    choices=["yes", "no"],
                    default="no",
                )
                if confirm == "yes":
                    if _delete_session(user_id, session_to_delete):
                        console.print("\n[bold green]✓ Session deleted[/bold green]")
            else:
                console.print("[bold red]Invalid selection[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input[/bold red]")

    console.print()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def show_main_menu(user_id: str) -> str:
    """Display the main menu and get user's choice.

    Args:
        user_id: User identifier

    Returns:
        User's menu selection as a string
    """
    console.clear()
    console.print(
        Panel.fit(
            "[bold magenta]FastAPI Atomic Agents - Interactive Client[/bold magenta]",
            border_style="magenta",
        )
    )
    console.print(f"[dim]User ID: {user_id[:8]}...[/dim]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan bold", justify="right")
    table.add_column(style="white")

    table.add_row("1", "Start Chat (Non-Streaming)")
    table.add_row("2", "Start Chat (Streaming)")
    table.add_row("3", "Manage Sessions")
    table.add_row("4", "Exit")

    console.print(table)
    console.print()

    choice = Prompt.ask(
        "[bold yellow]Select an option[/bold yellow]",
        choices=["1", "2", "3", "4"],
        default="1",
    )
    return choice


async def main() -> None:
    """Main application loop."""
    user_id = get_or_create_user_id()

    while True:
        choice = show_main_menu(user_id)

        if choice == "1":
            # Non-streaming chat
            session_id = select_or_create_session(user_id)
            if session_id:
                chat_non_streaming(user_id, session_id)

        elif choice == "2":
            # Streaming chat
            session_id = select_or_create_session(user_id)
            if session_id:
                await chat_streaming_async(user_id, session_id)

        elif choice == "3":
            # Manage sessions
            manage_sessions(user_id)

        elif choice == "4":
            console.print("\n[bold cyan]Goodbye![/bold cyan]\n")
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold cyan]Goodbye![/bold cyan]\n")
