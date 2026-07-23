from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

PRIMARY_COLOR: str = "#AAAA00"
SECONDARY_COLOR: str = "#AA00AA"
BORDER_STYLE: str = f"bold {SECONDARY_COLOR}"
TITLE_FONT: str = "big"
TOOLS_SUBFOLDER: str = "atomic-forge/tools"
GITHUB_BASE_URL: str = "https://github.com/eigenwise/atomic-agents.git"
GITHUB_BRANCH: str = "main"


@dataclass(frozen=True)
class ForgeSource:
    """A git repository that exposes an Atomic Forge tool index."""

    name: str
    url: str
    branch: str
    tools_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "url": self.url,
            "branch": self.branch,
            "tools_path": self.tools_path,
        }


DEFAULT_SOURCES: tuple[ForgeSource, ...] = (ForgeSource("official", GITHUB_BASE_URL, GITHUB_BRANCH, TOOLS_SUBFOLDER),)


@dataclass
class MenuOption:
    """Dataclass representing a menu option."""

    label: str
    action: str
    params: Optional[Dict[str, Any]] = None


MENU_OPTIONS: List[MenuOption] = [
    MenuOption("Download Tools", "download_tools"),
    MenuOption("Open Atomic Agents on GitHub", "open_github"),
    MenuOption("Quit", "exit"),
]


class Mode(Enum):
    FILE_MODE = "file_mode"
    DIRECTORY_MODE = "directory_mode"
