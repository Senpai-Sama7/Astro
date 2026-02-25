"""
Unit tests for vibe_shell.py - Async LLM-powered ReAct orchestrator.

Run with: python3 -m pytest tests/test_vibe_shell.py -v
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# We need to import the module - handle import errors gracefully
try:
    from vibe_shell import (
        VibeShell, Action, Step, LLMProvider,
        ValidationError, VibeShellError
    )
    HAS_VIBE_SHELL = True
except ImportError as e:
    HAS_VIBE_SHELL = False
    print(f"Warning: Could not import vibe_shell: {e}")

class TestVibeShellBasics:
    """Test basic VibeShell initialization and configuration."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test that VibeShell initializes correctly."""
        shell = VibeShell()
        assert shell.cwd == os.getcwd()
        assert shell.token is None
        assert shell.history == []
        assert shell.llm_providers == []
        assert shell.session is None
        assert not shell._initialized
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_prompt_generation(self):
        """Test prompt string generation."""
        shell = VibeShell()
        shell.cwd = "/home/user/projects"
        
        # Without LLM provider
        shell.llm_providers = []
        prompt = shell.prompt()
        assert "💤" in prompt
        assert "projects" in prompt
        
        # With LLM provider
        mock_provider = MagicMock()
        mock_provider.name = "anthropic"
        shell.llm_providers = [mock_provider]
        prompt = shell.prompt()
        assert "🧠" in prompt
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_is_direct_command(self):
        """Test detection of direct shell commands."""
        shell = VibeShell()
        
        # Direct commands
        assert shell.is_direct_command("ls -la")
        assert shell.is_direct_command("git status")
        assert shell.is_direct_command("python3 script.py")
        assert shell.is_direct_command("./script.sh")
        assert shell.is_direct_command("/usr/bin/python3")
        assert shell.is_direct_command("~/Documents")
        
        # Not direct commands (natural language)
        assert not shell.is_direct_command("what files are here")
        assert not shell.is_direct_command("show me the readme")
        assert not shell.is_direct_command("")


class TestActionAndStep:
    """Test Action and Step dataclasses."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_action_creation(self):
        """Test Action dataclass creation and validation."""
        action = Action("shell", {"cmd": "echo hello"})
        assert action.tool == "shell"
        assert action.args == {"cmd": "echo hello"}
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_action_validation_invalid_tool(self):
        """Test Action validation with invalid tool."""
        with pytest.raises(ValidationError):
            Action("", {"cmd": "echo hello"})
        
        with pytest.raises(ValidationError):
            Action(123, {"cmd": "echo hello"})  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_action_validation_invalid_args(self):
        """Test Action validation with invalid args."""
        with pytest.raises(ValidationError):
            Action("shell", "not a dict")  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_step_creation(self):
        """Test Step dataclass creation."""
        step = Step(thought="I need to list files")
        assert step.thought == "I need to list files"
        assert step.action is None
        assert step.observation is None
        assert step.answer is None
        
        action = Action("shell", {"cmd": "ls"})
        step = Step(
            thought="I need to list files",
            action=action,
            observation="file1.txt file2.txt",
            answer="Here are the files"
        )
        assert step.action == action
        assert step.observation == "file1.txt file2.txt"
        assert step.answer == "Here are the files"


class TestParseLLMResponse:
    """Test LLM response parsing."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_thought_only(self):
        """Test parsing response with only thought."""
        shell = VibeShell()
        response = "THOUGHT: I need to check the directory"
        step = shell.parse_llm_response(response)
        
        assert step.thought == "I need to check the directory"
        assert step.action is None
        assert step.answer is None
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_with_action(self):
        """Test parsing response with thought and action."""
        shell = VibeShell()
        response = """THOUGHT: I need to list files
ACTION: shell(ls -la)"""
        step = shell.parse_llm_response(response)
        
        assert step.thought == "I need to list files"
        assert step.action is not None
        assert step.action.tool == "shell"
        assert step.action.args["cmd"] == "ls -la"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_with_answer(self):
        """Test parsing response with answer."""
        shell = VibeShell()
        response = """THOUGHT: I found the files
ANSWER: Here are the files in the directory"""
        step = shell.parse_llm_response(response)
        
        assert step.thought == "I found the files"
        assert step.answer == "Here are the files in the directory"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_read_file_action(self):
        """Test parsing read_file action."""
        shell = VibeShell()
        response = "THOUGHT: Read the file\nACTION: read_file(README.md)"
        step = shell.parse_llm_response(response)
        
        assert step.action.tool == "read_file"
        assert step.action.args["path"] == "README.md"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_write_file_action(self):
        """Test parsing write_file action."""
        shell = VibeShell()
        response = 'THOUGHT: Write to file\nACTION: write_file("test.txt", "hello world")'
        step = shell.parse_llm_response(response)
        
        assert step.action.tool == "write_file"
        assert step.action.args["path"] == "test.txt"
        assert step.action.args["content"] == "hello world"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_search_action(self):
        """Test parsing search action."""
        shell = VibeShell()
        response = "THOUGHT: Search for pattern\nACTION: search(def main, .)"
        step = shell.parse_llm_response(response)
        
        assert step.action.tool == "search"
        assert step.action.args["pattern"] == "def main"
        assert step.action.args["path"] == "."
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_empty_response(self):
        """Test parsing empty response."""
        shell = VibeShell()
        step = shell.parse_llm_response("")
        
        assert step.thought == ""
        assert step.action is None
        assert step.answer is None
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_parse_non_string_response(self):
        """Test parsing non-string response."""
        shell = VibeShell()
        step = shell.parse_llm_response(None)  # type: ignore
        
        assert step.thought == ""
        assert step.action is None


class TestToolExecution:
    """Test async tool execution."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_shell_basic(self, tmp_path):
        """Test basic shell command execution."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        result = await shell.tool_shell("echo hello")
        assert "hello" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_shell_empty_command(self):
        """Test shell with empty command."""
        shell = VibeShell()
        
        result = await shell.tool_shell("")
        assert result == "(no command)"
        
        result = await shell.tool_shell("   ")
        assert result == "(no command)"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_shell_invalid_type(self):
        """Test shell with invalid command type."""
        shell = VibeShell()
        
        with pytest.raises(ValidationError):
            await shell.tool_shell(123)  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_shell_dangerous_command_blocked(self):
        """Test that dangerous commands are blocked."""
        shell = VibeShell()
        
        # Fork bomb pattern
        result = await shell.tool_shell(":(){ :|:& };:")
        assert "blocked" in result.lower() or "fork bomb" in result.lower()
        
        # DD disk destruction pattern
        result = await shell.tool_shell("dd if=/dev/zero of=/dev/sda")
        assert "blocked" in result.lower() or "disk destruction" in result.lower()
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_shell_timeout(self):
        """Test shell command timeout."""
        shell = VibeShell()
        
        result = await shell.tool_shell("sleep 5", timeout=0.1)
        assert "timed out" in result.lower()
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_read_file(self, tmp_path):
        """Test file reading."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        result = await shell.tool_read_file("test.txt")
        assert "hello world" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_read_file_not_found(self, tmp_path):
        """Test reading non-existent file."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        result = await shell.tool_read_file("nonexistent.txt")
        assert "not found" in result.lower()
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_read_file_invalid_type(self):
        """Test read_file with invalid path type."""
        shell = VibeShell()
        
        with pytest.raises(ValidationError):
            await shell.tool_read_file(123)  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_write_file(self, tmp_path):
        """Test file writing."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        result = await shell.tool_write_file("output.txt", "test content")
        assert "Written" in result
        assert "12 chars" in result  # len("test content") == 12
        
        # Verify file was written
        written_file = tmp_path / "output.txt"
        assert written_file.read_text() == "test content"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_write_file_creates_directories(self, tmp_path):
        """Test that write_file creates parent directories."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        result = await shell.tool_write_file("subdir/nested/file.txt", "content")
        assert "Written" in result
        
        written_file = tmp_path / "subdir" / "nested" / "file.txt"
        assert written_file.exists()
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_write_file_invalid_type(self):
        """Test write_file with invalid types."""
        shell = VibeShell()
        
        with pytest.raises(ValidationError):
            await shell.tool_write_file(123, "content")  # type: ignore
        
        with pytest.raises(ValidationError):
            await shell.tool_write_file("path", 123)  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_search(self, tmp_path):
        """Test file search."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        # Create test files
        (tmp_path / "file1.txt").write_text("hello world")
        (tmp_path / "file2.txt").write_text("hello again")
        
        result = await shell.tool_search("hello", ".")
        assert "hello" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_search_empty_pattern(self):
        """Test search with empty pattern."""
        shell = VibeShell()
        
        result = await shell.tool_search("", ".")
        assert "empty" in result.lower()
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_tool_search_invalid_type(self):
        """Test search with invalid types."""
        shell = VibeShell()
        
        with pytest.raises(ValidationError):
            await shell.tool_search(123, ".")  # type: ignore
        
        with pytest.raises(ValidationError):
            await shell.tool_search("pattern", 123)  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_execute_action(self, tmp_path):
        """Test action execution dispatcher."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        # Test shell action
        action = Action("shell", {"cmd": "echo test"})
        result = await shell.execute_action(action)
        assert "test" in result
        
        # Test read_file action
        (tmp_path / "test.txt").write_text("content")
        action = Action("read_file", {"path": "test.txt"})
        result = await shell.execute_action(action)
        assert "content" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_execute_action_unknown_tool(self):
        """Test execution of unknown tool."""
        shell = VibeShell()
        
        action = Action("unknown_tool", {})
        result = await shell.execute_action(action)
        assert "unknown tool" in result.lower()
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_execute_action_invalid_action(self):
        """Test execution with invalid action type."""
        shell = VibeShell()
        
        with pytest.raises(ValidationError):
            await shell.execute_action("not an action")  # type: ignore


class TestBuiltinCommands:
    """Test built-in shell commands."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_cd(self, tmp_path):
        """Test cd built-in command."""
        shell = VibeShell()
        
        # Change to temp directory
        result = await shell.handle_builtin(f"cd {tmp_path}")
        assert "📂" in result
        assert str(tmp_path) in shell.cwd
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_cd_no_args(self, tmp_path, monkeypatch):
        """Test cd with no arguments (should go to home)."""
        shell = VibeShell()
        monkeypatch.setenv("HOME", str(tmp_path))
        
        result = await shell.handle_builtin("cd")
        assert "📂" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_cd_invalid(self, tmp_path):
        """Test cd to non-existent directory."""
        shell = VibeShell()
        
        result = await shell.handle_builtin("cd /nonexistent/path/12345")
        assert "Not a directory" in result or "Error" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_pwd(self):
        """Test pwd built-in command."""
        shell = VibeShell()
        shell.cwd = "/test/path"
        
        result = await shell.handle_builtin("pwd")
        assert result == "/test/path"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_help(self):
        """Test help built-in command."""
        shell = VibeShell()
        
        result = await shell.handle_builtin("help")
        assert "ASTRO Vibe Shell" in result
        assert "Built-ins:" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_clear(self):
        """Test clear built-in command."""
        shell = VibeShell()
        
        result = await shell.handle_builtin("clear")
        assert result == ""  # clear returns empty string
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_not_builtin(self):
        """Test that non-built-in commands return None."""
        shell = VibeShell()
        
        result = await shell.handle_builtin("ls -la")
        assert result is None
        
        result = await shell.handle_builtin("echo hello")
        assert result is None
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_builtin_empty(self):
        """Test empty built-in command."""
        shell = VibeShell()
        
        result = await shell.handle_builtin("")
        assert result is None
        
        result = await shell.handle_builtin("   ")
        assert result is None


class TestReactLoop:
    """Test ReAct loop functionality."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_react_empty_input(self):
        """Test react with empty input."""
        shell = VibeShell()
        
        result = await shell.react("")
        assert "Please enter" in result
        
        result = await shell.react("   ")
        assert "Please enter" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_react_invalid_input_type(self):
        """Test react with invalid input type."""
        shell = VibeShell()
        
        with pytest.raises(ValidationError):
            await shell.react(123)  # type: ignore
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @patch.object(VibeShell, 'call_llm_with_fallback')
    @pytest.mark.asyncio
    async def test_react_with_answer(self, mock_call_llm):
        """Test react loop with immediate answer."""
        shell = VibeShell()
        mock_call_llm.return_value = "ANSWER: Here is your answer"
        
        result = await shell.react("test query")
        assert result == "Here is your answer"
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @patch.object(VibeShell, 'call_llm_with_fallback')
    @patch.object(VibeShell, 'execute_action')
    @pytest.mark.asyncio
    async def test_react_with_action(self, mock_execute, mock_call_llm):
        """Test react loop with action execution."""
        shell = VibeShell()
        
        # First call returns action, second returns answer
        mock_call_llm.side_effect = [
            "THOUGHT: Need to check\nACTION: shell(ls)",
            "ANSWER: Here are the files"
        ]
        mock_execute.return_value = "file1.txt file2.txt"
        
        result = await shell.react("list files")
        assert result == "Here are the files"
        mock_execute.assert_called_once()


class TestLLMProviderFallback:
    """Test LLM provider fallback chain."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_no_providers_available(self):
        """Test behavior when no LLM providers are available."""
        shell = VibeShell()
        shell.llm_providers = []
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await shell.call_llm_with_fallback(messages)
        
        assert "No LLM providers available" in result
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @patch.object(VibeShell, '_call_anthropic')
    @pytest.mark.asyncio
    async def test_primary_provider_success(self, mock_anthropic):
        """Test successful call to primary provider."""
        shell = VibeShell()
        mock_client = AsyncMock()
        shell.llm_providers = [LLMProvider("anthropic", mock_client, priority=1)]
        mock_anthropic.return_value = "Success response"
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await shell.call_llm_with_fallback(messages)
        
        assert result == "Success response"
        mock_anthropic.assert_called_once()


class TestInputValidation:
    """Test input validation across methods."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    def test_validation_error_inheritance(self):
        """Test that ValidationError is properly defined."""
        assert issubclass(ValidationError, VibeShellError)
        
        with pytest.raises(VibeShellError):
            raise ValidationError("test error")


class TestIntegration:
    """Integration tests that exercise multiple components."""
    
    @pytest.mark.skipif(not HAS_VIBE_SHELL, reason="vibe_shell not available")
    @pytest.mark.asyncio
    async def test_full_workflow_read_file(self, tmp_path, capsys):
        """Test full workflow: react -> parse -> execute -> result."""
        shell = VibeShell()
        shell.cwd = str(tmp_path)
        
        # Create a test file
        (tmp_path / "notes.txt").write_text("Important note")
        
        # Mock LLM to return read_file action then answer
        with patch.object(VibeShell, 'call_llm_with_fallback') as mock_llm:
            mock_llm.side_effect = [
                'THOUGHT: Read the file\nACTION: read_file(notes.txt)',
                'ANSWER: I found: Important note'
            ]
            
            result = await shell.react("read notes.txt")
            
            assert "Important note" in result
            captured = capsys.readouterr()
            assert "💭" in captured.out  # Thought printed
            assert "⚡" in captured.out  # Action printed


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
