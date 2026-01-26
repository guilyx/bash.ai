"""Additional tests for enhancers."""

import os
from pathlib import Path

from flourish.plugins.enhancers import LsColorEnhancer


def test_ls_color_enhancer_long_format(tmp_path):
    """Test LsColorEnhancer with ls -l format."""
    enhancer = LsColorEnhancer()
    
    # Create test files
    (tmp_path / "file.txt").touch()
    (tmp_path / "dir").mkdir()
    
    # Simulate ls -l output
    ls_output = f"total 0\n-rw-r--r-- 1 user user 0 Jan 1 00:00 file.txt\ndrwxr-xr-x 2 user user 4096 Jan 1 00:00 dir"
    
    result = enhancer.enhance_output(
        "ls -l", ls_output, "", 0, str(tmp_path)
    )
    assert result["enhanced"] is True
    assert "stdout" in result


def test_ls_color_enhancer_with_error(tmp_path):
    """Test LsColorEnhancer with error."""
    enhancer = LsColorEnhancer()
    
    result = enhancer.enhance_output(
        "ls", "", "No such file", 1, str(tmp_path)
    )
    assert result["enhanced"] is False


def test_ls_color_enhancer_get_file_color_directory(tmp_path):
    """Test _get_file_color for directory."""
    enhancer = LsColorEnhancer()
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    
    color = enhancer._get_file_color(test_dir, tmp_path)
    assert enhancer.BLUE in color
    assert enhancer.BOLD in color


def test_ls_color_enhancer_get_file_color_executable(tmp_path):
    """Test _get_file_color for executable file."""
    enhancer = LsColorEnhancer()
    test_file = tmp_path / "test.sh"
    test_file.write_text("#!/bin/bash\necho test")
    test_file.chmod(0o755)
    
    color = enhancer._get_file_color(test_file, tmp_path)
    assert enhancer.GREEN in color


def test_ls_color_enhancer_get_file_color_archive(tmp_path):
    """Test _get_file_color for archive file."""
    enhancer = LsColorEnhancer()
    test_file = tmp_path / "test.zip"
    test_file.touch()
    
    color = enhancer._get_file_color(test_file, tmp_path)
    assert enhancer.YELLOW in color


def test_ls_color_enhancer_get_file_color_image(tmp_path):
    """Test _get_file_color for image file."""
    enhancer = LsColorEnhancer()
    test_file = tmp_path / "test.jpg"
    test_file.touch()
    
    color = enhancer._get_file_color(test_file, tmp_path)
    assert enhancer.MAGENTA in color


def test_ls_color_enhancer_get_file_color_symlink(tmp_path):
    """Test _get_file_color for symlink."""
    enhancer = LsColorEnhancer()
    target = tmp_path / "target"
    target.touch()
    symlink = tmp_path / "link"
    symlink.symlink_to(target)
    
    color = enhancer._get_file_color(symlink, tmp_path)
    assert enhancer.CYAN in color
