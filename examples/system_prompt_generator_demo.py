from datetime import datetime
from unittest.mock import Mock
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator, SystemPromptInfo


class CurrentDateProvider(SystemPromptContextProviderBase):
        def __init__(self, title, format: str = '%Y-%m-%d %H:%M:%S'):
            super().__init__(title)
            self.format = format

        def get_info(self) -> str:
            return f'The current date, in the format "{self.format}", is {datetime.now().strftime(self.format)}'

class LoremIpsumProvider(SystemPromptContextProviderBase):
    def get_info(self) -> str:
        return (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
        )

system_prompt = SystemPromptInfo(
    background=[
        'This assistant is a general-purpose AI designed to be helpful and friendly.',
    ],
    steps=[
        'Understand the user\'s input and provide a relevant response.',
        'Respond to the user.'
    ],
    output_instructions=[
        'Provide helpful and relevant information to assist the user.',
        'Be friendly and respectful in all interactions.',
        'Always answer in rhyming verse.'
    ],
    context_providers={
        'date': CurrentDateProvider(title='Current date', format='%Y-%m-%d %H:%M:%S'),
        'lorem': LoremIpsumProvider(title='Lorem Ipsum')
    }
)

system_prompt_generator = SystemPromptGenerator(system_prompt)
print(system_prompt_generator.generate_prompt())


def test_generate_prompt_with_empty_providers():
    """Test generating a prompt with empty context providers."""
    empty_provider = Mock(spec=SystemPromptContextProviderBase)
    empty_provider.get_info.return_value = ""
    empty_provider.title = "Empty Provider"

    info = SystemPromptInfo(
        background=["Test background"],
        context_providers={"empty": empty_provider}
    )
    generator = SystemPromptGenerator(info)
    prompt = generator.generate_prompt()

    assert "# IDENTITY and PURPOSE" in prompt
    assert "Test background" in prompt
    assert "# EXTRA INFORMATION AND CONTEXT" in prompt
    assert "## Empty Provider" not in prompt
