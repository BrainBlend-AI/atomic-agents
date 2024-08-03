import pytest
from atomic_agents.lib.components.agent_memory import AgentMemory, Message


@pytest.fixture
def agent_memory():
    return AgentMemory(max_messages=5)


def test_initialization(agent_memory):
    assert agent_memory.history == []
    assert agent_memory.max_messages == 5


def test_add_message(agent_memory):
    agent_memory.add_message("user", "Hello")
    assert len(agent_memory.history) == 1
    assert agent_memory.history[0].role == "user"
    assert agent_memory.history[0].content == "Hello"


def test_add_message_with_tool(agent_memory):
    tool_message = {
        "id": "weather_1",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"location": "New York"}'},
    }
    agent_memory.add_message("assistant", "Checking weather", tool_message=tool_message)
    assert len(agent_memory.history) == 1
    assert agent_memory.history[0].role == "assistant"
    assert agent_memory.history[0].content == "Checking weather"
    assert agent_memory.history[0].tool_calls == [tool_message]
    assert agent_memory.history[0].tool_call_id == "weather_1"


def test_add_tool_response(agent_memory):
    agent_memory.add_message("tool", "Weather is sunny", tool_id="weather_1")
    assert len(agent_memory.history) == 1
    assert agent_memory.history[0].role == "tool"
    assert agent_memory.history[0].content == "Weather is sunny"
    assert agent_memory.history[0].tool_call_id == "weather_1"


def test_manage_overflow(agent_memory):
    for i in range(7):
        agent_memory.add_message("user", f"Message {i}")
    assert len(agent_memory.history) == 5
    assert agent_memory.history[0].content == "Message 2"
    assert agent_memory.history[-1].content == "Message 6"


def test_get_history(agent_memory):
    agent_memory.add_message("user", "Hello")
    agent_memory.add_message("assistant", "Hi there")
    history = agent_memory.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there"
    assert "turn_id" not in history[0]
    assert "turn_id" not in history[1]


def test_get_current_turn_id(agent_memory):
    # Initially, current_turn_id should be None
    assert agent_memory.get_current_turn_id() is None

    # After adding a message, current_turn_id should be set
    agent_memory.add_message("user", "Hello")
    first_turn_id = agent_memory.get_current_turn_id()
    assert first_turn_id is not None
    assert isinstance(first_turn_id, str)

    # Adding another message should not change the turn_id
    agent_memory.add_message("assistant", "Hi there")
    assert agent_memory.get_current_turn_id() == first_turn_id

    # Initializing a new turn should change the turn_id
    agent_memory.initialize_turn()
    second_turn_id = agent_memory.get_current_turn_id()
    assert second_turn_id != first_turn_id


def test_dump_and_load():
    original_memory = AgentMemory(max_messages=3)
    original_memory.add_message("user", "Hello")
    original_memory.add_message("assistant", "Hi there")

    dumped_data = original_memory.dump()

    new_memory = AgentMemory(max_messages=3)
    new_memory.load(dumped_data)

    assert len(new_memory.history) == 2
    assert new_memory.history[0].role == "user"
    assert new_memory.history[0].content == "Hello"
    assert new_memory.history[1].role == "assistant"
    assert new_memory.history[1].content == "Hi there"


def test_copy(agent_memory):
    agent_memory.add_message("user", "Hello")
    copied_memory = agent_memory.copy()

    assert len(copied_memory.history) == 1
    assert copied_memory.history[0].role == "user"
    assert copied_memory.history[0].content == "Hello"
    assert copied_memory.max_messages == agent_memory.max_messages

    agent_memory.add_message("assistant", "Hi there")
    assert len(agent_memory.history) == 2
    assert len(copied_memory.history) == 1


def test_get_message_count(agent_memory):
    assert agent_memory.get_message_count() == 0
    agent_memory.add_message("user", "Hello")
    agent_memory.add_message("assistant", "Hi there")
    assert agent_memory.get_message_count() == 2


def test_load_with_invalid_data():
    memory = AgentMemory()
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


def test_add_message_with_dict_content(agent_memory):
    dict_content = {"text": "Hello", "confidence": 0.95}
    agent_memory.add_message("assistant", dict_content)
    assert len(agent_memory.history) == 1
    assert agent_memory.history[0].role == "assistant"
    assert agent_memory.history[0].content == dict_content


if __name__ == "__main__":
    pytest.main()
