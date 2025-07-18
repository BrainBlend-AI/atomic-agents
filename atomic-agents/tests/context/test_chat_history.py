from enum import Enum

import pytest
import json
from typing import List, Dict
from pydantic import Field
from atomic_agents.context import ChatHistory, Message
from atomic_agents import BaseIOSchema
import instructor


class InputSchema(BaseIOSchema):
    """Test Input Schema"""

    test_field: str = Field(..., description="A test field")


class MockOutputSchema(BaseIOSchema):
    """Test Output Schema"""

    test_field: str = Field(..., description="A test field")


class MockNestedSchema(BaseIOSchema):
    """Test Nested Schema"""

    nested_field: str = Field(..., description="A nested field")
    nested_int: int = Field(..., description="A nested integer")


class MockComplexInputSchema(BaseIOSchema):
    """Test Complex Input Schema"""

    text_field: str = Field(..., description="A text field")
    number_field: float = Field(..., description="A number field")
    list_field: List[str] = Field(..., description="A list of strings")
    nested_field: MockNestedSchema = Field(..., description="A nested schema")


class MockComplexOutputSchema(BaseIOSchema):
    """Test Complex Output Schema"""

    response_text: str = Field(..., description="A response text")
    calculated_value: int = Field(..., description="A calculated value")
    data_dict: Dict[str, MockNestedSchema] = Field(..., description="A dictionary of nested schemas")


class MockMultimodalSchema(BaseIOSchema):
    """Test schema for multimodal content"""

    instruction_text: str = Field(..., description="The instruction text")
    images: List[instructor.Image] = Field(..., description="The images to analyze")
    pdfs: List[instructor.multimodal.PDF] = Field(..., description="The PDFs to analyze")
    audio: instructor.multimodal.Audio = Field(..., description="The audio to analyze")


class ColorEnum(str, Enum):
    BLUE = "blue"
    RED = "red"


class MockEnumSchema(BaseIOSchema):
    """Test Input Schema with Enum."""

    color: ColorEnum = Field(..., description="Some color.")


@pytest.fixture
def history():
    return ChatHistory(max_messages=5)


def test_initialization(history):
    assert history.history == []
    assert history.max_messages == 5
    assert history.current_turn_id is None


def test_initialize_turn(history):
    history.initialize_turn()
    assert history.current_turn_id is not None


def test_add_message(history):
    history.add_message("user", InputSchema(test_field="Hello"))
    assert len(history.history) == 1
    assert history.history[0].role == "user"
    assert isinstance(history.history[0].content, InputSchema)
    assert history.history[0].turn_id is not None


def test_manage_overflow(history):
    for i in range(7):
        history.add_message("user", InputSchema(test_field=f"Message {i}"))
    assert len(history.history) == 5
    assert history.history[0].content.test_field == "Message 2"


def test_get_history(history):
    """
    Ensure non-ASCII characters are serialized without Unicode escaping, because
    it can cause issue with some OpenAI models like GPT-4.1.

    Reference ticket: https://github.com/BrainBlend-AI/atomic-agents/issues/138.
    """
    history.add_message("user", InputSchema(test_field="Hello"))
    history.add_message("assistant", MockOutputSchema(test_field="Hi there"))
    history = history.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert json.loads(history[0]["content"][0]) == {"test_field": "Hello"}
    assert json.loads(history[1]["content"][0]) == {"test_field": "Hi there"}


def test_get_history_allow_unicode(history):
    history.add_message("user", InputSchema(test_field="àéèï"))
    history.add_message("assistant", MockOutputSchema(test_field="â"))
    history = history.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"][0] == '{"test_field":"àéèï"}'
    assert history[1]["content"][0] == '{"test_field":"â"}'
    assert json.loads(history[0]["content"][0]) == {"test_field": "àéèï"}
    assert json.loads(history[1]["content"][0]) == {"test_field": "â"}


def test_copy(history):
    history.add_message("user", InputSchema(test_field="Hello"))
    copied_history = history.copy()
    assert copied_history.max_messages == history.max_messages
    assert copied_history.current_turn_id == history.current_turn_id
    assert len(copied_history.history) == len(history.history)
    assert copied_history.history[0].role == history.history[0].role
    assert copied_history.history[0].content.test_field == history.history[0].content.test_field


def test_get_current_turn_id(history):
    assert history.get_current_turn_id() is None
    history.initialize_turn()
    assert history.get_current_turn_id() is not None


def test_get_message_count(history):
    assert history.get_message_count() == 0
    history.add_message("user", InputSchema(test_field="Hello"))
    assert history.get_message_count() == 1


def test_dump_and_load(history):
    history.add_message(
        "user",
        MockComplexInputSchema(
            text_field="Hello",
            number_field=3.14,
            list_field=["item1", "item2"],
            nested_field=MockNestedSchema(nested_field="Nested", nested_int=42),
        ),
    )
    history.add_message(
        "assistant",
        MockComplexOutputSchema(
            response_text="Hi there",
            calculated_value=100,
            data_dict={"key": MockNestedSchema(nested_field="Nested Output", nested_int=10)},
        ),
    )

    dumped_data = history.dump()
    new_history = ChatHistory()
    new_history.load(dumped_data)

    assert new_history.max_messages == history.max_messages
    assert new_history.current_turn_id == history.current_turn_id
    assert len(new_history.history) == len(history.history)
    assert isinstance(new_history.history[0].content, MockComplexInputSchema)
    assert isinstance(new_history.history[1].content, MockComplexOutputSchema)
    assert new_history.history[0].content.text_field == "Hello"
    assert new_history.history[1].content.response_text == "Hi there"


def test_dump_and_load_multimodal_data(history):
    import os

    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    test_image = instructor.Image.from_path(path=os.path.join(base_path, "files/image_sample.jpg"))
    test_pdf = instructor.multimodal.PDF.from_path(path=os.path.join(base_path, "files/pdf_sample.pdf"))
    test_audio = instructor.multimodal.Audio.from_path(path=os.path.join(base_path, "files/audio_sample.mp3"))

    # multimodal message
    history.add_message(
        role="user",
        content=MockMultimodalSchema(
            instruction_text="Analyze this image", images=[test_image], pdfs=[test_pdf], audio=test_audio
        ),
    )

    dumped_data = history.dump()
    new_history = ChatHistory()
    new_history.load(dumped_data)

    assert new_history.max_messages == history.max_messages
    assert new_history.current_turn_id == history.current_turn_id
    assert len(new_history.history) == len(history.history)
    assert isinstance(new_history.history[0].content, MockMultimodalSchema)
    assert new_history.history[0].content.instruction_text == history.history[0].content.instruction_text
    assert new_history.history[0].content.images == history.history[0].content.images
    assert new_history.history[0].content.pdfs == history.history[0].content.pdfs
    assert new_history.history[0].content.audio == history.history[0].content.audio


def test_dump_and_load_with_enum(history):
    """Test that get_history works with Enum."""

    history.add_message(
        "user",
        MockEnumSchema(
            color=ColorEnum.RED,
        ),
    )

    dumped_data = history.dump()
    new_history = ChatHistory()
    new_history.load(dumped_data)

    assert new_history.max_messages == history.max_messages
    assert new_history.current_turn_id == history.current_turn_id
    assert len(new_history.history) == len(history.history)


def test_load_invalid_data(history):
    with pytest.raises(ValueError):
        history.load("invalid json")


def test_get_class_from_string():
    class_string = "tests.context.test_chat_history.InputSchema"
    cls = ChatHistory._get_class_from_string(class_string)
    assert cls.__name__ == InputSchema.__name__
    assert cls.__module__.endswith("test_chat_history")
    assert issubclass(cls, BaseIOSchema)


def test_get_class_from_string_invalid():
    with pytest.raises((ImportError, AttributeError)):
        ChatHistory._get_class_from_string("invalid.module.Class")


def test_message_model():
    message = Message(role="user", content=InputSchema(test_field="Test"), turn_id="123")
    assert message.role == "user"
    assert isinstance(message.content, InputSchema)
    assert message.turn_id == "123"


def test_complex_scenario(history):
    # Add complex input
    history.add_message(
        "user",
        MockComplexInputSchema(
            text_field="Complex input",
            number_field=2.718,
            list_field=["a", "b", "c"],
            nested_field=MockNestedSchema(nested_field="Nested input", nested_int=99),
        ),
    )

    # Add complex output
    history.add_message(
        "assistant",
        MockComplexOutputSchema(
            response_text="Complex output",
            calculated_value=200,
            data_dict={
                "key1": MockNestedSchema(nested_field="Nested output 1", nested_int=10),
                "key2": MockNestedSchema(nested_field="Nested output 2", nested_int=20),
            },
        ),
    )

    # Dump and load
    dumped_data = history.dump()
    new_history = ChatHistory()
    new_history.load(dumped_data)

    # Verify loaded data
    assert len(new_history.history) == 2
    assert isinstance(new_history.history[0].content, MockComplexInputSchema)
    assert isinstance(new_history.history[1].content, MockComplexOutputSchema)
    assert new_history.history[0].content.text_field == "Complex input"
    assert new_history.history[0].content.nested_field.nested_int == 99
    assert new_history.history[1].content.response_text == "Complex output"
    assert new_history.history[1].content.data_dict["key1"].nested_field == "Nested output 1"

    # Add a new message to the loaded history
    new_history.add_message("user", InputSchema(test_field="New message"))
    assert len(new_history.history) == 3
    assert new_history.history[2].content.test_field == "New message"


def test_history_with_no_max_messages():
    unlimited_history = ChatHistory()
    for i in range(100):
        unlimited_history.add_message("user", InputSchema(test_field=f"Message {i}"))
    assert len(unlimited_history.history) == 100


def test_history_with_zero_max_messages():
    zero_max_history = ChatHistory(max_messages=0)
    for i in range(10):
        zero_max_history.add_message("user", InputSchema(test_field=f"Message {i}"))
    assert len(zero_max_history.history) == 0


def test_history_turn_consistency():
    history = ChatHistory()
    history.initialize_turn()
    turn_id = history.get_current_turn_id()
    history.add_message("user", InputSchema(test_field="Hello"))
    history.add_message("assistant", MockOutputSchema(test_field="Hi"))
    assert history.history[0].turn_id == turn_id
    assert history.history[1].turn_id == turn_id

    history.initialize_turn()
    new_turn_id = history.get_current_turn_id()
    assert new_turn_id != turn_id
    history.add_message("user", InputSchema(test_field="Next turn"))
    assert history.history[2].turn_id == new_turn_id


def test_get_history_nested_model(history):
    """Test that get_history works with nested models."""
    # Add complex input
    history.add_message(
        "user",
        MockComplexInputSchema(
            text_field="Complex input",
            number_field=2.718,
            list_field=["a", "b", "c"],
            nested_field=MockNestedSchema(nested_field="Nested input", nested_int=99),
        ),
    )

    # Add complex output
    history.add_message(
        "assistant",
        MockComplexOutputSchema(
            response_text="Complex output",
            calculated_value=200,
            data_dict={
                "key1": MockNestedSchema(nested_field="Nested output 1", nested_int=10),
                "key2": MockNestedSchema(nested_field="Nested output 2", nested_int=20),
            },
        ),
    )

    # Get history and verify the format
    history = history.get_history()

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    assert history[0]["content"][0] == '{"text_field":"Complex input"}'
    assert history[1]["content"][0] == '{"response_text":"Complex output"}'


def test_chat_history_delete_turn_id(history):
    mock_input = InputSchema(test_field="Test input")
    mock_output = InputSchema(test_field="Test output")

    history = ChatHistory()
    initial_turn_id = "123-456"
    history.current_turn_id = initial_turn_id

    # Add a message with a specific turn ID
    history.add_message(
        "user",
        mock_input,
    )
    history.history[-1].turn_id = initial_turn_id

    # Add another message with a different turn ID
    other_turn_id = "789-012"
    history.add_message(
        "assistant",
        mock_output,
    )
    history.history[-1].turn_id = other_turn_id

    # Act & Assert: Delete the message with initial_turn_id and verify
    history.delete_turn_id(initial_turn_id)

    # The remaining message in history should have the other_turn_id
    assert len(history.history) == 1
    assert history.history[0].turn_id == other_turn_id

    # If we delete the last message, current_turn_id should become None
    history.delete_turn_id(other_turn_id)
    assert history.current_turn_id is None
    assert len(history.history) == 0

    # Assert: Trying to delete a non-existing turn ID should raise a ValueError
    with pytest.raises(ValueError, match="Turn ID non-existent-id not found in history."):
        history.delete_turn_id("non-existent-id")


def test_get_history_with_multimodal_content(history):
    """Test that get_history correctly handles multimodal content"""
    # Create mock multimodal objects
    mock_image = instructor.Image(source="test_url", media_type="image/jpeg", detail="low")
    mock_pdf = instructor.multimodal.PDF(source="test_pdf_url", media_type="application/pdf", detail="low")
    mock_audio = instructor.multimodal.Audio(source="test_audio_url", media_type="audio/mp3", detail="low")

    # Add a multimodal message
    history.add_message(
        "user",
        MockMultimodalSchema(instruction_text="Analyze this image", images=[mock_image], pdfs=[mock_pdf], audio=mock_audio),
    )

    # Get history and verify format
    history = history.get_history()
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert isinstance(history[0]["content"], list)
    assert json.loads(history[0]["content"][0]) == {"instruction_text": "Analyze this image"}
    assert history[0]["content"][1] == mock_image


def test_get_history_with_multiple_images_multimodal_content(history):
    """Test that get_history correctly handles multimodal content"""

    class MockMultimodalSchemaArbitraryKeys(BaseIOSchema):
        """Test schema for multimodal content"""

        instruction_text: str = Field(..., description="The instruction text")
        some_key_for_images: List[instructor.Image] = Field(..., description="The images to analyze")
        some_other_key_with_image: instructor.Image = Field(..., description="The images to analyze")

    # Create a mock image
    mock_image = instructor.Image(source="test_url", media_type="image/jpeg", detail="low")
    mock_image_2 = instructor.Image(source="test_url_2", media_type="image/jpeg", detail="low")
    mock_image_3 = instructor.Image(source="test_url_3", media_type="image/jpeg", detail="low")

    # Add a multimodal message
    history.add_message(
        "user",
        MockMultimodalSchemaArbitraryKeys(
            instruction_text="Analyze this image",
            some_other_key_with_image=mock_image,
            some_key_for_images=[mock_image_2, mock_image_3],
        ),
    )

    # Get history and verify format
    history = history.get_history()
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert isinstance(history[0]["content"], list)
    assert json.loads(history[0]["content"][0]) == {"instruction_text": "Analyze this image"}
    assert mock_image in history[0]["content"]
    assert mock_image_2 in history[0]["content"]
    assert mock_image_3 in history[0]["content"]
