from textual.widgets import SelectionList
from textual.widgets.selection_list import Selection
from textual.binding import Binding
from textual.message import Message
from rich.text import Text


class IconSelectionList(SelectionList):
    """A custom SelectionList that supports icons."""

    class ItemSelected(Message):
        """Message emitted when an item is selected."""

        def __init__(self, item_info: dict) -> None:
            self.item_info = item_info
            super().__init__()

    DEFAULT_CSS = """
    IconSelectionList {
        height: 1fr;
        border: solid $accent;
    }

    IconSelectionList > .selection-list--option {
        background: transparent;
    }

    IconSelectionList > .selection-list--option.-highlight {
        color: $text;
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("enter", "select", "Select", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.items = []

    def update_list(self, items: list):
        """Update the selection list."""
        self.items = items
        self.clear_options()
        for index, item in enumerate(items):
            self.add_option(self._create_item(item, index))

    def _create_item(self, item: dict, index: int) -> Selection:
        """Create a Selection representing an item."""
        icon = item.get("icon", "📄")
        label = Text(f"{icon} {item['name']}")
        return Selection(label, str(index))  # Use index as a string for the value

    def action_select(self):
        """Handle the selection action."""
        highlighted = self.highlighted
        if highlighted is not None:
            index = int(self.get_option_at_index(highlighted).value)
            self.post_message(self.ItemSelected(self.items[index]))

    def get_selected_item(self) -> dict:
        """Get the currently selected item."""
        highlighted = self.highlighted
        if highlighted is not None:
            index = int(self.get_option_at_index(highlighted).value)
            return self.items[index]
        return None
