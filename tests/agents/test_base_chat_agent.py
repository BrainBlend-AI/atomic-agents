import unittest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel
import instructor
from atomic_agents.agents.base_chat_agent import (
    BaseChatAgent,
    BaseChatAgentConfig,
    BaseChatAgentInputSchema,
    BaseChatAgentOutputSchema,
    SystemPromptGenerator,
    ChatMemory,
    SystemPromptContextProviderBase
)
from atomic_agents.lib.components.system_prompt_generator import SystemPromptInfo

class TestBaseChatAgent(unittest.TestCase):
    def setUp(self):
        # Mock the Instructor class
        self.mock_instructor = Mock(spec=instructor.Instructor)
        self.mock_instructor.chat.completions.create = Mock()
        
        # Mock ChatMemory
        self.mock_memory = Mock(spec=ChatMemory)
        self.mock_memory.get_history.return_value = []
        self.mock_memory.add_message = Mock()
        self.mock_memory.copy = Mock(return_value=Mock(spec=ChatMemory))
        
        # Mock SystemPromptGenerator
        self.mock_system_prompt_generator = Mock(spec=SystemPromptGenerator)
        self.mock_system_prompt_generator.generate_prompt.return_value = "Mocked system prompt"
        self.mock_system_prompt_generator.system_prompt_info = Mock(spec=SystemPromptInfo)
        self.mock_system_prompt_generator.system_prompt_info.context_providers = {}
        
        self.config = BaseChatAgentConfig(
            client=self.mock_instructor,
            model="gpt-3.5-turbo",
            memory=self.mock_memory,
            system_prompt_generator=self.mock_system_prompt_generator
        )
        
        self.agent = BaseChatAgent(self.config)

    def test_initialization(self):
        self.assertEqual(self.agent.client, self.mock_instructor)
        self.assertEqual(self.agent.model, "gpt-3.5-turbo")
        self.assertEqual(self.agent.memory, self.mock_memory)
        self.assertEqual(self.agent.system_prompt_generator, self.mock_system_prompt_generator)
        self.assertEqual(self.agent.input_schema, BaseChatAgentInputSchema)
        self.assertEqual(self.agent.output_schema, BaseChatAgentOutputSchema)

    def test_reset_memory(self):
        initial_memory = self.agent.initial_memory
        self.agent.reset_memory()
        self.assertNotEqual(self.agent.memory, initial_memory)
        self.mock_memory.copy.assert_called_once()

    def test_get_response(self):
        self.mock_memory.get_history.return_value = [{'role': 'user', 'content': 'Hello'}]
        self.mock_system_prompt_generator.generate_prompt.return_value = "System prompt"
        
        mock_response = Mock(spec=BaseChatAgentOutputSchema)
        self.mock_instructor.chat.completions.create.return_value = mock_response
        
        response = self.agent.get_response()
        
        self.assertEqual(response, mock_response)
        
        self.mock_instructor.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {'role': 'system', 'content': 'System prompt'},
                {'role': 'user', 'content': 'Hello'}
            ],
            response_model=BaseChatAgentOutputSchema
        )

    def test_run(self):
        mock_input = BaseChatAgentInputSchema(chat_message="Test input")
        mock_output = BaseChatAgentOutputSchema(chat_message="Test output")
        
        self.agent._init_run = Mock()
        self.agent._pre_run = Mock()
        self.agent._post_run = Mock()
        self.agent.get_response = Mock(return_value=mock_output)
        
        result = self.agent.run(mock_input)
        
        self.assertEqual(result, mock_output)
        self.agent._init_run.assert_called_once_with(mock_input)
        self.agent._pre_run.assert_called_once()
        self.agent.get_response.assert_called_once()
        self.agent._post_run.assert_called_once_with(mock_output)

    def test_get_context_provider(self):
        mock_provider = Mock(spec=SystemPromptContextProviderBase)
        self.mock_system_prompt_generator.system_prompt_info.context_providers = {
            'test_provider': mock_provider
        }
        
        result = self.agent.get_context_provider('test_provider')
        self.assertEqual(result, mock_provider)
        
        with self.assertRaises(KeyError):
            self.agent.get_context_provider('non_existent_provider')

    def test_register_context_provider(self):
        mock_provider = Mock(spec=SystemPromptContextProviderBase)
        self.agent.register_context_provider('new_provider', mock_provider)
        
        self.assertIn('new_provider', self.mock_system_prompt_generator.system_prompt_info.context_providers)
        self.assertEqual(
            self.mock_system_prompt_generator.system_prompt_info.context_providers['new_provider'],
            mock_provider
        )

    def test_unregister_context_provider(self):
        mock_provider = Mock(spec=SystemPromptContextProviderBase)
        self.mock_system_prompt_generator.system_prompt_info.context_providers = {
            'test_provider': mock_provider
        }
        
        self.agent.unregister_context_provider('test_provider')
        self.assertNotIn('test_provider', self.mock_system_prompt_generator.system_prompt_info.context_providers)
        
        with self.assertRaises(KeyError):
            self.agent.unregister_context_provider('non_existent_provider')

    def test_custom_input_output_schemas(self):
        class CustomInputSchema(BaseModel):
            custom_field: str

        class CustomOutputSchema(BaseModel):
            result: str

        custom_config = BaseChatAgentConfig(
            client=self.mock_instructor,
            model="gpt-3.5-turbo",
            input_schema=CustomInputSchema,
            output_schema=CustomOutputSchema
        )
        
        custom_agent = BaseChatAgent(custom_config)
        
        self.assertEqual(custom_agent.input_schema, CustomInputSchema)
        self.assertEqual(custom_agent.output_schema, CustomOutputSchema)

if __name__ == '__main__':
    unittest.main()
