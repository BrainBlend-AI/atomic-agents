from typing import List, Dict, Union, Optional
from pydantic import BaseModel, ValidationError

class Message(BaseModel):
    """
    Represents a message in the chat history.

    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'system', 'tool').
        content (Union[str, Dict]): The content of the message.
        tool_calls (Optional[List[Dict]]): Optional list of tool call messages.
        tool_call_id (Optional[str]): Optional unique identifier for the tool call.
    """
    role: str
    content: Union[str, Dict]
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None

class ChatMemory:
    """
    Manages the chat history for an AI agent.

    Attributes:
        history (List[Message]): A list of messages representing the chat history.
        max_messages (Optional[int]): Maximum number of turns to keep in history.
    """

    def __init__(self, max_messages: Optional[int] = None):
        """
        Initializes the ChatMemory with an empty history and optional constraints.

        Args:
            max_messages (Optional[int]): Maximum number of turns to keep in history.
        """
        self.history: List[Message] = []
        self.max_messages = max_messages

    def add_message(self, role: str, content: Union[str, Dict], tool_message: Optional[Dict] = None, tool_id: Optional[str] = None) -> None:
        """
        Adds a message to the chat history and manages overflow.

        Args:
            role (str): The role of the message sender.
            content (Union[str, Dict]): The content of the message.
            tool_message (Optional[Dict]): Optional tool message to be included.
            tool_id (Optional[str]): Optional unique identifier for the tool call.
        """
        message = Message(role=role, content=content)
        if tool_message:
            if tool_id is None:
                tool_id = tool_message["id"]
            
            message.tool_calls = [tool_message]
            message.tool_call_id = tool_id
        elif role == "tool":
            message.tool_call_id = tool_id
        
        self.history.append(message)
        self._manage_overflow()

    def _manage_overflow(self) -> None:
        """
        Manages the chat history overflow based on max_messages constraint.
        """
        if self.max_messages is not None:
            while len(self.history) > self.max_messages:
                self.history.pop(0)

    def get_history(self) -> List[Message]:
        """
        Retrieves the chat history.

        Returns:
            List[Message]: The list of messages in the chat history.
        """
        return self.history

    def dump(self) -> List[Dict]:
        """
        Converts the chat history to a list of dictionaries.

        Returns:
            List[Dict]: The list of messages as dictionaries.
        """
        return [message.model_dump() for message in self.history]

    def load(self, dict_list: List[Dict]) -> None:
        """
        Loads the chat history from a list of dictionaries using Pydantic's parsing.

        Args:
            dict_list (List[Dict]): The list of messages as dictionaries.
        """
        self.history = []
        for message_dict in dict_list:
            try:
                message = Message.model_validate(message_dict)
                self.history.append(message)
            except ValidationError as e:
                # Handle validation errors, e.g., log them or raise a custom exception
                print(f"Error parsing message: {e}")
                # Optionally, you might want to skip invalid messages or raise an exception
                # depending on your error handling strategy
                continue

        # Optionally, manage overflow after loading all messages
        self._manage_overflow()
        
    def copy(self) -> 'ChatMemory':
        """
        Creates a copy of the chat memory.

        Returns:
            ChatMemory: A copy of the chat memory.
        """
        new_memory = ChatMemory(max_messages=self.max_messages)
        new_memory.load(self.dump())
        
        return new_memory

    def get_message_count(self) -> int:
        """
        Returns the number of messages in the chat history.

        Returns:
            int: The number of messages.
        """
        return len(self.history)


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table

    console = Console()

    def print_panel(title, content):
        console.print(Panel(content, title=title, expand=False, border_style="cyan"))

    # Create a ChatMemory with a maximum of 5 messages
    memory = ChatMemory(max_messages=5)

    console.print("[bold magenta]ChatMemory Test Cases[/bold magenta]", justify="center")
    console.print()

    # Test Case 1
    content = Text()
    memory.add_message("user", "Hello, how are you?")
    memory.add_message("assistant", "I'm doing well, thank you for asking!")
    memory.add_message("user", "Can you help me with the weather?")
    content.append(f"Total messages: {memory.get_message_count()}\n\n")
    content.append("Current history:\n")
    for msg in memory.get_history():
        content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue'}")
    print_panel("1. Adding regular messages", content)

    # Test Case 2
    content = Text()
    tool_message = {
        "id": "weather_1",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"location": "New York"}'}
    }
    memory.add_message("assistant", "Certainly! I'll check the weather for you.", tool_message=tool_message)
    content.append(f"Total messages: {memory.get_message_count()}\n\n")
    content.append("Last message:\n")
    last_msg = memory.get_history()[-1]
    content.append(f"- {last_msg.role}: {last_msg.content}\n", style="blue")
    content.append(f"  Tool call: {last_msg.tool_calls}\n", style="yellow")
    print_panel("2. Adding a message with a tool call", content)

    # Test Case 3
    content = Text()
    memory.add_message("tool", "The weather in New York is sunny with a high of 75°F.", tool_id="weather_1")
    content.append(f"Total messages: {memory.get_message_count()}\n\n")
    content.append("Last message:\n")
    last_msg = memory.get_history()[-1]
    content.append(f"- {last_msg.role}: {last_msg.content}\n", style="yellow")
    content.append(f"  Tool call ID: {last_msg.tool_call_id}\n", style="yellow")
    print_panel("3. Adding a tool response", content)

    # Test Case 4
    content = Text()
    memory.add_message("user", "Thanks for the weather info!")
    content.append(f"Total messages: {memory.get_message_count()}\n\n")
    content.append("Current history (should only have 5 most recent messages):\n")
    for msg in memory.get_history():
        content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue' if msg.role == 'assistant' else 'yellow'}")
    print_panel("4. Testing overflow management", content)

    # Test Case 5
    content = Text()
    dumped_data = memory.dump()
    content.append("Dumped data:\n")
    content.append(str(dumped_data), style="dim")
    content.append("\n\n")
    new_memory = ChatMemory(max_messages=5)
    new_memory.load(dumped_data)
    content.append("Loaded memory:\n")
    for msg in new_memory.get_history():
        content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue' if msg.role == 'assistant' else 'yellow'}")
    content.append(f"\nTotal messages in loaded memory: {new_memory.get_message_count()}")
    print_panel("5. Testing dump and load", content)

    # Test Case 6
    content = Text()
    copied_memory = memory.copy()
    content.append(f"Original memory message count: {memory.get_message_count()}\n")
    content.append(f"Copied memory message count: {copied_memory.get_message_count()}\n\n")
    content.append("Adding a message to the copy:\n")
    copied_memory.add_message("user", "This is a new message in the copy.")
    content.append(f"Original memory message count: {memory.get_message_count()}\n")
    content.append(f"Copied memory message count: {copied_memory.get_message_count()}")
    print_panel("6. Testing copy", content)

    # Test Case 7
    content = Text()
    large_buffer = [
        {"role": "user", "content": f"Message {i}"} for i in range(10)
    ]
    large_memory = ChatMemory(max_messages=5)
    large_memory.load(large_buffer)
    content.append(f"Total messages after loading large buffer: {large_memory.get_message_count()}\n\n")
    content.append("Current history (should only have 5 most recent messages):\n")
    for msg in large_memory.get_history():
        content.append(f"- {msg.role}: {msg.content}\n", style="green")
    print_panel("7. Testing loading a larger buffer than max_messages", content)

    # Test Case 8
    content = Text()
    mixed_memory = ChatMemory(max_messages=10)
    mixed_memory.add_message("user", "Hello")
    mixed_memory.add_message("assistant", {"text": "Hi there!", "confidence": 0.95})
    mixed_memory.add_message("system", {"command": "reset_conversation"})
    content.append(f"Total messages in mixed memory: {mixed_memory.get_message_count()}\n\n")
    content.append("Mixed memory contents:\n")
    for msg in mixed_memory.get_history():
        content.append(f"- {msg.role}: {msg.content}\n", style=f"{'green' if msg.role == 'user' else 'blue' if msg.role == 'assistant' else 'red'}")
    print_panel("8. Testing adding messages with different content types", content)