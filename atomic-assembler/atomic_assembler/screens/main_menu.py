# In main_menu.py

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual import on

from atomic_assembler.widgets.gradient_title import GradientTitle
from atomic_assembler.widgets.menu import MenuWidget
from atomic_assembler.constants import (
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    MENU_OPTIONS,
)


class MainMenuScreen(Screen):
    """The main menu screen for the application."""

    CSS = """
    Vertical {
        width: 100%;
        height: auto;
        max-height: 20;
        align: center middle;
    }

    #title_container {
        width: 100%;
        height: auto;
        content-align: center top;
    }

    #menu_container {
        width: 100%;
        height: 1fr;
        align: center bottom;
        padding-bottom: 1;
    }

    MenuWidget {
        width: 100%;
        height: auto;
        content-align: center middle;
    }
    """

    def __init__(self):
        """Initialize the MainMenuScreen with a menu widget."""
        super().__init__()
        self.menu_widget = MenuWidget(MENU_OPTIONS)

    def compose(self) -> ComposeResult:
        """Compose the main layout of the screen."""
        yield Vertical(
            Container(
                GradientTitle(
                    "Atomic Assembler",
                    start_color=PRIMARY_COLOR,
                    end_color=SECONDARY_COLOR,
                ),
                id="title_container",
            ),
            Container(
                self.menu_widget,
                id="menu_container",
            ),
        )

    @on(MenuWidget.ItemSelected)
    def handle_item_selected(self, event: MenuWidget.ItemSelected) -> None:
        """Handle the selection of a menu item."""
        selected_option = MENU_OPTIONS[event.index]

        self.app.handle_menu_action(selected_option.action, **(selected_option.params or {}))

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
