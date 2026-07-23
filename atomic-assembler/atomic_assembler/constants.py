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
    return urlunsplit(
        parsed_url._replace(
            netloc=f"***@{host}" if separator else parsed_url.netloc,
            query="***" if parsed_url.query else "",
            fragment="***" if parsed_url.fragment else "",
        )
    )


def validate_source_url(url: str) -> None:
    try:
        parsed_url = urlsplit(url)
    except ValueError as error:
        raise ValueError("Forge source URL is invalid: <redacted source URL>") from error
    if "@" in parsed_url.netloc or parsed_url.query or parsed_url.fragment:
        raise ValueError(
            f"Forge source URLs cannot include userinfo, query parameters, or fragments: {redact_source_url(url)}. "
            "Use Git credential helpers for private source access."
        )


@dataclass(frozen=True)
class ForgeSource:
    """A git repository that exposes an Atomic Forge tool index."""

    name: str
    url: str
    branch: str
    tools_path: str

    def __post_init__(self) -> None:
        validate_source_url(self.url)

    def to_dict(self) -> dict[str, str]:
        validate_source_url(self.url)
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
