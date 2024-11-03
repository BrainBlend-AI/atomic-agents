from dataclasses import dataclass
from datetime import datetime
from typing import List
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase


@dataclass
class ContentItem:
    content: str
    url: str


class ScrapedContentContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.content_items: List[ContentItem] = []

    def get_info(self) -> str:
        return "\n\n".join(
            [
                f"Source {idx}:\nURL: {item.url}\nContent:\n{item.content}\n{'-' * 80}"
                for idx, item in enumerate(self.content_items, 1)
            ]
        )


class CurrentDateContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str, date_format: str = "%A %B %d, %Y"):
        super().__init__(title=title)
        self.date_format = date_format

    def get_info(self) -> str:
        return f"The current date in the format {self.date_format} is {datetime.now().strftime(self.date_format)}."
