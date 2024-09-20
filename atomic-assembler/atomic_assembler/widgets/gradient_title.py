import math
from typing import List
from logging import Logger

from pyfiglet import Figlet
from rich.align import Align
from rich.console import RenderResult
from rich.style import Style
from rich.text import Text
from rich.console import Group
from textual.widgets import Static

from atomic_assembler.color_utils import interpolate_color


class GradientTitle(Static):
    """A widget that displays a static gradient title."""

    def __init__(
        self,
        title_text: str,
        font: str = "big",
        start_color: str = "#CCCC00",
        end_color: str = "#CC00CC",
    ):
        """
        Initialize the GradientTitle widget.

        Args:
            title_text (str): The text to display as the title.
            font (str, optional): The font to use for the ASCII art. Defaults to "big".
            start_color (str, optional): The starting color of the gradient. Defaults to "#CCCC00".
            end_color (str, optional): The ending color of the gradient. Defaults to "#CC00CC".
        """
        super().__init__()
        self.title_text = title_text
        self.font = font
        self.start_color = start_color
        self.end_color = end_color
        self.gradient_offset = 2  # Renamed from animation_offset

        self.ascii_art = Figlet(font=self.font).renderText(self.title_text)
        self.max_width = max(len(line) for line in self.ascii_art.splitlines())

    def create_gradient_text_lines(self) -> List[Text]:
        """
        Create text lines with a gradient effect and bold styling.

        Returns:
            List[Text]: A list of rich.text.Text objects with gradient coloring and bold styling.
        """
        lines = self.ascii_art.splitlines()
        gradient_lines = []

        for line_index, line in enumerate(lines):
            if not line.strip() and line_index not in (0, len(lines) - 1):
                continue

            mix_ratio = (math.sin(self.gradient_offset + line_index * 0.33) + 1) / 2
            interpolated_color = interpolate_color(
                self.start_color, self.end_color, mix_ratio
            )

            styled_line = Text(line, Style(color=interpolated_color, bold=True))
            gradient_lines.append(styled_line)

        return gradient_lines

    def render(self) -> RenderResult:
        """
        Render the gradient title.

        Returns:
            RenderResult: The rendered gradient title.
        """
        gradient_lines = self.create_gradient_text_lines()

        centered_lines = [
            Align.center(line, width=self.max_width) for line in gradient_lines
        ]

        return Align.center(Group(*centered_lines), vertical="middle")
