import logging
from textual import on
from textual.app import App
from textual.screen import Screen
from pathlib import Path
import webbrowser  # Import webbrowser module

from atomic_assembler.screens.main_menu import MainMenuScreen
from atomic_assembler.screens.file_explorer import FileExplorerScreen
from atomic_assembler.screens.atomic_tool_explorer import AtomicToolExplorerScreen
from atomic_assembler.constants import MENU_OPTIONS, Mode


class AtomicAssembler(App):
    """The main application class for Atomic Assembler."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    SCREENS = {
        "main_menu": MainMenuScreen,
        "atomic_tool_explorer": AtomicToolExplorerScreen,
        "file_explorer": FileExplorerScreen,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_path = None  # Renamed from selected_file to selected_path

    def on_mount(self) -> None:
        """Handler called when app is mounted."""
        self.push_screen("main_menu")

    def handle_menu_action(self, action: str, **kwargs) -> None:
        """Handle all menu actions dynamically."""
        action_map = {
            "browse_files": self.push_file_explorer,
            "browse_folders": self.push_folder_explorer,
            "download_tools": self.push_atomic_tool_explorer,
            "open_github": self.open_github,  # Added this line
            "exit": self.exit_app,
        }

        if action in action_map:
            action_map[action](**kwargs)
        else:
            logging.warning(f"Action '{action}' not implemented")

    def open_github(self) -> None:
        """Open the Atomic Agents GitHub page in a web browser."""
        webbrowser.open(
            "https://github.com/BrainBlend-AI/atomic-agents"
        )  # Open the URL

    def push_file_explorer(self, **kwargs):
        """Push the file explorer screen in file mode."""
        self.push_screen(
            FileExplorerScreen(
                mode=Mode.FILE_MODE,
                callback=self.handle_selection,  # Ensure this is set
            )
        )

    def push_folder_explorer(self, **kwargs):
        """Push the file explorer screen in directory mode."""
        self.push_screen(
            FileExplorerScreen(
                mode=Mode.DIRECTORY_MODE,
                callback=self.handle_selection,  # Renamed callback
            )
        )

    def push_atomic_tool_explorer(self, **kwargs) -> None:
        """Push the Atomic Tool Explorer screen."""
        self.push_screen("atomic_tool_explorer")

    def exit_app(self, **kwargs):
        """Exit the application."""
        self.exit()

    def handle_selection(self, selected_path: Path) -> None:  # Renamed method
        """Handle the selection of a file or folder."""
        logging.debug(f"File or folder selected in main app: {selected_path}")
        self.selected_path = selected_path  # Updated to use selected_path

    @on(FileExplorerScreen.FileSelected)
    def handle_file_selected(self, message: FileExplorerScreen.FileSelected) -> None:
        """Handle the file selected event."""
        logging.debug(f"File selected in main app: {message.path}")
        self.selected_path = message.path  # Updated to use selected_path
