from textual.widgets import Input
from textual.binding import Binding
from textual.message import Message


class NewItemInput(Input):
    """Configurable input field for creating new files or folders."""

    class Cancelled(Message):
        """Emitted when the user cancels the item creation."""

    class Submitted(Message):
        """Emitted when the user submits the item creation."""

        def __init__(self, value: str):
            self.value = value
            super().__init__()

    DEFAULT_CSS = """
    NewItemInput {
        dock: bottom;
        margin-bottom: 1;
        color: $text;
        display: none;
        border: solid #AAAA00 !important;
    }
    """

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    async def action_submit(self) -> None:
        """Handle a submit action."""

        self.post_message(self.Submitted(self.value))

    async def action_cancel(self) -> None:
        """Handle a cancel action."""
        self.post_message(self.Cancelled())
