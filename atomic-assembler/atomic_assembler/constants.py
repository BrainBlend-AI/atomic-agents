from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Color configuration
PRIMARY_COLOR: str = "#AAAA00"
SECONDARY_COLOR: str = "#AA00AA"
BORDER_STYLE: str = f"bold {SECONDARY_COLOR}"

# Title configuration
TITLE_FONT: str = "big"


@dataclass
class MenuOption:
    """Dataclass representing a menu option."""

    label: str
    action: str
    params: Optional[Dict[str, Any]] = None


# Define menu options as a list of MenuOption instances
MENU_OPTIONS: List[MenuOption] = [
    # MenuOption("Browse Files", "browse_files"),
    # MenuOption("Browse Folders", "browse_folders"),
    MenuOption("Download Tools", "download_tools"),
    MenuOption("Open Atomic Agents on GitHub", "open_github"),  # Added this line
    MenuOption("Quit", "exit"),
]


class Mode(Enum):
    FILE_MODE = "file_mode"
    DIRECTORY_MODE = "directory_mode"
