import pytest
from atomic_agents.lib.components.chat_memory import ChatMemory, Message

@pytest.fixture
def chat_memory():
    return ChatMemory(max_messages=5)

def test_initialization(chat_memory):
    assert chat_memory.history == []
    assert chat_memory.max_messages == 5

def test_add_message(chat_memory):
    chat_memory.add_message("user", "Hello")
    assert len(chat_memory.history) == 1
    assert chat_memory.history[0].role == "user"
    assert chat_memory.history[0].content == "Hello"

def test_add_message_with_tool(chat_memory):
    tool_message = {
        "id": "weather_1",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"location": "New York"}'}
    }
    chat_memory.add_message("assistant", "Checking weather", tool_message=tool_message)
    assert len(chat_memory.history) == 1
    assert chat_memory.history[0].role == "assistant"
    assert chat_memory.history[0].content == "Checking weather"
    assert chat_memory.history[0].tool_calls == [tool_message]
    assert chat_memory.history[0].tool_call_id == "weather_1"

def test_add_tool_response(chat_memory):
    chat_memory.add_message("tool", "Weather is sunny", tool_id="weather_1")
    assert len(chat_memory.history) == 1
    assert chat_memory.history[0].role == "tool"
    assert chat_memory.history[0].content == "Weather is sunny"
    assert chat_memory.history[0].tool_call_id == "weather_1"

def test_manage_overflow(chat_memory):
    for i in range(7):
        chat_memory.add_message("user", f"Message {i}")
    assert len(chat_memory.history) == 5
    assert chat_memory.history[0].content == "Message 2"
    assert chat_memory.history[-1].content == "Message 6"

def test_get_history(chat_memory):
    chat_memory.add_message("user", "Hello")
    chat_memory.add_message("assistant", "Hi there")
    history = chat_memory.get_history()
    assert len(history) == 2
    assert isinstance(history[0], Message)
    assert history[0].role == "user"
    assert history[1].role == "assistant"

def test_dump_and_load():
    original_memory = ChatMemory(max_messages=3)
    original_memory.add_message("user", "Hello")
    original_memory.add_message("assistant", "Hi there")
    
    dumped_data = original_memory.dump()
    
    new_memory = ChatMemory(max_messages=3)
    new_memory.load(dumped_data)
    
    assert len(new_memory.history) == 2
    assert new_memory.history[0].role == "user"
    assert new_memory.history[0].content == "Hello"
    assert new_memory.history[1].role == "assistant"
    assert new_memory.history[1].content == "Hi there"

def test_copy(chat_memory):
    chat_memory.add_message("user", "Hello")
    copied_memory = chat_memory.copy()
    
    assert len(copied_memory.history) == 1
    assert copied_memory.history[0].role == "user"
    assert copied_memory.history[0].content == "Hello"
    assert copied_memory.max_messages == chat_memory.max_messages
    
    chat_memory.add_message("assistant", "Hi there")
    assert len(chat_memory.history) == 2
    assert len(copied_memory.history) == 1

def test_get_message_count(chat_memory):
    assert chat_memory.get_message_count() == 0
    chat_memory.add_message("user", "Hello")
    chat_memory.add_message("assistant", "Hi there")
    assert chat_memory.get_message_count() == 2

def test_load_with_invalid_data():
    memory = ChatMemory()
    invalid_data = [
        {"role": "user", "content": "Valid message"},
        {"role": "invalid_role", "content": "Invalid role"},
        {"role": "user", "invalid_field": "Missing content"},
    ]
    memory.load(invalid_data)
    assert len(memory.history) == 2
    assert memory.history[0].role == "user"
    assert memory.history[0].content == "Valid message"
    assert memory.history[1].role == "invalid_role"
    assert memory.history[1].content == "Invalid role"

def test_add_message_with_dict_content(chat_memory):
    dict_content = {"text": "Hello", "confidence": 0.95}
    chat_memory.add_message("assistant", dict_content)
    assert len(chat_memory.history) == 1
    assert chat_memory.history[0].role == "assistant"
    assert chat_memory.history[0].content == dict_content

if __name__ == "__main__":
    pytest.main()
