from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class SystemPromptContextProviderBase(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_info(self) -> str:
        pass

    def __repr__(self) -> str:
        return self.get_info()


class SystemPromptGenerator:
    def __init__(
        self,
        background: Optional[List[str]] = None,
        steps: Optional[List[str]] = None,
        output_instructions: Optional[List[str]] = None,
        context_providers: Optional[Dict[str, SystemPromptContextProviderBase]] = None,
    ):
        self.background = background or ["This is a conversation with a helpful and friendly AI assistant."]
        self.steps = steps or []
        self.output_instructions = output_instructions or []
        self.context_providers = context_providers or {}

        self.output_instructions.extend(
            [
                "Always respond using the proper JSON schema.",
                "Always use the available additional information and context to enhance the response.",
            ]
        )

    def generate_prompt(self) -> str:
        sections = [
            ("IDENTITY and PURPOSE", self.background),
            ("INTERNAL ASSISTANT STEPS", self.steps),
            ("OUTPUT INSTRUCTIONS", self.output_instructions),
        ]

        prompt_parts = []

        for title, content in sections:
            if content:
                prompt_parts.append(f"# {title}")
                prompt_parts.extend(f"- {item}" for item in content)
                prompt_parts.append("")

        if self.context_providers:
            prompt_parts.append("# EXTRA INFORMATION AND CONTEXT")
            for provider in self.context_providers.values():
                info = provider.get_info()
                if info:
                    prompt_parts.append(f"## {provider.title}")
                    prompt_parts.append(info)
                    prompt_parts.append("")

        return "\n".join(prompt_parts).strip()
