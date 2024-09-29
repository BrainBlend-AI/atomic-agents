import uuid

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError


class Message(BaseModel):
    """
    Represents a message in the chat history.

    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'system', 'tool').
        content (Union[str, Dict]): The content of the message.
        tool_calls (Optional[List[Dict]]): Optional list of tool call messages.
        tool_call_id (Optional[str]): Optional unique identifier for the tool call.
        turn_id (Optional[str]): Unique identifier for the turn this message belongs to.
    """

    role: str
    content: Union[str, Dict]
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    turn_id: Optional[str] = None


class AgentMemory:
    """
    Manages the chat history for an AI agent.

    Attributes:
        history (List[Message]): A list of messages representing the chat history.
        max_messages (Optional[int]): Maximum number of turns to keep in history.
        current_turn_id (Optional[str]): The ID of the current turn.
    """

    def __init__(self, max_messages: Optional[int] = None):
        """
        Initializes the AgentMemory with an empty history and optional constraints.

        Args:
            max_messages (Optional[int]): Maximum number of turns to keep in history.
        """
        self.history: List[Message] = []
        self.max_messages = max_messages
        self.current_turn_id: Optional[str] = None

    def initialize_turn(self) -> None:
        """
        Initializes a new turn by generating a random turn ID.
        """
        self.current_turn_id = str(uuid.uuid4())

    def add_message(
        self,
        role: str,
        content: Union[str, Dict],
        tool_message: Optional[Dict] = None,
        tool_id: Optional[str] = None,
    ) -> None:
        """
        Adds a message to the chat history and manages overflow.

        Args:
            role (str): The role of the message sender.
            content (Union[str, Dict]): The content of the message.
            tool_message (Optional[Dict]): Optional tool message to be included.
            tool_id (Optional[str]): Optional unique identifier for the tool call.
        """
        if self.current_turn_id is None:
            self.initialize_turn()

        message = Message(role=role, content=content, turn_id=self.current_turn_id)
        if tool_message:
            message.tool_calls = [tool_message]
            message.tool_call_id = tool_id or tool_message.get("id")
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

    def get_history(self) -> List[Dict]:
        """
        Retrieves the chat history, filtering out unnecessary fields.

        Returns:
            List[Dict]: The list of messages in the chat history as dictionaries.
        """
        return [
            {
                "role": message.role,
                "content": message.content,
                **({"tool_calls": message.tool_calls} if message.tool_calls else {}),
                **({"tool_call_id": message.tool_call_id} if message.tool_call_id else {}),
            }
            for message in self.history
        ]

    def dump(self) -> List[Dict]:
        """
        Converts the chat history to a list of dictionaries, including turn_id.

        Returns:
            List[Dict]: The list of messages as dictionaries, including turn_id.
        """
        return [message.model_dump(exclude_none=True) for message in self.history]

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
                print(f"Error parsing message: {e}")
                continue
        # Set the current_turn_id to the last message's turn_id if available
        if self.history:
            self.current_turn_id = self.history[-1].turn_id

    def copy(self) -> "AgentMemory":
        """
        Creates a copy of the chat memory.

        Returns:
            AgentMemory: A copy of the chat memory.
        """
        new_memory = AgentMemory(max_messages=self.max_messages)
        new_memory.load(self.dump())
        new_memory.current_turn_id = self.current_turn_id
        return new_memory

    def get_current_turn_id(self) -> Optional[str]:
        """
        Returns the current turn ID.

        Returns:
            Optional[str]: The current turn ID, or None if not set.
        """
        return self.current_turn_id

    def get_message_count(self) -> int:
        """
        Returns the number of messages in the chat history.

        Returns:
            int: The number of messages.
        """
        return len(self.history)
