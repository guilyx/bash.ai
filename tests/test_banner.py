"""Tests for banner module."""

from unittest.mock import patch

from flourish.ui.banner import animate_banner, print_banner


def test_print_banner():
    """Test print_banner function."""
    # Should not raise
    with patch("flourish.ui.banner.animate_banner") as mock_animate:
        print_banner()
        mock_animate.assert_called_once()


def test_animate_banner():
    """Test animate_banner function."""
    # Should not raise
    animate_banner(speed=0.001)  # Fast for testing
