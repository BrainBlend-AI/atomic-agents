import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptContextProviderBase,
    SystemPromptInfo,
    SystemPromptGenerator,
)

class TestSystemPromptContextProviderBase(unittest.TestCase):
    """Tests for the SystemPromptContextProviderBase class."""

    def test_abstract_base_class(self):
        """Test that SystemPromptContextProviderBase cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            SystemPromptContextProviderBase("Test")

    def test_repr(self):
        """Test the __repr__ method of a concrete subclass."""
        class ConcreteProvider(SystemPromptContextProviderBase):
            def get_info(self):
                return "Test Info"

        provider = ConcreteProvider("Test")
        self.assertEqual(repr(provider), "Test Info")

class TestSystemPromptInfo(unittest.TestCase):
    """Tests for the SystemPromptInfo class."""

    def test_default_values(self):
        """Test the default values of SystemPromptInfo."""
        info = SystemPromptInfo(background=["Test background"])
        self.assertEqual(info.background, ["Test background"])
        self.assertEqual(info.steps, [])
        self.assertEqual(info.output_instructions, [])
        self.assertEqual(info.context_providers, {})

    def test_custom_values(self):
        """Test custom values for SystemPromptInfo."""
        info = SystemPromptInfo(
            background=["Test background"],
            steps=["Step 1", "Step 2"],
            output_instructions=["Instruction 1"],
            context_providers={"test": None}
        )
        self.assertEqual(info.background, ["Test background"])
        self.assertEqual(info.steps, ["Step 1", "Step 2"])
        self.assertEqual(info.output_instructions, ["Instruction 1"])
        self.assertEqual(info.context_providers, {"test": None})

class SystemPromptGeneratorTestBase(unittest.TestCase):
    """Base class for SystemPromptGenerator tests."""

    def setUp(self):
        self.default_generator = SystemPromptGenerator()

        class MockContextProvider(SystemPromptContextProviderBase):
            def get_info(self):
                return "Mock info"

        class CurrentDateProvider(SystemPromptContextProviderBase):
            def __init__(self, title, format: str = '%Y-%m-%d %H:%M:%S'):
                super().__init__(title)
                self.format = format

            def get_current_datetime(self):
                return datetime.now()

            def get_info(self) -> str:
                current_datetime = self.get_current_datetime()
                return f'The current date, in the format "{self.format}", is {current_datetime.strftime(self.format)}'

        class LoremIpsumProvider(SystemPromptContextProviderBase):
            def get_info(self) -> str:
                return (
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
                )

        self.current_date_provider = CurrentDateProvider(title="Current date", format="%Y-%m-%d %H:%M:%S")
        self.custom_info = SystemPromptInfo(
            background=["Custom background"],
            steps=["Custom step"],
            output_instructions=["Custom instruction"],
            context_providers={
                "test": MockContextProvider("Test Provider"),
                "date": self.current_date_provider,
                "lorem": LoremIpsumProvider(title="Lorem Ipsum")
            }
        )
        self.custom_generator = SystemPromptGenerator(self.custom_info)

class TestSystemPromptGeneratorBasic(SystemPromptGeneratorTestBase):
    """Tests for basic functionality of SystemPromptGenerator."""

    def test_default_initialization(self):
        """Test default initialization of SystemPromptGenerator."""
        self.assertEqual(
            self.default_generator.system_prompt_info.background,
            ['This is a conversation with a helpful and friendly AI assistant.']
        )
        self.assertEqual(len(self.default_generator.system_prompt_info.output_instructions), 2)

    def test_custom_initialization(self):
        """Test custom initialization of SystemPromptGenerator."""
        self.assertEqual(self.custom_generator.system_prompt_info, self.custom_info)
        self.assertEqual(len(self.custom_generator.system_prompt_info.output_instructions), 3)

    def test_generate_prompt_default(self):
        """Test generating a prompt with default settings."""
        prompt = self.default_generator.generate_prompt()
        self.assertIn("# IDENTITY and PURPOSE", prompt)
        self.assertIn("# OUTPUT INSTRUCTIONS", prompt)
        self.assertNotIn("# INTERNAL ASSISTANT STEPS", prompt)
        self.assertNotIn("# EXTRA INFORMATION AND CONTEXT", prompt)

    def test_generate_prompt_custom(self):
        """Test generating a prompt with custom settings."""
        prompt = self.custom_generator.generate_prompt()
        
        self.assertIn("# IDENTITY and PURPOSE", prompt)
        self.assertIn("# INTERNAL ASSISTANT STEPS", prompt)
        self.assertIn("# OUTPUT INSTRUCTIONS", prompt)
        self.assertIn("# EXTRA INFORMATION AND CONTEXT", prompt)
        self.assertIn("Custom background", prompt)
        self.assertIn("Custom step", prompt)
        self.assertIn("Custom instruction", prompt)
        self.assertIn("Mock info", prompt)

    def test_empty_system_prompt_info(self):
        """Test generating a prompt with empty SystemPromptInfo."""
        empty_info = SystemPromptInfo(background=[])
        empty_generator = SystemPromptGenerator(empty_info)
        prompt = empty_generator.generate_prompt()
        self.assertEqual(prompt, "# OUTPUT INSTRUCTIONS\n- Always respond using the proper JSON schema.\n- Always use the available additional information and context to enhance the response.\n\n")

    def test_partial_system_prompt_info(self):
        """Test generating a prompt with partial SystemPromptInfo."""
        partial_info = SystemPromptInfo(
            background=["Test background"],
            steps=["Test step"],
        )
        partial_generator = SystemPromptGenerator(partial_info)
        prompt = partial_generator.generate_prompt()
        self.assertIn("# IDENTITY and PURPOSE", prompt)
        self.assertIn("Test background", prompt)
        self.assertIn("# INTERNAL ASSISTANT STEPS", prompt)
        self.assertIn("Test step", prompt)
        self.assertIn("# OUTPUT INSTRUCTIONS", prompt)
        self.assertNotIn("# EXTRA INFORMATION AND CONTEXT", prompt)
        
class TestSystemPromptGeneratorContextProviders(SystemPromptGeneratorTestBase):
    """Tests for context providers in SystemPromptGenerator."""

    def test_generate_prompt_with_context_providers(self):
        """Test generating a prompt with context providers."""
        prompt = self.custom_generator.generate_prompt()
        
        self.assertIn("# IDENTITY and PURPOSE", prompt)
        self.assertIn("# INTERNAL ASSISTANT STEPS", prompt)
        self.assertIn("# OUTPUT INSTRUCTIONS", prompt)
        self.assertIn("# EXTRA INFORMATION AND CONTEXT", prompt)
        self.assertIn("Custom background", prompt)
        self.assertIn("Custom step", prompt)
        self.assertIn("Custom instruction", prompt)
        self.assertIn("Mock info", prompt)
        self.assertIn("## Current date", prompt)
        self.assertIn("The current date, in the format", prompt)
        self.assertIn("## Lorem Ipsum", prompt)
        self.assertIn("Lorem ipsum dolor sit amet", prompt)

    def test_current_date_provider(self):
        """Test the CurrentDateProvider."""
        mock_datetime = datetime(2023, 5, 1, 12, 0, 0)
        self.current_date_provider.get_current_datetime = Mock(return_value=mock_datetime)
        prompt = self.custom_generator.generate_prompt()
        self.assertIn("The current date, in the format \"%Y-%m-%d %H:%M:%S\", is 2023-05-01 12:00:00", prompt)

    def test_custom_output_instructions(self):
        """Test custom output instructions."""
        custom_instructions = ["Custom instruction 1", "Custom instruction 2"]
        custom_info = SystemPromptInfo(
            background=["Test background"],
            output_instructions=custom_instructions
        )
        custom_generator = SystemPromptGenerator(custom_info)
        prompt = custom_generator.generate_prompt()
        for instruction in custom_instructions:
            self.assertIn(instruction, prompt)
        self.assertIn("Always respond using the proper JSON schema.", prompt)
        self.assertIn("Always use the available additional information and context to enhance the response.", prompt)

    def test_empty_context_provider(self):
        """Test an empty context provider."""
        class EmptyProvider(SystemPromptContextProviderBase):
            def get_info(self):
                return ""

        info = SystemPromptInfo(
            background=["Test"],
            context_providers={"empty": EmptyProvider("Empty")}
        )
        generator = SystemPromptGenerator(info)
        prompt = generator.generate_prompt()
        self.assertNotIn("## Empty", prompt)

    def test_multiple_context_providers(self):
        """Test multiple context providers."""
        class Provider1(SystemPromptContextProviderBase):
            def get_info(self):
                return "Info 1"

        class Provider2(SystemPromptContextProviderBase):
            def get_info(self):
                return "Info 2"

        info = SystemPromptInfo(
            background=["Test"],
            context_providers={
                "provider1": Provider1("Provider 1"),
                "provider2": Provider2("Provider 2")
            }
        )
        generator = SystemPromptGenerator(info)
        prompt = generator.generate_prompt()
        self.assertIn("## Provider 1", prompt)
        self.assertIn("Info 1", prompt)
        self.assertIn("## Provider 2", prompt)
        self.assertIn("Info 2", prompt)

if __name__ == '__main__':
    unittest.main()
