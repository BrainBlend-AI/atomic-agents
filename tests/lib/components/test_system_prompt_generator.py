import pytest
from datetime import datetime
from unittest.mock import Mock

from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptContextProviderBase,
    SystemPromptInfo,
    SystemPromptGenerator,
)

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

@pytest.fixture
def default_generator():
    return SystemPromptGenerator()

@pytest.fixture
def custom_info():
    current_date_provider = CurrentDateProvider(title="Current date", format="%Y-%m-%d %H:%M:%S")
    return SystemPromptInfo(
        background=["Custom background"],
        steps=["Custom step"],
        output_instructions=["Custom instruction"],
        context_providers={
            "test": MockContextProvider("Test Provider"),
            "date": current_date_provider,
            "lorem": LoremIpsumProvider(title="Lorem Ipsum")
        }
    )

@pytest.fixture
def custom_generator(custom_info):
    return SystemPromptGenerator(custom_info)

class TestSystemPromptContextProviderBase:
    def test_abstract_base_class(self):
        with pytest.raises(TypeError):
            SystemPromptContextProviderBase("Test")

    def test_repr(self):
        class ConcreteProvider(SystemPromptContextProviderBase):
            def get_info(self):
                return "Test Info"

        provider = ConcreteProvider("Test")
        assert repr(provider) == "Test Info"

class TestSystemPromptInfo:
    def test_default_values(self):
        info = SystemPromptInfo(background=["Test background"])
        assert info.background == ["Test background"]
        assert info.steps == []
        assert info.output_instructions == []
        assert info.context_providers == {}

    def test_custom_values(self):
        info = SystemPromptInfo(
            background=["Test background"],
            steps=["Step 1", "Step 2"],
            output_instructions=["Instruction 1"],
            context_providers={"test": None}
        )
        assert info.background == ["Test background"]
        assert info.steps == ["Step 1", "Step 2"]
        assert info.output_instructions == ["Instruction 1"]
        assert info.context_providers == {"test": None}

class TestSystemPromptGeneratorBasic:
    def test_default_initialization(self, default_generator):
        assert default_generator.system_prompt_info.background == ['This is a conversation with a helpful and friendly AI assistant.']
        assert len(default_generator.system_prompt_info.output_instructions) == 2

    def test_custom_initialization(self, custom_generator, custom_info):
        assert custom_generator.system_prompt_info == custom_info
        assert len(custom_generator.system_prompt_info.output_instructions) == 3

    def test_generate_prompt_default(self, default_generator):
        prompt = default_generator.generate_prompt()
        assert "# IDENTITY and PURPOSE" in prompt
        assert "# OUTPUT INSTRUCTIONS" in prompt
        assert "# INTERNAL ASSISTANT STEPS" not in prompt
        assert "# EXTRA INFORMATION AND CONTEXT" not in prompt

    def test_generate_prompt_custom(self, custom_generator):
        prompt = custom_generator.generate_prompt()
        
        assert "# IDENTITY and PURPOSE" in prompt
        assert "# INTERNAL ASSISTANT STEPS" in prompt
        assert "# OUTPUT INSTRUCTIONS" in prompt
        assert "# EXTRA INFORMATION AND CONTEXT" in prompt
        assert "Custom background" in prompt
        assert "Custom step" in prompt
        assert "Custom instruction" in prompt
        assert "Mock info" in prompt

    def test_empty_system_prompt_info(self):
        empty_info = SystemPromptInfo(background=[])
        empty_generator = SystemPromptGenerator(empty_info)
        prompt = empty_generator.generate_prompt()
        expected_prompt = "# OUTPUT INSTRUCTIONS\n- Always respond using the proper JSON schema.\n- Always use the available additional information and context to enhance the response."
        assert prompt == expected_prompt

    def test_partial_system_prompt_info(self):
        partial_info = SystemPromptInfo(
            background=["Test background"],
            steps=["Test step"],
        )
        partial_generator = SystemPromptGenerator(partial_info)
        prompt = partial_generator.generate_prompt()
        assert "# IDENTITY and PURPOSE" in prompt
        assert "Test background" in prompt
        assert "# INTERNAL ASSISTANT STEPS" in prompt
        assert "Test step" in prompt
        assert "# OUTPUT INSTRUCTIONS" in prompt
        assert "# EXTRA INFORMATION AND CONTEXT" not in prompt

class TestSystemPromptGeneratorContextProviders:
    def test_generate_prompt_with_context_providers(self, custom_generator):
        prompt = custom_generator.generate_prompt()
        
        assert "# IDENTITY and PURPOSE" in prompt
        assert "# INTERNAL ASSISTANT STEPS" in prompt
        assert "# OUTPUT INSTRUCTIONS" in prompt
        assert "# EXTRA INFORMATION AND CONTEXT" in prompt
        assert "Custom background" in prompt
        assert "Custom step" in prompt
        assert "Custom instruction" in prompt
        assert "Mock info" in prompt
        assert "## Current date" in prompt
        assert "The current date, in the format" in prompt
        assert "## Lorem Ipsum" in prompt
        assert "Lorem ipsum dolor sit amet" in prompt

    def test_current_date_provider(self, custom_generator, monkeypatch):
        mock_datetime = datetime(2023, 5, 1, 12, 0, 0)
        monkeypatch.setattr(custom_generator.system_prompt_info.context_providers['date'], 'get_current_datetime', lambda: mock_datetime)
        prompt = custom_generator.generate_prompt()
        assert 'The current date, in the format "%Y-%m-%d %H:%M:%S", is 2023-05-01 12:00:00' in prompt

    def test_custom_output_instructions(self):
        custom_instructions = ["Custom instruction 1", "Custom instruction 2"]
        custom_info = SystemPromptInfo(
            background=["Test background"],
            output_instructions=custom_instructions
        )
        custom_generator = SystemPromptGenerator(custom_info)
        prompt = custom_generator.generate_prompt()
        for instruction in custom_instructions:
            assert instruction in prompt
        assert "Always respond using the proper JSON schema." in prompt
        assert "Always use the available additional information and context to enhance the response." in prompt

    def test_empty_context_provider(self):
        class EmptyProvider(SystemPromptContextProviderBase):
            def get_info(self):
                return ""

        info = SystemPromptInfo(
            background=["Test"],
            context_providers={"empty": EmptyProvider("Empty")}
        )
        generator = SystemPromptGenerator(info)
        prompt = generator.generate_prompt()
        assert "## Empty" not in prompt

    def test_multiple_context_providers(self):
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
        assert "## Provider 1" in prompt
        assert "Info 1" in prompt
        assert "## Provider 2" in prompt
        assert "Info 2" in prompt
        
if __name__ == '__main__':
    pytest.main()