"""Tests for skills system."""

from src.skills import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission


class TestSkill:
    """Test base skill functionality."""
    
    def test_skill_creation(self):
        """Test creating a skill."""
        config = SkillConfig(
            name="test_skill",
            description="A test skill",
            permissions=[SkillPermission.READ_ONLY]
        )
        
        class TestSkill(Skill):
            async def execute(self, params, context):
                return SkillResult.ok("Success")
        
        skill = TestSkill(config)
        assert skill.name == "test_skill"
        assert skill.has_permission(SkillPermission.READ_ONLY)
        assert not skill.has_permission(SkillPermission.FILE_SYSTEM)
    
    def test_skill_permissions(self):
        """Test permission checking."""
        config = SkillConfig(
            name="test",
            description="Test",
            permissions=[SkillPermission.FILE_SYSTEM, SkillPermission.NETWORK]
        )
        
        class TestSkill(Skill):
            async def execute(self, params, context):
                return SkillResult.ok("Done")
        
        skill = TestSkill(config)
        assert skill.has_permission(SkillPermission.FILE_SYSTEM)
        assert skill.has_permission(SkillPermission.NETWORK)
        assert not skill.has_permission(SkillPermission.SYSTEM)


class TestSkillResult:
    """Test skill results."""
    
    def test_ok_result(self):
        """Test successful result."""
        result = SkillResult.ok("It worked!", data={"key": "value"})
        assert result.success is True
        assert result.message == "It worked!"
        assert result.data["key"] == "value"
    
    def test_error_result(self):
        """Test error result."""
        result = SkillResult.error("Something failed")
        assert result.success is False
        assert result.message == "Something failed"


class TestSkillContext:
    """Test skill context."""
    
    def test_context_creation(self):
        """Test creating context."""
        context = SkillContext(
            user_id="user123",
            session_id="session456",
            working_directory="/tmp"
        )
        
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.working_directory == "/tmp"
    
    def test_memory_operations(self):
        """Test memory get/set."""
        context = SkillContext(
            user_id="user",
            session_id="session",
            working_directory="/tmp"
        )
        
        # Set and get
        context.set_memory("key", "value")
        assert context.get_memory("key") == "value"
        
        # Get missing with default
        assert context.get_memory("missing", "default") == "default"
        assert context.get_memory("missing") is None
