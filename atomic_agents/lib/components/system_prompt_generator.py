from typing import List, Dict, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

class SystemPromptContextProviderBase(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_info(self) -> str:
        pass

@dataclass
class SystemPromptInfo:
    background: List[str]
    steps: Optional[List[str]] = field(default_factory=list)
    output_instructions: Optional[List[str]] = field(default_factory=list)
    context_providers: Optional[Dict[str, SystemPromptContextProviderBase]] = field(default_factory=dict)

class SystemPromptGenerator:
    def __init__(self, system_prompt_info: SystemPromptInfo = None):
        self.system_prompt_info = system_prompt_info or SystemPromptInfo(
            background=['This is a conversation with a helpful and friendly AI assistant.'],
            steps=[],
            output_instructions=[],
            context_providers={}
        )
        
        self.system_prompt_info.output_instructions.extend([
            'Always respond using the proper JSON schema.',
            'Always use the available additional information and context to enhance the response.'
        ])

    def generate_prompt(self) -> str:
        system_prompt = ''

        if self.system_prompt_info.background:
            system_prompt += '# IDENTITY and PURPOSE\n'
            system_prompt += '- ' + '\n- '.join(self.system_prompt_info.background) + '\n\n'

        if self.system_prompt_info.steps:
            system_prompt += '# INTERNAL ASSISTANT STEPS\n'
            system_prompt += '- ' + '\n- '.join(self.system_prompt_info.steps) + '\n\n'

        if self.system_prompt_info.output_instructions:
            system_prompt += '# OUTPUT INSTRUCTIONS\n'
            system_prompt += '- ' + '\n- '.join(self.system_prompt_info.output_instructions) + '\n\n'

        if self.system_prompt_info.context_providers:
            system_prompt += '# EXTRA INFORMATION AND CONTEXT\n'
            for provider in self.system_prompt_info.context_providers.values():
                info = provider.get_info()
                if info:
                    system_prompt += f'## {provider.title}\n'
                    system_prompt += f'{info}\n\n'

        return system_prompt

if __name__ == "__main__":
    class CurrentDateProvider(SystemPromptContextProviderBase):
        def __init__(self, format: str = '%Y-%m-%d %H:%M:%S', **kwargs):
            super().__init__(**kwargs)
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