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