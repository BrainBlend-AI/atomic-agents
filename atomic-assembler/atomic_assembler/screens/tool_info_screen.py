from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Markdown
from textual.binding import Binding
from textual.screen import Screen


class ToolInfoScreen(Screen):
    """Screen for displaying tool information."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, tool_name: str, readme_content: str):
        """Initialize the ToolInfoScreen with tool information."""
        super().__init__()
        self.tool_name = tool_name
        self.readme_content = readme_content

    def compose(self) -> ComposeResult:
        """Compose the layout of the tool info screen."""
        with VerticalScroll():
            yield Markdown(self.readme_content)
        yield Footer()
