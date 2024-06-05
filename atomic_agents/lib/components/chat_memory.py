import json
from typing import List, Dict, Union, Optional
from pydantic import BaseModel

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
    """

    def __init__(self):
        """
        Initializes the ChatMemory with an empty history.
        """
        self.history: List[Message] = []

    def add_message(self, role: str, content: Union[str, Dict], tool_message: Optional[Dict] = None, tool_id: Optional[str] = None) -> None:
        """
        Adds a message to the chat history.

        Args:
            role (str): The role of the message sender.
            content (Union[str, Dict]): The content of the message.
            tool_message (Optional[Dict]): Optional tool message to be included.
            tool_id (Optional[str]): Optional unique identifier for the tool call.
        """
        message = Message(role=role, content=json.dumps(content))
        if tool_message:
            if tool_id is None:
                tool_id = tool_message["id"]
            
            message.tool_calls = [tool_message]
            message.tool_call_id = tool_id
        elif role == "tool":
            message.tool_call_id = tool_id
        self.history.append(message)

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
        Loads the chat history from a list of dictionaries.

        Args:
            dict_list (List[Dict]): The list of messages as dictionaries.
        """
        self.history = [Message(**message_dict) for message_dict in dict_list]
        
    def copy(self) -> 'ChatMemory':
        """
        Creates a copy of the chat memory.

        Returns:
            ChatMemory: A copy of the chat memory.
        """
        new_memory = ChatMemory()
        new_memory.load(self.dump())