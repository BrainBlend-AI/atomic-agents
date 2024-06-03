from typing import List
from pydantic import BaseModel
from abc import ABC, abstractmethod

class SystemPrompt(BaseModel):
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
    def __init__(self, system_prompt: SystemPrompt, dynamic_info_providers: dict[str, DynamicInfoProviderBase] = None):
        self.system_prompt = system_prompt
        self.dynamic_info_providers = dynamic_info_providers or {}

    def generate_prompt(self) -> str:
        system_prompt = ''

        if self.system_prompt.background:
            system_prompt += '# IDENTITY and PURPOSE\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.background)}\n\n'

        if self.system_prompt.steps:
            system_prompt += '# INTERNAL ASSISTANT STEPS\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.steps)}\n\n'

        if self.system_prompt.output_instructions:
            system_prompt += '# OUTPUT INSTRUCTIONS\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.output_instructions)}\n\n'

        if self.dynamic_info_providers:
            system_prompt += '# EXTRA INFORMATION AND CONTEXT\n'
            for provider in self.dynamic_info_providers.values():
                info = provider.get_info()
                if info:
                    system_prompt += f'## {provider.title}\n'
                    system_prompt += f'{info}\n\n'

        return system_prompt