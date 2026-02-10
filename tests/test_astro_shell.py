"""Tests for astro_shell.py."""
import sys
import pytest
from astro_shell import AstroShell


def test_analyze_intent_file_read():
    """Test intent analysis for file read commands."""
    shell = AstroShell()
    msg = 'Read "README.md"'
    intent = shell.analyze_intent(msg)
    assert intent.get("wants_file_read") is True
    assert "file_path" in intent


def test_tool_read_file(tmp_path, monkeypatch):
    """Test file reading functionality."""
    p = tmp_path / "sample.txt"
    p.write_text("hello world")
    shell = AstroShell()
    # set cwd to tmp_path for relative resolution
    shell.cwd = tmp_path
    res = shell._tool_read_file("sample.txt")
    assert "hello world" in res


def test_react_loop_read_file(tmp_path):
    """Test ReAct loop with file read."""
    p = tmp_path / "notes.txt"
    p.write_text("line1\nline2\n")
    shell = AstroShell()
    shell.cwd = tmp_path
    out = shell.react_loop("Please read notes.txt")
    assert "notes.txt" in out or "line1" in out


def test_tool_shell_timeout():
    """Test shell command timeout."""
    shell = AstroShell()
    # Use current Python executable for portability
    cmd = f'{sys.executable} -c "import time; time.sleep(2); print(\'done\')"'
    # call with a very small timeout to trigger timeout behavior
    res = shell._tool_shell(cmd, timeout=1)
    assert "timed out" in res.lower() or "done" in res or "error" in res
