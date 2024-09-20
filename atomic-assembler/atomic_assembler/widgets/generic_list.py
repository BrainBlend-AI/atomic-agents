from textual.widgets import ListView, ListItem
from textual.binding import Binding
from textual.message import Message
from rich.text import Text
from typing import Any, Callable, Optional


class GenericList(ListView):
    """A generic ListView for displaying a list of items."""

    class ItemSelected(Message):
        """Message emitted when an item is selected."""

        def __init__(self, selected_item: Any) -> None:  # Improved parameter name
            self.item = selected_item  # Updated to match parameter name
            super().__init__()

    DEFAULT_CSS = """
    GenericList {
        height: 1fr;
        border: solid #AAAA00;
    }

    GenericList > ListItem {
        background: transparent;
    }

    GenericList > ListItem.--highlight {
        color: #000000;
        text-style: bold;
        background: #AAAA00 !important;
    }
    """

    BINDINGS = [
        Binding("enter", "select", "Select Item", priority=True),
    ]

    def __init__(self, item_renderer: Callable[[Any], str]):
        """Initialize the GenericList with a custom item renderer.

        Args:
            item_renderer (Callable[[Any], str]): A function that takes an item and returns its string representation.
        """
        super().__init__()
        self.item_list = []  # Renamed for clarity
        self.item_renderer = item_renderer
        self.highlighted_index = 0

    def update_list(
        self, new_items: list, highlighted_item: Optional[Any] = None
    ):  # Improved parameter name
        """Update the list with new items and optionally highlight one.

        Args:
            new_items (list): The list of items to display.
            highlighted_item (Optional[Any]): An item to highlight, if any.
        """
        self.item_list = new_items  # Renamed for clarity
        self.clear()
        for item in new_items:  # Updated to match parameter name
            self.append(self._create_item(item))

    def _create_item(self, item: Any) -> ListItem:
        """Create a ListItem representing a given item.

        Args:
            item (Any): The item to represent in the list.

        Returns:
            ListItem: The ListItem created for the item.
        """
        list_item = ListItem()
        list_item.item_data = item

        def render() -> Text:
            """Render the item using the provided item renderer."""
            return Text(self.item_renderer(item))

        list_item.render = render
        return list_item

    def action_select(self):
        """Handle the selection action for the highlighted item."""
        selected_item = self.highlighted_child  # Renamed for clarity
        if selected_item:
            self.post_message(self.ItemSelected(selected_item.item_data))

    def on_focus(self) -> None:
        self.index = self.highlighted_index

    def set_highlighted_index(self, index: int) -> None:
        self.highlighted_index = index
        self.blur()
        self.focus()
