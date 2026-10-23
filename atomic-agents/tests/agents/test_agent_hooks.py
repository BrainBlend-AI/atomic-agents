import instructor
import pytest
from unittest.mock import Mock

from atomic_agents import AgentConfig, AtomicAgent


@pytest.mark.parametrize("event", [None, "completion:kwargs"])
def test_clear_hooks_preserves_foreign_handlers(event):
    client = instructor.Instructor(client=Mock(), create=Mock())
    agent = AtomicAgent(AgentConfig(client=client))
    foreign = Mock()
    owned = Mock()
    other_owned = Mock()
    client.on("completion:kwargs", foreign)
    agent.register_hook("completion:kwargs", owned)
    agent.register_hook("completion:response", other_owned)

    agent.clear_hooks(event)
    client.hooks.emit_completion_arguments(model="test-model")
    client.hooks.emit_completion_response(Mock())

    foreign.assert_called_once_with(model="test-model")
    owned.assert_not_called()
    assert other_owned.call_count == (0 if event is None else 1)
    assert agent._hook_handlers.get("completion:kwargs", []) == []
