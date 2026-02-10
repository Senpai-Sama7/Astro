import tempfile
from pathlib import Path
import os
import pytest
from astro_shell import AstroShell

def test_analyze_intent_file_read(tmp_path):
    shell = AstroShell()
    msg = 'Read "README.md"'
    intent = shell.analyze_intent(msg)
    assert intent.get("wants_file_read") is True
    assert "file_path" in intent

def test_tool_read_file(tmp_path, monkeypatch):
    p = tmp_path / "sample.txt"
    p.write_text("hello world")
    shell = AstroShell()
    # set cwd to tmp_path for relative resolution
    shell.cwd = tmp_path
    res = shell._tool_read_file("sample.txt")
    assert "hello world" in res

def test_react_loop_read_file(tmp_path):
    p = tmp_path / "notes.txt"
    p.write_text("line1\nline2\n")
    shell = AstroShell()
    shell.cwd = tmp_path
    out = shell.react_loop("Please read notes.txt")
    assert "notes.txt" in out or "line1" in out

def test_tool_shell_timeout():
    shell = AstroShell()
    # A command that sleeps longer than the timeout (use a harmless cross-platform approach)
    # Use Python sleep in a subprocess to ensure availability
    cmd = "python3 -c \"import time; time.sleep(2); print('done')\""
    # call with a very small timeout to trigger timeout behavior by calling _tool_shell directly
    res = shell._tool_shell(cmd, timeout=1)
    assert "timed out" in res.lower()