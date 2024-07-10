from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SystemPromptContextProviderBase(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_info(self) -> str:
        pass

    def __repr__(self) -> str:
        return self.get_info()


@dataclass
class SystemPromptInfo:
    background: List[str]
    steps: List[str] = field(default_factory=list)
    output_instructions: List[str] = field(default_factory=list)
    context_providers: Dict[str, SystemPromptContextProviderBase] = field(default_factory=dict)


class SystemPromptGenerator:
    def __init__(self, system_prompt_info: Optional[SystemPromptInfo] = None):
        self.system_prompt_info = system_prompt_info or SystemPromptInfo(
            background=["This is a conversation with a helpful and friendly AI assistant."]
        )

        self.system_prompt_info.output_instructions.extend(
            [
                "Always respond using the proper JSON schema.",
                "Always use the available additional information and context to enhance the response.",
            ]
        )

    def generate_prompt(self) -> str:
        sections = [
            ("IDENTITY and PURPOSE", self.system_prompt_info.background),
            ("INTERNAL ASSISTANT STEPS", self.system_prompt_info.steps),
            ("OUTPUT INSTRUCTIONS", self.system_prompt_info.output_instructions),
        ]

        prompt_parts = []

        for title, content in sections:
            if content:
                prompt_parts.append(f"# {title}")
                prompt_parts.extend(f"- {item}" for item in content)
                prompt_parts.append("")

        if self.system_prompt_info.context_providers:
            prompt_parts.append("# EXTRA INFORMATION AND CONTEXT")
            for provider in self.system_prompt_info.context_providers.values():
                info = provider.get_info()
                if info:
                    prompt_parts.append(f"## {provider.title}")
                    prompt_parts.append(info)
                    prompt_parts.append("")

        return "\n".join(prompt_parts).strip()
