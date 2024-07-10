import pytest
from unittest.mock import Mock, call
from pydantic import BaseModel
import instructor
from atomic_agents.agents.base_chat_agent import (
    BaseAgentIO,
    BaseChatAgent,
    BaseChatAgentConfig,
    BaseChatAgentInputSchema,
    BaseChatAgentOutputSchema,
    SystemPromptGenerator,
    AgentMemory,
    SystemPromptContextProviderBase
)
from atomic_agents.lib.components.system_prompt_generator import SystemPromptInfo

@pytest.fixture
def mock_instructor():
    mock = Mock(spec=instructor.Instructor)
    mock.chat.completions.create = Mock()
    return mock

@pytest.fixture
def mock_memory():
    mock = Mock(spec=AgentMemory)
    mock.get_history.return_value = []
    mock.add_message = Mock()
    mock.copy = Mock(return_value=Mock(spec=AgentMemory))
    return mock

@pytest.fixture
def mock_system_prompt_generator():
    mock = Mock(spec=SystemPromptGenerator)
    mock.generate_prompt.return_value = "Mocked system prompt"
    mock.system_prompt_info = Mock(spec=SystemPromptInfo)
    mock.system_prompt_info.context_providers = {}
    return mock

@pytest.fixture
def agent_config(mock_instructor, mock_memory, mock_system_prompt_generator):
    return BaseChatAgentConfig(
        client=mock_instructor,
        model="gpt-3.5-turbo",
        memory=mock_memory,
        system_prompt_generator=mock_system_prompt_generator
    )

@pytest.fixture
def agent(agent_config):
    return BaseChatAgent(agent_config)

def test_initialization(agent, mock_instructor, mock_memory, mock_system_prompt_generator):
    assert agent.client == mock_instructor
    assert agent.model == "gpt-3.5-turbo"
    assert agent.memory == mock_memory
    assert agent.system_prompt_generator == mock_system_prompt_generator
    assert agent.input_schema == BaseChatAgentInputSchema
    assert agent.output_schema == BaseChatAgentOutputSchema

def test_reset_memory(agent, mock_memory):
    initial_memory = agent.initial_memory
    agent.reset_memory()
    assert agent.memory != initial_memory
    mock_memory.copy.assert_called_once()

def test_get_response(agent, mock_instructor, mock_memory, mock_system_prompt_generator):
    mock_memory.get_history.return_value = [{'role': 'user', 'content': 'Hello'}]
    mock_system_prompt_generator.generate_prompt.return_value = "System prompt"
    
    mock_response = Mock(spec=BaseChatAgentOutputSchema)
    mock_instructor.chat.completions.create.return_value = mock_response
    
    response = agent.get_response()
    
    assert response == mock_response
    
    mock_instructor.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[
            {'role': 'system', 'content': 'System prompt'},
            {'role': 'user', 'content': 'Hello'}
        ],
        response_model=BaseChatAgentOutputSchema
    )

def test_run(agent):
    mock_input = BaseChatAgentInputSchema(chat_message="Test input")
    mock_output = BaseChatAgentOutputSchema(chat_message="Test output")
    
    agent._init_run = Mock()
    agent._pre_run = Mock()
    agent._post_run = Mock()
    agent.get_response = Mock(return_value=mock_output)
    
    result = agent.run(mock_input)
    
    assert result == mock_output
    agent._init_run.assert_called_once_with(mock_input)
    agent._pre_run.assert_called_once()
    agent.get_response.assert_called_once()
    agent._post_run.assert_called_once_with(mock_output)

def test_get_context_provider(agent, mock_system_prompt_generator):
    mock_provider = Mock(spec=SystemPromptContextProviderBase)
    mock_system_prompt_generator.system_prompt_info.context_providers = {
        'test_provider': mock_provider
    }
    
    result = agent.get_context_provider('test_provider')
    assert result == mock_provider
    
    with pytest.raises(KeyError):
        agent.get_context_provider('non_existent_provider')

def test_register_context_provider(agent, mock_system_prompt_generator):
    mock_provider = Mock(spec=SystemPromptContextProviderBase)
    agent.register_context_provider('new_provider', mock_provider)
    
    assert 'new_provider' in mock_system_prompt_generator.system_prompt_info.context_providers
    assert mock_system_prompt_generator.system_prompt_info.context_providers['new_provider'] == mock_provider

def test_unregister_context_provider(agent, mock_system_prompt_generator):
    mock_provider = Mock(spec=SystemPromptContextProviderBase)
    mock_system_prompt_generator.system_prompt_info.context_providers = {
        'test_provider': mock_provider
    }
    
    agent.unregister_context_provider('test_provider')
    assert 'test_provider' not in mock_system_prompt_generator.system_prompt_info.context_providers
    
    with pytest.raises(KeyError):
        agent.unregister_context_provider('non_existent_provider')

def test_custom_input_output_schemas(mock_instructor):
    class CustomInputSchema(BaseModel):
        custom_field: str

    class CustomOutputSchema(BaseModel):
        result: str

    custom_config = BaseChatAgentConfig(
        client=mock_instructor,
        model="gpt-3.5-turbo",
        input_schema=CustomInputSchema,
        output_schema=CustomOutputSchema
    )
    
    custom_agent = BaseChatAgent(custom_config)
    
    assert custom_agent.input_schema == CustomInputSchema
    assert custom_agent.output_schema == CustomOutputSchema
    

def test_base_agent_io_str_and_rich():
    class TestIO(BaseAgentIO):
        field: str

    test_io = TestIO(field="test")
    assert str(test_io) == '{"field":"test"}'
    assert test_io.__rich__() is not None  # Just check if it returns something, as we can't easily compare Rich objects

def test_base_chat_agent_input_output_schema_config():
    assert BaseChatAgentInputSchema.Config.title == "BaseChatAgentInputSchema"
    assert "description" in BaseChatAgentInputSchema.Config.json_schema_extra
    
    assert BaseChatAgentOutputSchema.Config.title == "BaseChatAgentOutputSchema"
    assert "description" in BaseChatAgentOutputSchema.Config.json_schema_extra

def test_init_run(agent, mock_memory):
    input_schema = BaseChatAgentInputSchema(chat_message="Test message")
    agent._init_run(input_schema)
    assert agent.current_user_input == input_schema
    mock_memory.add_message.assert_called_once_with("user", str(input_schema))

def test_pre_run(agent):
    # This test just ensures that _pre_run can be called without errors
    agent._pre_run()

def test_post_run(agent, mock_memory):
    output_schema = BaseChatAgentOutputSchema(chat_message="Test response")
    agent._post_run(output_schema)
    mock_memory.add_message.assert_called_once_with("assistant", str(output_schema))

# Update the existing test_run function to use the actual methods instead of mocks
def test_run(agent, mock_memory):
    mock_input = BaseChatAgentInputSchema(chat_message="Test input")
    mock_output = BaseChatAgentOutputSchema(chat_message="Test output")
    
    agent.get_response = Mock(return_value=mock_output)
    
    result = agent.run(mock_input)
    
    assert result == mock_output
    assert agent.current_user_input == mock_input
    mock_memory.add_message.assert_has_calls([
        call("user", str(mock_input)),
        call("assistant", str(mock_output))
    ])
    
if __name__ == '__main__':
    pytest.main()