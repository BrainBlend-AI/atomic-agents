from typing import List, Dict, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

class SystemPromptContextProviderBase(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_info(self) -> str:
        return
    
    def __repr__(self) -> str:
        return self.get_info()

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