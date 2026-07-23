from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

PRIMARY_COLOR: str = "#AAAA00"
SECONDARY_COLOR: str = "#AA00AA"
BORDER_STYLE: str = f"bold {SECONDARY_COLOR}"
TITLE_FONT: str = "big"
TOOLS_SUBFOLDER: str = "atomic-forge/tools"
GITHUB_BASE_URL: str = "https://github.com/eigenwise/atomic-agents.git"
GITHUB_BRANCH: str = "main"


def source_url_has_userinfo(url: str) -> bool:
    try:
        return "@" in urlsplit(url).netloc
    except ValueError:
        return False


def redact_source_url(url: str) -> str:
    try:
        parsed_url = urlsplit(url)
    except ValueError:
        return "<redacted source URL>"
    _userinfo, separator, host = parsed_url.netloc.rpartition("@")
    if not separator:
        return url
    return urlunsplit(parsed_url._replace(netloc=f"***@{host}"))


@dataclass(frozen=True)
class ForgeSource:
    """A git repository that exposes an Atomic Forge tool index."""

    name: str
    url: str
    branch: str
    tools_path: str

    def __post_init__(self) -> None:
        if source_url_has_userinfo(self.url):
            raise ValueError(
                f"Forge source URLs cannot include userinfo: {redact_source_url(self.url)}. "
                "Use Git credential helpers for private source access."
            )

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
