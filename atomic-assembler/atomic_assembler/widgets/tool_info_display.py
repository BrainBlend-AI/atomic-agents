from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import ScrollableContainer
from textual.widgets import Static
from textual.app import ComposeResult
from atomic_assembler.constants import (
    PRIMARY_COLOR,
)


class ToolInfoDisplay(Widget):
    """Widget for displaying tool information."""

    tool_info = reactive({})

    DEFAULT_CSS = f"""
    ToolInfoDisplay {{
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr;
    }}

    #title {{
        width: 100%;
        padding: 1 2;
        color: $text;
        text-align: center;
        text-style: bold;
        border: solid {PRIMARY_COLOR};
    }}

    #content {{
        width: 100%;
        height: 100%;
    }}

    .tool-details, .env-vars {{
        border: solid {PRIMARY_COLOR};
        padding: 1 2;
        margin: 1 0;
    }}

    #tool-header, .env-vars-header {{
        text-align: left;
        text-style: bold;
        margin-bottom: 1;
    }}

    .env-var-name {{
        color: {PRIMARY_COLOR};
        text-style: bold;
    }}

    .env-var-description, .env-var-default {{
        padding-left: 1;
    }}
    """

    def __init__(self, tool_info: dict):
        super().__init__()
        self.tool_info = tool_info

    def compose(self) -> ComposeResult:
        """Compose the layout of the tool info display."""
        yield Static("Tool Information", id="title")

        with ScrollableContainer(id="content"):
            # Tool Details Section
            with Static(classes="tool-details"):
                yield Static("🔧 Tool Details", id="tool-header")
                yield Static(f"Name: {self.tool_info.get('tool_name', 'N/A')}", id="tool-name")
                yield Static(
                    f"Description: {self.tool_info.get('tool_description', 'No description available.')}",
                    id="tool-description",
                )

            # Environment Variables Section
            env_vars = self.tool_info.get("env_vars", {})
            if env_vars:
                with Static(classes="env-vars"):
                    yield Static("📌 Environment Variables", classes="env-vars-header")
                    for var, var_info in env_vars.items():
                        with Static(classes="env-var"):
                            yield Static(f"{var}", classes="env-var-name")
                            yield Static(
                                f"Description: {var_info.get('description', 'No description available.')}",
                                classes="env-var-description",
                            )
                            yield Static(
                                f"Default Value: {var_info.get('default', 'No default value')}",
                                classes="env-var-default",
                            )
            else:
                yield Static("No environment variables available.", classes="env-var-description")

    def watch_tool_info(self, new_info: dict) -> None:
        """React to changes in the tool_info."""
        self.refresh()
