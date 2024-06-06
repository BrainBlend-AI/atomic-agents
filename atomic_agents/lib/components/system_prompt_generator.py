from typing import List
from pydantic import BaseModel
from abc import ABC, abstractmethod

class SystemPromptInfo(BaseModel):
    background: List[str]
    steps: List[str]
    output_instructions: List[str]

class DynamicInfoProviderBase(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_info(self) -> str:
        pass

class SystemPromptGenerator:
    def __init__(self, system_prompt_info: SystemPromptInfo = None, dynamic_info_providers: dict[str, DynamicInfoProviderBase] = None):
        self.system_prompt_info = system_prompt_info or SystemPromptInfo(
            background=['This is a conversation with a helpful and friendly AI assistant.'],
            steps=[],
            output_instructions=[]
        )
        self.dynamic_info_providers = dynamic_info_providers or {}

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

        if self.dynamic_info_providers:
            system_prompt += '# EXTRA INFORMATION AND CONTEXT\n'
            for provider in self.dynamic_info_providers.values():
                info = provider.get_info()
                if info:
                    system_prompt += f'## {provider.title}\n'
                    system_prompt += f'{info}\n'

        return system_prompt
    
if __name__ == "__main__":
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
            'Always answer in rhyming verse. Preferably in alexandrine verse.'
        ]
    )
    system_prompt_generator = SystemPromptGenerator(system_prompt)

    print(system_prompt_generator.generate_prompt())
