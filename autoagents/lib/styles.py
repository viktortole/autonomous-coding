"""
ANSI Color Codes & Styling
==========================

Terminal styling utilities for AUTOAGENTS visual output.
"""


class Style:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = '\033[0m'

    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    # Foreground colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'


def colorize(text: str, color: str, bold: bool = False) -> str:
    """
    Apply color to text.

    Args:
        text: Text to colorize
        color: Style attribute (e.g., Style.RED)
        bold: Whether to make text bold

    Returns:
        Colorized text string
    """
    prefix = f"{Style.BOLD}{color}" if bold else color
    return f"{prefix}{text}{Style.RESET}"
