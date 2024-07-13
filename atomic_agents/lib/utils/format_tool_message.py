import uuid
import json
from typing import Dict, Optional, Type

from pydantic import BaseModel


def format_tool_message(tool_call: Type[BaseModel], tool_id: Optional[str] = None) -> Dict:
    """
    Formats a message for a tool call.

    Args:
        tool_call (Type[BaseModel]): The Pydantic model instance representing the tool call.
        tool_id (str, optional): The unique identifier for the tool call. If not provided, a random UUID will be generated.

    Returns:
        Dict: A formatted message dictionary for the tool call.
    """
    if tool_id is None:
        tool_id = str(uuid.uuid4())

    return {
        "id": tool_id,
        "type": "function",
        "function": {
            "name": tool_call.model_config["title"],
            "arguments": json.dumps(tool_call.model_dump(), separators=(', ', ': '))
        },
    }