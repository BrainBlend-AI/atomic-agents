import uuid
import json
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema


class Message(BaseModel):
    """
    Represents a message in the chat history.

    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'system', 'tool').
        content (BaseIOSchema): The content of the message.
        turn_id (Optional[str]): Unique identifier for the turn this message belongs to.
    """

    role: str
    content: BaseIOSchema
    turn_id: Optional[str] = None


class ChatHistory:
    """
    Manages the chat history for an AI agent.

    Attributes:
        history (List[Message]): A list of messages representing the chat history.
        max_messages (Optional[int]): Maximum number of messages to keep in history.
        current_turn_id (Optional[str]): The ID of the current turn.
    """

    def __init__(self, max_messages: Optional[int] = None):
        """
        Initializes the ChatHistory with an empty history and optional constraints.

        Args:
            max_messages (Optional[int]): Maximum number of messages to keep in history.
                When exceeded, oldest messages are removed first.
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
        content: BaseIOSchema,
    ) -> None:
        """
        Adds a message to the chat history and manages overflow.

        Args:
            role (str): The role of the message sender.
            content (BaseIOSchema): The content of the message.
        """
        if self.current_turn_id is None:
            self.initialize_turn()

        message = Message(
            role=role,
            content=content,
            turn_id=self.current_turn_id,
        )
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
        Retrieves the chat history, handling both regular and multimodal content.

        Returns:
            List[Dict]: The list of messages in the chat history as dictionaries.
        """
        history = []
        for message in self.history:
            content = message.content
            message_content = content.model_dump()

            images = []
            image_keys = []

            for key, value in message_content.items():
                if isinstance(value, list):
                    for list_item in value:
                        if isinstance(list_item, dict) and list_item.get("media_type", "").startswith("image"):
                            images.extend(value)
                            image_keys.append(key)
                            break

                if isinstance(value, dict) and value.get("media_type", "").startswith("image"):
                    images.append(value)
                    image_keys.append(key)

            if len(images) > 0:
                # For multimodal content, format as a list with text and images
                # delete image keys from model
                images = []
                for key in image_keys:
                    message_content.pop(key)
                    image_content = getattr(content, key)
                    if isinstance(image_content, list):
                        images.extend(image_content)
                    else:
                        images.append(image_content)

                history.append({"role": message.role, "content": [json.dumps(message_content), *images]})
            else:
                # For regular content, serialize to JSON string
                history.append({"role": message.role, "content": json.dumps(content.model_dump(mode="json"))})
        return history

    def copy(self) -> "ChatHistory":
        """
        Creates a copy of the chat history.

        Returns:
            ChatHistory: A copy of the chat history.
        """
        new_history = ChatHistory(max_messages=self.max_messages)
        new_history.load(self.dump())
        new_history.current_turn_id = self.current_turn_id
        return new_history

    def get_current_turn_id(self) -> Optional[str]:
        """
        Returns the current turn ID.

        Returns:
            Optional[str]: The current turn ID, or None if not set.
        """
        return self.current_turn_id

    def delete_turn_id(self, turn_id: int):
        """
        Delete messages from the history by its turn ID.

        Args:
            turn_id (int): The turn ID of the message to delete.

        Returns:
            str: A success message with the deleted turn ID.

        Raises:
            ValueError: If the specified turn ID is not found in the history.
        """
        initial_length = len(self.history)
        self.history = [msg for msg in self.history if msg.turn_id != turn_id]

        if len(self.history) == initial_length:
            raise ValueError(f"Turn ID {turn_id} not found in history.")

        # Update current_turn_id if necessary
        if not len(self.history):
            self.current_turn_id = None
        elif turn_id == self.current_turn_id:
            # Always update to the last message's turn_id
            self.current_turn_id = self.history[-1].turn_id

    def get_message_count(self) -> int:
        """
        Returns the number of messages in the chat history.

        Returns:
            int: The number of messages.
        """
        return len(self.history)

    def dump(self) -> str:
        """
        Serializes the entire ChatHistory instance to a JSON string.

        Returns:
            str: A JSON string representation of the ChatHistory.
        """
        serialized_history = []
        for message in self.history:
            content_class = message.content.__class__
            serialized_message = {
                "role": message.role,
                "content": {
                    "class_name": f"{content_class.__module__}.{content_class.__name__}",
                    "data": message.content.model_dump(),
                },
                "turn_id": message.turn_id,
            }
            serialized_history.append(serialized_message)

        history_data = {
            "history": serialized_history,
            "max_messages": self.max_messages,
            "current_turn_id": self.current_turn_id,
        }
        return json.dumps(history_data)

    def load(self, serialized_data: str) -> None:
        """
        Deserializes a JSON string and loads it into the ChatHistory instance.

        Args:
            serialized_data (str): A JSON string representation of the ChatHistory.

        Raises:
            ValueError: If the serialized data is invalid or cannot be deserialized.
        """
        try:
            history_data = json.loads(serialized_data)
            self.history = []
            self.max_messages = history_data["max_messages"]
            self.current_turn_id = history_data["current_turn_id"]

            for message_data in history_data["history"]:
                content_info = message_data["content"]
                content_class = self._get_class_from_string(content_info["class_name"])
                content_instance = content_class(**content_info["data"])

                message = Message(role=message_data["role"], content=content_instance, turn_id=message_data["turn_id"])
                self.history.append(message)
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError) as e:
            raise ValueError(f"Invalid serialized data: {e}")

    @staticmethod
    def _get_class_from_string(class_string: str) -> Type[BaseIOSchema]:
        """
        Retrieves a class object from its string representation.

        Args:
            class_string (str): The fully qualified class name.

        Returns:
            Type[BaseIOSchema]: The class object.

        Raises:
            AttributeError: If the class cannot be found.
        """
        module_name, class_name = class_string.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)


if __name__ == "__main__":
    import instructor
    from typing import List as TypeList, Dict as TypeDict
    import os

    # Define complex test schemas
    class NestedSchema(BaseIOSchema):
        """A nested schema for testing"""

        nested_field: str = Field(..., description="A nested field")
        nested_int: int = Field(..., description="A nested integer")

    class ComplexInputSchema(BaseIOSchema):
        """Complex Input Schema"""

        text_field: str = Field(..., description="A text field")
        number_field: float = Field(..., description="A number field")
        list_field: TypeList[str] = Field(..., description="A list of strings")
        nested_field: NestedSchema = Field(..., description="A nested schema")

    class ComplexOutputSchema(BaseIOSchema):
        """Complex Output Schema"""

        response_text: str = Field(..., description="A response text")
        calculated_value: int = Field(..., description="A calculated value")
        data_dict: TypeDict[str, NestedSchema] = Field(..., description="A dictionary of nested schemas")

    # Add a new multimodal schema for testing
    class MultimodalSchema(BaseIOSchema):
        """Schema for testing multimodal content"""

        instruction_text: str = Field(..., description="The instruction text")
        images: List[instructor.Image] = Field(..., description="The images to analyze")

    # Create and populate the original history with complex data
    original_history = ChatHistory(max_messages=10)

    # Add a complex input message
    original_history.add_message(
        "user",
        ComplexInputSchema(
            text_field="Hello, this is a complex input",
            number_field=3.14159,
            list_field=["item1", "item2", "item3"],
            nested_field=NestedSchema(nested_field="Nested input", nested_int=42),
        ),
    )

    # Add a complex output message
    original_history.add_message(
        "assistant",
        ComplexOutputSchema(
            response_text="This is a complex response",
            calculated_value=100,
            data_dict={
                "key1": NestedSchema(nested_field="Nested output 1", nested_int=10),
                "key2": NestedSchema(nested_field="Nested output 2", nested_int=20),
            },
        ),
    )

    # Test multimodal functionality if test image exists
    test_image_path = os.path.join("test_images", "test.jpg")
    if os.path.exists(test_image_path):
        # Add a multimodal message
        original_history.add_message(
            "user",
            MultimodalSchema(
                instruction_text="Please analyze this image", images=[instructor.Image.from_path(test_image_path)]
            ),
        )

    # Continue with existing tests...
    dumped_data = original_history.dump()
    print("Dumped data:")
    print(dumped_data)

    # Create a new history and load the dumped data
    loaded_history = ChatHistory()
    loaded_history.load(dumped_data)

    # Print detailed information about the loaded history
    print("\nLoaded history details:")
    for i, message in enumerate(loaded_history.history):
        print(f"\nMessage {i + 1}:")
        print(f"Role: {message.role}")
        print(f"Turn ID: {message.turn_id}")
        print(f"Content type: {type(message.content).__name__}")
        print("Content:")
        for field, value in message.content.model_dump().items():
            print(f"  {field}: {value}")

    # Final verification
    print("\nFinal verification:")
    print(f"Max messages: {loaded_history.max_messages}")
    print(f"Current turn ID: {loaded_history.get_current_turn_id()}")
    print("Last message content:")
    last_message = loaded_history.history[-1]
    print(last_message.content.model_dump())
