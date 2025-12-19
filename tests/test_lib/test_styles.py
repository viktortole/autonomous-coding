"""
Tests for autoagents.lib.styles
"""

import pytest
from autoagents.lib.styles import Style, colorize


class TestStyle:
    """Tests for Style class."""

    def test_reset_is_escape_sequence(self):
        """RESET should be an ANSI escape sequence."""
        assert Style.RESET.startswith('\033[')
        assert Style.RESET == '\033[0m'

    def test_colors_defined(self):
        """All standard colors should be defined."""
        colors = ['RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE']
        for color in colors:
            assert hasattr(Style, color)
            assert getattr(Style, color).startswith('\033[')

    def test_text_styles_defined(self):
        """Text styles should be defined."""
        styles = ['BOLD', 'DIM', 'UNDERLINE']
        for style in styles:
            assert hasattr(Style, style)
            assert getattr(Style, style).startswith('\033[')

    def test_background_colors_defined(self):
        """Background colors should be defined."""
        bg_colors = ['BG_RED', 'BG_GREEN', 'BG_YELLOW', 'BG_BLUE']
        for bg in bg_colors:
            assert hasattr(Style, bg)
            assert getattr(Style, bg).startswith('\033[')


class TestColorize:
    """Tests for colorize function."""

    def test_colorize_adds_color(self):
        """colorize should wrap text with color codes."""
        result = colorize("hello", Style.RED)
        assert Style.RED in result
        assert Style.RESET in result
        assert "hello" in result

    def test_colorize_with_bold(self):
        """colorize with bold=True should include bold."""
        result = colorize("hello", Style.GREEN, bold=True)
        assert Style.BOLD in result
        assert Style.GREEN in result
        assert Style.RESET in result
