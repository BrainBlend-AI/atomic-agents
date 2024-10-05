from typing import List
from textual.reactive import reactive
from textual.widget import Widget
from textual.message import Message
from textual.binding import Binding
from atomic_assembler.constants import PRIMARY_COLOR, MenuOption


class MenuWidget(Widget):
    """A widget that displays a selectable menu."""

    class ItemSelected(Message):
        """Emitted when an item is selected."""

        def __init__(self, index: int):
            self.index = index
            super().__init__()

    _selected_index = reactive(0)

    BINDINGS = [
        Binding("enter", "select", "Select item", priority=True),
        Binding("up", "move_up", "Move up"),
        Binding("down", "move_down", "Move down"),
    ]

    def __init__(self, menu_items: List[MenuOption]):
        """
        Initialize the MenuWidget.

        Args:
            menu_items (List[MenuOption]): A list of MenuOption instances representing menu options.
        """
        super().__init__()
        self._menu_items = menu_items
        self.can_focus = True

    def on_mount(self) -> None:
        """Set focus to this widget when mounted."""
        self.focus()

    def render(self) -> str:
        """
        Render the menu items with the current selection highlighted.

        Returns:
            str: The rendered menu items as a string.
        """
        rendered_menu_items = []
        for index, item in enumerate(self._menu_items):
            is_selected = index == self._selected_index
            menu_text = (
                f"[{PRIMARY_COLOR} bold][ {item.label} ][/{PRIMARY_COLOR} bold]" if is_selected else f"  {item.label}  "
            )
            rendered_menu_items.append(f"[center]{menu_text}[/center]")

        return "\n".join(rendered_menu_items)

    def action_move_up(self) -> None:
        """Move the selection up."""
        self._move_selection(-1)

    def action_move_down(self) -> None:
        """Move the selection down."""
        self._move_selection(1)

    def action_select(self) -> None:
        """Handle the selection of a menu item."""
        self.post_message(self.ItemSelected(self._selected_index))

    def _move_selection(self, direction: int) -> None:
        """Move the selection up or down, wrapping around if necessary."""
        self._selected_index = (self._selected_index + direction) % len(self._menu_items)
