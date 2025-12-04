# ASTRO Security & Quality Implementation Checklist

**Created:** December 4, 2025  
**Status:** 6/9 Complete - Security Items Done ✅

---

## Summary

| # | Item | Priority | Status |
|---|------|----------|--------|
| 1 | Pin Dependencies | CRITICAL | ✅ DONE |
| 2 | CSRF Protection | HIGH | ✅ DONE |
| 3 | WebSocket Validation | MEDIUM | ✅ DONE |
| 4 | Audit Logging | HIGH | ✅ DONE |
| 5 | Request Signing (HMAC) | HIGH | ✅ DONE |
| 6 | Session Token Rotation | MEDIUM | ✅ DONE |
| 7 | Refactor engine.py | MEDIUM | 🔲 TODO |
| 8 | Refactor server.py | MEDIUM | 🔲 TODO |
| 9 | Add Test Cases | MEDIUM | 🔲 TODO |

---

## ✅ COMPLETED ITEMS

### 1. Pin Unpinned Dependencies ✅
**File:** `requirements.txt`
```diff
- torch
+ torch==2.5.1
- duckduckgo-search  
+ duckduckgo-search==6.3.5
```

### 2. CSRF Protection ✅
**File:** `src/api/middleware.py`
- Added `CSRFProtection` class with double-submit cookie pattern
- Added `CSRFMiddleware` to middleware chain
- Generates cryptographically secure tokens
- Validates X-CSRF-Token header on POST/PUT/DELETE
- Exempts API key authenticated requests

### 3. WebSocket Input Validation ✅
**File:** `src/api/server.py`
- Added `WSMessageType` enum for valid message types
- Added `WSMessage` Pydantic model with validation
- 64KB message size limit
- Proper error responses for invalid messages

### 4. Audit Logging ✅
**File:** `src/core/audit_logger.py` (NEW)
- `AuditEvent` enum with event types
- `AuditLogger` class writing JSONL to logs/audit.jsonl
- Integrated into `AuthenticationMiddleware`
- Logs auth success/failure with IP, request_id, details

### 5. Request Signing (HMAC) ✅
**File:** `src/api/request_signing.py` (NEW)
- `RequestSigner` class with HMAC-SHA256
- 5-minute timestamp tolerance
- `RequestSigningMiddleware` validates X-Timestamp and X-Signature
- Enable via `ASTRO_SIGNING_KEY` environment variable

### 6. Session Token Rotation ✅
**File:** `src/api/session_manager.py` (NEW)
- `SessionManager` class with token rotation
- 15-minute rotation interval
- 24-hour session TTL
- Secure token generation with `secrets` module

---

## 🔲 REMAINING ITEMS (Code Quality)

### 7. Refactor engine.py - Extract TaskQueue
**Priority:** MEDIUM  
**Effort:** 4-5 hours  
**Risk:** Medium (core component)

**Why:** 600+ line file violates single responsibility principle.

**Implementation:**
```python
# src/core/task_queue.py
import asyncio
from typing import Dict, Set
from dataclasses import dataclass

class TaskQueue:
    """Thread-safe priority task queue with dependency tracking."""
    
    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._active: Dict[str, 'Task'] = {}
        self._lock = asyncio.Lock()
    
    async def enqueue(self, task, priority_score: float):
        await self._queue.put((priority_score, task))
    
    async def dequeue(self):
        return await self._queue.get()
    
    async def mark_completed(self, task_id: str):
        async with self._lock:
            self._completed.add(task_id)
            self._active.pop(task_id, None)
    
    async def mark_failed(self, task_id: str):
        async with self._lock:
            self._failed.add(task_id)
            self._active.pop(task_id, None)
    
    def dependencies_met(self, task) -> bool:
        return all(dep in self._completed for dep in (task.dependencies or []))
    
    @property
    def qsize(self) -> int:
        return self._queue.qsize()
```

**engine.py changes:**
- Import TaskQueue
- Replace self.task_queue, self.completed_tasks, self.failed_tasks with TaskQueue instance
- Update methods to use TaskQueue API

---

### 8. Refactor server.py - Split into Routers
**Priority:** MEDIUM  
**Effort:** 3-4 hours  
**Risk:** Low (additive change)

**Why:** 700+ line file is hard to maintain.

**Target Structure:**
```
src/api/
├── server.py          # Main app, lifespan only
├── routers/
│   ├── __init__.py
│   ├── system.py      # /api/system/*
│   ├── agents.py      # /api/agents/*
│   ├── workflows.py   # /api/workflows/*
│   ├── chat.py        # /api/chat/*
│   ├── knowledge.py   # /api/knowledge/*
│   └── files.py       # /api/files/*
```

**Example router:**
```python
# src/api/routers/system.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")
async def get_status():
    ...
```

**server.py changes:**
```python
from api.routers import system, agents, workflows, chat
app.include_router(system.router)
app.include_router(agents.router)
# etc.
```

---

### 9. Add Missing Test Cases
**Priority:** MEDIUM  
**Effort:** 4-6 hours  
**Risk:** None (additive)

**Coverage Gaps:**
- API error handling
- WebSocket edge cases
- Agent timeouts
- Database failures

**Test file structure:**
```
tests/
├── test_api_errors.py      # NEW
├── test_websocket.py       # NEW  
├── test_agent_errors.py    # NEW
└── test_session.py         # NEW
```

**Example tests:**
```python
# tests/test_api_errors.py
def test_invalid_workflow_returns_404(client):
    response = client.get("/api/workflows/nonexistent")
    assert response.status_code == 404

def test_rate_limit_returns_429(client):
    for _ in range(150):
        client.get("/api/system/status")
    assert client.get("/api/system/status").status_code == 429
```

---

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | Modified | Pinned torch, duckduckgo-search |
| `src/api/middleware.py` | Modified | Added CSRF, audit logging |
| `src/api/server.py` | Modified | Added WebSocket validation |
| `src/core/audit_logger.py` | Created | Audit logging system |
| `src/api/request_signing.py` | Created | HMAC request signing |
| `src/api/session_manager.py` | Created | Session token rotation |

---

## Verification

```bash
# Test the changes
cd /home/donovan/Projects/AI/Astro
python -m pytest tests/test_security.py -v

# Check for syntax errors
python -m py_compile src/api/middleware.py
python -m py_compile src/core/audit_logger.py
python -m py_compile src/api/request_signing.py
python -m py_compile src/api/session_manager.py

# Run full test suite
python -m pytest tests/ -v
```

---

## Environment Variables

New environment variables added:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ASTRO_SIGNING_KEY` | HMAC signing secret | (disabled if empty) |
| `ASTRO_ENV` | Environment (production/development) | development |

---

## Security Checklist

- [x] All dependencies pinned
- [x] CSRF protection on state-changing endpoints
- [x] WebSocket input validation
- [x] Audit logging for compliance
- [x] Request signing (HMAC) available
- [x] Session token rotation
- [ ] Refactor large files (optional, code quality)
- [ ] Additional test coverage (optional)

---

*Last Updated: December 4, 2025*
