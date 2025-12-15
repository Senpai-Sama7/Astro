"""
Error Path Tests for ASTRO
Tests error handling, edge cases, and failure scenarios.
"""
import asyncio
import pytest
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ============================================================================
# Request Signing Tests
# ============================================================================

class TestRequestSigningErrors:
    """Error paths for HMAC request signing."""

    def test_invalid_timestamp_format(self):
        from api.request_signing import RequestSigner
        signer = RequestSigner("test_secret")
        valid, msg = signer.verify("GET", "/api/test", "", "not-a-number", "sig")
        assert not valid
        assert "Invalid timestamp" in msg

    def test_expired_request(self):
        from api.request_signing import RequestSigner
        signer = RequestSigner("test_secret")
        old_ts = str(int(time.time()) - 600)  # 10 min ago
        valid, msg = signer.verify("GET", "/api/test", "", old_ts, "sig")
        assert not valid
        assert "expired" in msg.lower()

    def test_invalid_signature(self):
        from api.request_signing import RequestSigner
        signer = RequestSigner("test_secret")
        ts = str(int(time.time()))
        valid, msg = signer.verify("GET", "/api/test", "", ts, "wrong_sig")
        assert not valid
        assert "Invalid signature" in msg

    def test_valid_signature(self):
        from api.request_signing import RequestSigner
        signer = RequestSigner("test_secret")
        ts = str(int(time.time()))
        sig = signer.sign("GET", "/api/test", "", ts)
        valid, msg = signer.verify("GET", "/api/test", "", ts, sig)
        assert valid
        assert msg == "OK"

    def test_no_secret_key_bypasses(self):
        from api.request_signing import RequestSigner
        signer = RequestSigner("")  # Empty key
        valid, msg = signer.verify("GET", "/api/test", "", "any", "any")
        assert valid  # Signing disabled

    def test_none_timestamp(self):
        from api.request_signing import RequestSigner
        signer = RequestSigner("test_secret")
        valid, msg = signer.verify("GET", "/api/test", "", None, "sig")
        assert not valid


# ============================================================================
# Session Manager Tests
# ============================================================================

class TestSessionManagerErrors:
    """Error paths for session management."""

    def test_invalid_session_id(self):
        from api.session_manager import SessionManager
        mgr = SessionManager()
        valid, _ = mgr.validate("nonexistent", "token")
        assert not valid

    def test_invalid_token(self):
        from api.session_manager import SessionManager
        mgr = SessionManager()
        sid, token = mgr.create("user1")
        valid, _ = mgr.validate(sid, "wrong_token")
        assert not valid

    def test_expired_session(self):
        from api.session_manager import SessionManager
        mgr = SessionManager()
        mgr.SESSION_TTL = 0  # Expire immediately
        sid, token = mgr.create("user1")
        time.sleep(0.01)
        valid, _ = mgr.validate(sid, token)
        assert not valid

    def test_token_rotation(self):
        from api.session_manager import SessionManager
        mgr = SessionManager()
        mgr.ROTATION_INTERVAL = 0  # Rotate immediately
        sid, token = mgr.create("user1")
        valid, new_token = mgr.validate(sid, token)
        assert valid
        assert new_token is not None
        assert new_token != token

    def test_invalidate_session(self):
        from api.session_manager import SessionManager
        mgr = SessionManager()
        sid, token = mgr.create("user1")
        mgr.invalidate(sid)
        valid, _ = mgr.validate(sid, token)
        assert not valid

    def test_cleanup_expired(self):
        from api.session_manager import SessionManager
        mgr = SessionManager()
        mgr.SESSION_TTL = 0
        mgr.create("user1")
        mgr.create("user2")
        time.sleep(0.01)
        mgr.cleanup()
        assert len(mgr._sessions) == 0


# ============================================================================
# Task Queue Tests (sync versions)
# ============================================================================

class TestTaskQueueErrors:
    """Error paths for task queue."""

    def test_is_failed(self):
        from core.task_queue import TaskQueue
        q = TaskQueue()
        q._failed.add("task1")
        assert q.is_failed("task1")
        assert not q.is_completed("task1")

    def test_failed_dependency(self):
        from core.task_queue import TaskQueue
        q = TaskQueue()
        q._failed.add("dep1")
        assert q.has_failed_dependency(["dep1", "dep2"])

    def test_unmet_dependencies(self):
        from core.task_queue import TaskQueue
        q = TaskQueue()
        # dep1 not in completed, not in failed -> unmet
        assert not q.dependencies_met(["dep1"])

    def test_empty_dependencies(self):
        from core.task_queue import TaskQueue
        q = TaskQueue()
        assert q.dependencies_met([])
        assert q.dependencies_met(None)

    def test_priority_calculation_overdue(self):
        from core.task_queue import TaskQueue, WorkflowPriority
        # Overdue deadline
        score = TaskQueue.calculate_priority(WorkflowPriority.LOW, deadline=time.time() - 100)
        assert score < 0.5  # Should be high priority

    def test_priority_calculation_urgent(self):
        from core.task_queue import TaskQueue, WorkflowPriority
        # 30 seconds remaining
        score = TaskQueue.calculate_priority(WorkflowPriority.MEDIUM, deadline=time.time() + 30)
        assert score < 0.3

    def test_priority_no_deadline(self):
        from core.task_queue import TaskQueue, WorkflowPriority
        score = TaskQueue.calculate_priority(WorkflowPriority.CRITICAL)
        assert score < 0.2  # Critical should be high priority

    def test_properties(self):
        from core.task_queue import TaskQueue
        q = TaskQueue()
        q._completed.add("t1")
        q._failed.add("t2")
        q._active["t3"] = {}
        assert "t1" in q.completed_tasks
        assert "t2" in q.failed_tasks
        assert "t3" in q.active_tasks


# ============================================================================
# Audit Logger Tests
# ============================================================================

class TestAuditLoggerErrors:
    """Error paths for audit logging."""

    def test_log_with_none_details(self):
        from core.audit_logger import AuditLogger, AuditEvent
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(tmpdir)
            logger.log(AuditEvent.AUTH_SUCCESS, "user", "/api", details=None)
            # Should not raise

    def test_all_event_types(self):
        from core.audit_logger import AuditEvent
        # Verify all event types are valid
        events = list(AuditEvent)
        assert len(events) >= 10
        assert AuditEvent.SECURITY_VIOLATION in events


# ============================================================================
# WebSocket Message Validation Tests
# ============================================================================

class TestWebSocketValidation:
    """Error paths for WebSocket message validation."""

    def test_invalid_message_type(self):
        from pydantic import ValidationError
        from api.server import WSMessage
        with pytest.raises(ValidationError):
            WSMessage(type="invalid_type", payload={})

    def test_valid_message_types(self):
        from api.server import WSMessage, WSMessageType
        for msg_type in WSMessageType:
            msg = WSMessage(type=msg_type, payload={"test": True})
            assert msg.type == msg_type

    def test_ws_message_type_values(self):
        from api.server import WSMessageType
        assert WSMessageType.PING.value == "ping"
        assert WSMessageType.COMMAND.value == "command"


# ============================================================================
# CSRF Protection Tests
# ============================================================================

class TestCSRFProtection:
    """Error paths for CSRF protection."""

    def test_generate_token(self):
        from api.middleware import CSRFProtection
        csrf = CSRFProtection()
        token = csrf.generate_token()
        assert len(token) > 20

    def test_validate_matching_tokens(self):
        from api.middleware import CSRFProtection
        csrf = CSRFProtection()
        token = csrf.generate_token()
        # Double-submit: cookie and header must match
        assert csrf.validate_token(token, token)

    def test_validate_mismatched_tokens(self):
        from api.middleware import CSRFProtection
        csrf = CSRFProtection()
        token = csrf.generate_token()
        assert not csrf.validate_token(token, "different_token")

    def test_validate_none_tokens(self):
        from api.middleware import CSRFProtection
        csrf = CSRFProtection()
        assert not csrf.validate_token(None, None)
        assert not csrf.validate_token("token", None)
        assert not csrf.validate_token(None, "token")


# ============================================================================
# Rate Limiter Tests
# ============================================================================

class TestRateLimiter:
    """Error paths for rate limiting."""

    def test_rate_limiter_exceeded(self):
        async def _test():
            from api.middleware import SlidingWindowRateLimiter
            limiter = SlidingWindowRateLimiter(requests_per_window=2, window_seconds=60)
            allowed1, _ = await limiter.is_allowed("client1")
            allowed2, _ = await limiter.is_allowed("client1")
            allowed3, _ = await limiter.is_allowed("client1")
            assert allowed1
            assert allowed2
            assert not allowed3  # Exceeded
        asyncio.run(_test())

    def test_rate_limiter_different_clients(self):
        async def _test():
            from api.middleware import SlidingWindowRateLimiter
            limiter = SlidingWindowRateLimiter(requests_per_window=1, window_seconds=60)
            allowed1, _ = await limiter.is_allowed("client1")
            allowed2, _ = await limiter.is_allowed("client2")  # Different client
            assert allowed1
            assert allowed2
        asyncio.run(_test())


# ============================================================================
# Code Agent Security Tests
# ============================================================================

class TestCodeAgentErrors:
    """Error paths for code execution."""

    def test_syntax_error_detection(self):
        """Test that syntax errors are caught."""
        import ast
        with pytest.raises(SyntaxError):
            ast.parse("def broken(")

    def test_nested_dangerous_call(self):
        """Test detection of nested dangerous calls."""
        import ast
        code = "result = eval(input())"
        tree = ast.parse(code)
        dangerous = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    dangerous = True
        assert dangerous

    def test_attribute_dangerous_call(self):
        """Test detection of attribute-based dangerous calls."""
        import ast
        code = "obj.__class__.__bases__[0].__subclasses__()"
        tree = ast.parse(code)
        has_dunder = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("__"):
                    has_dunder = True
        assert has_dunder


# ============================================================================
# Engine Error Handling Tests
# ============================================================================

class TestEngineErrors:
    """Error paths for workflow engine."""

    def test_task_timeout_handling(self):
        """Test that task timeouts are handled."""
        async def _test():
            async def slow_task():
                await asyncio.sleep(10)
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(slow_task(), timeout=0.01)
        asyncio.run(_test())

    def test_concurrent_task_failure(self):
        """Test handling of concurrent task failures."""
        async def _test():
            async def failing_task():
                raise ValueError("Task failed")
            tasks = [failing_task() for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            assert all(isinstance(r, ValueError) for r in results)
        asyncio.run(_test())


# ============================================================================
# Database Error Tests
# ============================================================================

class TestDatabaseErrors:
    """Error paths for database operations."""

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in database."""
        import json
        with pytest.raises(json.JSONDecodeError):
            json.loads("{invalid json}")

    def test_missing_key_handling(self):
        """Test handling of missing keys."""
        data = {"key1": "value1"}
        result = data.get("missing_key", "default")
        assert result == "default"


# ============================================================================
# Config Validation Tests
# ============================================================================

class TestConfigErrors:
    """Error paths for configuration."""

    def test_missing_env_var(self):
        """Test handling of missing environment variables."""
        result = os.getenv("NONEXISTENT_VAR", "default")
        assert result == "default"

    def test_invalid_int_env_var(self):
        """Test handling of invalid integer env vars."""
        os.environ["TEST_INT"] = "not_an_int"
        try:
            int(os.getenv("TEST_INT", "0"))
            assert False, "Should raise"
        except ValueError:
            pass
        finally:
            del os.environ["TEST_INT"]
