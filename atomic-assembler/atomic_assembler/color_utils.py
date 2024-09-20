from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert a hex color string to an RGB tuple.

    Args:
        hex_color (str): The hex color string (e.g., "#FF0000").

    Returns:
        Tuple[int, int, int]: The RGB values as a tuple.
    """
    return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))


def interpolate_color(start_color: str, end_color: str, mix_ratio: float) -> str:
    """
    Interpolate between two colors based on a mix ratio.

    Args:
        start_color (str): The starting color in hex format (e.g., "#FF0000").
        end_color (str): The ending color in hex format.
        mix_ratio (float): A value between 0 and 1 representing the mix ratio.

    Returns:
        str: The interpolated color in hex format.
    """
    r1, g1, b1 = hex_to_rgb(start_color)
    r2, g2, b2 = hex_to_rgb(end_color)

    r = int(r1 * (1 - mix_ratio) + r2 * mix_ratio)
    g = int(g1 * (1 - mix_ratio) + g2 * mix_ratio)
    b = int(b1 * (1 - mix_ratio) + b2 * mix_ratio)

    return f"#{r:02x}{g:02x}{b:02x}"
