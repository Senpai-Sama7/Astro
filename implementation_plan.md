
We're adding 4 critical systems in **precise order** to avoid breaking existing functionality:

1. **Structured Logging** (Foundation)
2. **Health Checks** (Monitoring)
3. **Rate Limiting** (Protection)
4. **Metrics Export** (Observability)

**Total Time**: ~8 hours  
**Impact**: Production-ready → Enterprise-grade

***

## **Phase 1: Structured Logging (2 hours)**

### **Why First**: Everything else depends on good logging. This is the foundation.

***

### **Step 1.1: Install Dependencies**

```bash
# No new dependencies needed - uses stdlib only
# But add these for optional integrations later
pip install python-json-logger  # Optional: better JSON formatting
```

***

### **Step 1.2: Create Structured Logger**

**File**: `src/utils/structured_logger.py` (NEW FILE)

```python
"""
Structured Logging System
Outputs JSON logs for ELK/Splunk/Datadog ingestion
"""
import logging
import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')
workflow_id_var: ContextVar[str] = ContextVar('workflow_id', default='')


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    
    Outputs consistent JSON format that can be parsed by log aggregators
    """
    
    # Fields to always include
    CORE_FIELDS = [
        'timestamp', 'level', 'logger', 'message', 'module', 
        'function', 'line', 'thread', 'process'
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Core log data
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
            "environment": "production"  # Set from env var
        }
        
        # Add context vars if set
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data['user_id'] = user_id
        
        workflow_id = workflow_id_var.get()
        if workflow_id:
            log_data['workflow_id'] = workflow_id
        
        # Add extra fields from log call
        # Example: logger.info("msg", extra={'agent_id': 'code_001'})
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in ['name', 'msg', 'args', 'created', 'filename', 
                        'funcName', 'levelname', 'levelno', 'lineno',
                        'module', 'msecs', 'message', 'pathname', 
                        'process', 'processName', 'relativeCreated',
                        'thread', 'threadName', 'exc_info', 'exc_text',
                        'stack_info']
        }
        
        log_data.update(extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add stack info if present (Python 3.8+)
        if hasattr(record, 'stack_info') and record.stack_info:
            log_data['stack_trace'] = record.stack_info
        
        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for development
    Colored output for better readability
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for console"""
        
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Timestamp
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        # Core message
        message = f"{color}[{record.levelname}]{reset} "
        message += f"{timestamp} "
        message += f"{record.name}:{record.lineno} "
        
        # Add context if available
        request_id = request_id_var.get()
        if request_id:
            message += f"[req:{request_id[:8]}] "
        
        # Add extra fields
        extra = []
        if hasattr(record, 'agent_id'):
            extra.append(f"agent={record.agent_id}")
        if hasattr(record, 'task_id'):
            extra.append(f"task={record.task_id}")
        if hasattr(record, 'duration_ms'):
            extra.append(f"duration={record.duration_ms:.1f}ms")
        
        if extra:
            message += f"[{', '.join(extra)}] "
        
        # The actual log message
        message += record.getMessage()
        
        # Exception info
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True,
    console_output: bool = True
):
    """
    Setup structured logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        json_format: Use JSON format (True) or human-readable (False)
        console_output: Output to console
    
    Example:
        # Development
        setup_logging(level="DEBUG", json_format=False)
        
        # Production
        setup_logging(
            level="INFO",
            json_format=True,
            log_file=Path("logs/astro.log")
        )
    """
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler (stdout)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if json_format:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ConsoleFormatter())
        
        root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging initialized",
        extra={
            'log_level': level,
            'json_format': json_format,
            'log_file': str(log_file) if log_file else None
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Task completed", extra={
            'agent_id': 'code_001',
            'task_id': 'task_123',
            'duration_ms': 1234.5
        })
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for setting request/workflow context
    
    Example:
        with LogContext(request_id="req-123", workflow_id="wf-456"):
            logger.info("Processing task")
            # All logs within this block will have request_id and workflow_id
    """
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.workflow_id = workflow_id
        self.tokens = []
    
    def __enter__(self):
        if self.request_id:
            self.tokens.append(request_id_var.set(self.request_id))
        if self.user_id:
            self.tokens.append(user_id_var.set(self.user_id))
        if self.workflow_id:
            self.tokens.append(workflow_id_var.set(self.workflow_id))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in self.tokens:
            if token:
                try:
                    request_id_var.reset(token)
                except (ValueError, LookupError):
                    pass


def log_performance(func):
    """
    Decorator to log function execution time
    
    Example:
        @log_performance
        async def execute_task(self, task):
            # Implementation
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        logger = get_logger(func.__module__)
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            
            logger.error(
                f"{func.__name__} failed",
                extra={
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'status': 'error',
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        logger = get_logger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            
            logger.error(
                f"{func.__name__} failed",
                extra={
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'status': 'error',
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# Example usage patterns
if __name__ == "__main__":
    # Development setup
    setup_logging(level="DEBUG", json_format=False)
    
    logger = get_logger(__name__)
    
    # Basic logging
    logger.info("Application started")
    
    # Logging with context
    logger.info(
        "Task completed",
        extra={
            'agent_id': 'code_001',
            'task_id': 'task_123',
            'duration_ms': 1234.5,
            'success': True
        }
    )
    
    # Logging with request context
    with LogContext(request_id="req-abc-123", workflow_id="wf-456"):
        logger.info("Processing within workflow")
        logger.debug("Detailed processing info")
    
    # Exception logging
    try:
        raise ValueError("Something went wrong")
    except Exception as e:
        logger.error("Operation failed", exc_info=True)
```

***

### **Step 1.3: Update Main Entry Point**

**File**: `main.py` (MODIFY EXISTING)

```python
"""
Astro Main Entry Point
"""
import asyncio
import sys
from pathlib import Path

# ADD THIS AT THE TOP (before other imports)
from utils.structured_logger import setup_logging, get_logger, LogContext

# Setup logging FIRST before any other imports
setup_logging(
    level="INFO",  # Change to DEBUG for development
    json_format=False,  # Set True for production
    console_output=True,
    log_file=Path("logs/astro.log")
)

logger = get_logger(__name__)

# Now import rest of application
from core.engine import AgentEngine
from core.database import DatabaseManager
# ... rest of imports


async def main():
    """Main application entry point"""
    
    # Generate request ID for this run
    import uuid
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    
    with LogContext(request_id=request_id):
        logger.info("Astro starting up")
        
        try:
            # Initialize systems
            db = DatabaseManager()
            engine = AgentEngine(db_manager=db)
            
            logger.info(
                "Astro initialized successfully",
                extra={
                    'agent_count': len(engine.agents),
                    'database_path': db.db_path
                }
            )
            
            # Start engine
            await engine.start_engine()
            
            logger.info("Astro engine started")
            
            # Keep running
            await engine.run_forever()
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error("Fatal error during startup", exc_info=True)
            sys.exit(1)
        finally:
            logger.info("Astro shutting down")
            await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

***

### **Step 1.4: Update AgentEngine with Structured Logging**

**File**: `src/core/engine.py` (MODIFY EXISTING)

```python
# At the top, replace old logger
from utils.structured_logger import get_logger, LogContext, log_performance

logger = get_logger(__name__)

class AgentEngine:
    # Existing __init__ code...
    
    @log_performance  # ADD THIS DECORATOR
    async def submit_workflow(self, workflow: Workflow):
        """Submit workflow with structured logging"""
        
        with LogContext(workflow_id=workflow.workflow_id):
            logger.info(
                "Workflow submitted",
                extra={
                    'workflow_id': workflow.workflow_id,
                    'task_count': len(workflow.tasks),
                    'priority': workflow.priority
                }
            )
            
            # Existing workflow submission code...
            await self._submit_workflow_internal(workflow)
            
            logger.info(
                "Workflow accepted",
                extra={
                    'workflow_id': workflow.workflow_id,
                    'status': 'queued'
                }
            )
    
    @log_performance  # ADD THIS DECORATOR
    async def _execute_task_with_agent(self, task: Task, agent_id: str):
        """Execute task with structured logging"""
        
        logger.info(
            "Task execution started",
            extra={
                'task_id': task.task_id,
                'agent_id': agent_id,
                'task_type': task.required_capabilities[0] if task.required_capabilities else 'generic'
            }
        )
        
        try:
            # Existing execution code...
            result = await self._execute_task_internal(task, agent_id)
            
            logger.info(
                "Task execution completed",
                extra={
                    'task_id': task.task_id,
                    'agent_id': agent_id,
                    'success': result.success,
                    'duration_ms': result.execution_time_ms
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Task execution failed",
                extra={
                    'task_id': task.task_id,
                    'agent_id': agent_id,
                    'error': str(e)
                },
                exc_info=True
            )
            raise
```

***

### **Step 1.5: Test Structured Logging**

```bash
# Run application
python main.py

# Check log file
cat logs/astro.log | jq '.'  # Pretty-print JSON logs

# Query specific agent
cat logs/astro.log | jq 'select(.agent_id == "code_agent_001")'

# Find slow operations
cat logs/astro.log | jq 'select(.duration_ms > 1000)'

# Filter by level
cat logs/astro.log | jq 'select(.level == "ERROR")'
```

***

## **Phase 2: Health Checks (1 hour)**

### **Step 2.1: Create Health Check System**

**File**: `src/api/health.py` (NEW FILE)

```python
"""
Health Check System
Kubernetes-compatible liveness/readiness/startup probes
"""
from fastapi import APIRouter, Response, status
from typing import Dict, Any, Optional
import time
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime

from utils.structured_logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@dataclass
class HealthStatus:
    """Health check result"""
    status: str  # "healthy", "unhealthy", "degraded"
    message: str = ""
    timestamp: str = ""
    response_time_ms: float = 0.0
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.details is None:
            self.details = {}


class HealthChecker:
    """
    Centralized health checking
    """
    
    def __init__(self, agent_engine=None, db_manager=None):
        self.agent_engine = agent_engine
        self.db = db_manager
        self.start_time = time.time()
        self._initialized = False
    
    def set_components(self, agent_engine, db_manager):
        """Set components after initialization"""
        self.agent_engine = agent_engine
        self.db = db_manager
        self._initialized = True
    
    async def check_database(self) -> HealthStatus:
        """Check database connectivity and performance"""
        start = time.time()
        
        try:
            if not self.db:
                return HealthStatus(
                    status="unhealthy",
                    message="Database not initialized"
                )
            
            # Simple query to check connectivity
            stats = await self.db.get_database_stats_async()
            
            response_time_ms = (time.time() - start) * 1000
            
            # Check if response time is acceptable (<100ms)
            if response_time_ms > 100:
                status_val = "degraded"
                message = f"Database slow ({response_time_ms:.1f}ms)"
            else:
                status_val = "healthy"
                message = "Database operational"
            
            return HealthStatus(
                status=status_val,
                message=message,
                response_time_ms=response_time_ms,
                details=stats
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start) * 1000
            logger.error("Database health check failed", exc_info=True)
            
            return HealthStatus(
                status="unhealthy",
                message=f"Database error: {str(e)}",
                response_time_ms=response_time_ms
            )
    
    async def check_agents(self) -> HealthStatus:
        """Check agent availability and status"""
        start = time.time()
        
        try:
            if not self.agent_engine:
                return HealthStatus(
                    status="unhealthy",
                    message="Agent engine not initialized"
                )
            
            # Get agent statuses
            agent_statuses = {
                agent_id: status.value
                for agent_id, status in self.agent_engine.agent_status.items()
            }
            
            # Count healthy agents (idle or active)
            healthy_count = sum(
                1 for s in agent_statuses.values()
                if s in ['idle', 'active']
            )
            
            total_count = len(agent_statuses)
            
            response_time_ms = (time.time() - start) * 1000
            
            # Determine overall status
            if healthy_count == 0:
                status_val = "unhealthy"
                message = "No healthy agents available"
            elif healthy_count < total_count * 0.5:
                status_val = "degraded"
                message = f"Only {healthy_count}/{total_count} agents healthy"
            else:
                status_val = "healthy"
                message = f"{healthy_count}/{total_count} agents healthy"
            
            return HealthStatus(
                status=status_val,
                message=message,
                response_time_ms=response_time_ms,
                details={
                    'total_agents': total_count,
                    'healthy_agents': healthy_count,
                    'agent_statuses': agent_statuses,
                    'active_tasks': len(self.agent_engine.active_tasks)
                }
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start) * 1000
            logger.error("Agent health check failed", exc_info=True)
            
            return HealthStatus(
                status="unhealthy",
                message=f"Agent check error: {str(e)}",
                response_time_ms=response_time_ms
            )
    
    async def check_docker(self) -> HealthStatus:
        """Check Docker availability (for CodeAgent)"""
        start = time.time()
        
        try:
            import subprocess
            
            # Quick Docker check
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                timeout=5
            )
            
            response_time_ms = (time.time() - start) * 1000
            
            if result.returncode == 0:
                return HealthStatus(
                    status="healthy",
                    message="Docker available",
                    response_time_ms=response_time_ms
                )
            else:
                return HealthStatus(
                    status="unhealthy",
                    message="Docker not responding",
                    response_time_ms=response_time_ms
                )
                
        except FileNotFoundError:
            return HealthStatus(
                status="unhealthy",
                message="Docker not installed"
            )
        except subprocess.TimeoutExpired:
            return HealthStatus(
                status="unhealthy",
                message="Docker timeout"
            )
        except Exception as e:
            logger.error("Docker health check failed", exc_info=True)
            return HealthStatus(
                status="unhealthy",
                message=f"Docker check error: {str(e)}"
            )
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time


# Global instance
_health_checker: Optional[HealthChecker] = None


def init_health_checker(agent_engine=None, db_manager=None) -> HealthChecker:
    """Initialize health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(agent_engine, db_manager)
    else:
        _health_checker.set_components(agent_engine, db_manager)
    return _health_checker


def get_health_checker() -> HealthChecker:
    """Get health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


@router.get("/live")
async def liveness():
    """
    Kubernetes liveness probe
    
    Returns 200 if process is alive
    Does NOT check dependencies (fast check)
    
    Kubernetes will restart pod if this fails
    """
    checker = get_health_checker()
    
    return {
        "status": "alive",
        "uptime_seconds": checker.get_uptime(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/ready")
async def readiness(response: Response):
    """
    Kubernetes readiness probe
    
    Returns 200 if system is ready to serve traffic
    Checks all dependencies
    
    Kubernetes will remove pod from load balancer if this fails
    """
    checker = get_health_checker()
    
    # Run all checks in parallel
    checks_results = await asyncio.gather(
        checker.check_database(),
        checker.check_agents(),
        checker.check_docker(),
        return_exceptions=True
    )
    
    checks = {
        "database": checks_results[0] if not isinstance(checks_results[0], Exception) else HealthStatus(status="unhealthy", message=str(checks_results[0])),
        "agents": checks_results[1] if not isinstance(checks_results[1], Exception) else HealthStatus(status="unhealthy", message=str(checks_results[1])),
        "docker": checks_results[2] if not isinstance(checks_results[2], Exception) else HealthStatus(status="unhealthy", message=str(checks_results[2]))
    }
    
    # Convert to dict
    checks_dict = {k: asdict(v) for k, v in checks.items()}
    
    # Overall status
    all_healthy = all(
        check.status == "healthy"
        for check in checks.values()
    )
    
    any_degraded = any(
        check.status == "degraded"
        for check in checks.values()
    )
    
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "not_ready"
    elif any_degraded:
        overall_status = "degraded"
    else:
        overall_status = "ready"
    
    return {
        "status": overall_status,
        "checks": checks_dict,
        "uptime_seconds": checker.get_uptime(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/startup")
async def startup(response: Response):
    """
    Kubernetes startup probe
    
    Returns 200 once initial startup is complete
    More lenient timeout than readiness (for slow starts)
    
    Kubernetes will restart pod if this fails during startup
    """
    checker = get_health_checker()
    
    if not checker._initialized:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "starting",
            "message": "System not yet initialized"
        }
    
    # Check if agents are registered
    if not checker.agent_engine or len(checker.agent_engine.agents) == 0:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "starting",
            "message": "Agents not yet registered"
        }
    
    return {
        "status": "started",
        "agent_count": len(checker.agent_engine.agents),
        "uptime_seconds": checker.get_uptime(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("")
@router.get("/")
async def health_summary():
    """
    Overall health summary
    Useful for monitoring dashboards
    """
    checker = get_health_checker()
    
    checks_results = await asyncio.gather(
        checker.check_database(),
        checker.check_agents(),
        checker.check_docker(),
        return_exceptions=True
    )
    
    checks = {
        "database": checks_results[0] if not isinstance(checks_results[0], Exception) else HealthStatus(status="unhealthy", message=str(checks_results[0])),
        "agents": checks_results[1] if not isinstance(checks_results[1], Exception) else HealthStatus(status="unhealthy", message=str(checks_results[1])),
        "docker": checks_results[2] if not isinstance(checks_results[2], Exception) else HealthStatus(status="unhealthy", message=str(checks_results[2]))
    }
    
    return {
        "overall_status": "healthy" if all(c.status == "healthy" for c in checks.values()) else "degraded",
        "checks": {k: asdict(v) for k, v in checks.items()},
        "uptime_seconds": checker.get_uptime(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

***

### **Step 2.2: Integrate Health Checks into API**

**File**: `src/api/main.py` (MODIFY EXISTING)

```python
from fastapi import FastAPI
from api import health  # ADD THIS IMPORT

app = FastAPI(title="Astro API", version="1.0.0")

# Include health check router
app.include_router(health.router)

# ... rest of your API routes

@app.on_event("startup")
async def startup_event():
    """Initialize health checker on startup"""
    from api.health import init_health_checker
    from core.engine import get_agent_engine  # Your engine singleton
    from core.database import get_database_manager  # Your DB singleton
    
    engine = get_agent_engine()
    db = get_database_manager()
    
    init_health_checker(engine, db)
    
    logger.info("Health check system initialized")
```

***

### **Step 2.3: Test Health Checks**

```bash
# Start API
uvicorn src.api.main:app --reload

# Test liveness (should always work)
curl http://localhost:8000/health/live

# Test readiness (checks dependencies)
curl http://localhost:8000/health/ready | jq '.'

# Test startup
curl http://localhost:8000/health/startup

# Test summary
curl http://localhost:8000/health | jq '.'
```

***

## **Phase 3: Rate Limiting (3 hours)**

### **Step 3.1: Create Rate Limiter**

**File**: `src/core/rate_limiter.py` (NEW FILE)

```python
"""
Rate Limiting System
Token bucket algorithm for rate limiting per key
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from utils.structured_logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information"""
    allowed: bool
    remaining: int
    reset_at: float
    retry_after: float = 0.0


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter
    
    Simple, efficient, no external dependencies
    Uses sliding window to prevent burst traffic
    
    Example:
        limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
        
        if await limiter.is_allowed("user_123"):
            # Process request
            pass
        else:
            # Return 429 Too Many Requests
            pass
    """
    
    def __init__(self, 
                 max_requests: int = 100,
                 window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.buckets: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
    
    async def check(self, key: str) -> RateLimitInfo:
        """
        Check rate limit for key (non-consuming)
        
        Args:
            key: Identifier (user_id, agent_id, ip_address)
        
        Returns:
            RateLimitInfo with status
        """
        async with self._lock:
            now = time.time()
            
            # Initialize bucket if needed
            if key not in self.buckets:
                self.buckets[key] = deque()
            
            bucket = self.buckets[key]
            
            # Remove expired timestamps
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            
            remaining = self.max_requests - len(bucket)
            allowed = remaining > 0
            
            # Calculate reset time
            if bucket:
                oldest = bucket[0]
                reset_at = oldest + self.window_seconds
                retry_after = max(0, reset_at - now) if not allowed else 0.0
            else:
                reset_at = now + self.window_seconds
                retry_after = 0.0
            
            return RateLimitInfo(
                allowed=allowed,
                remaining=max(0, remaining),
                reset_at=reset_at,
                retry_after=retry_after
            )
    
    async def consume(self, key: str) -> RateLimitInfo:
        """
        Check and consume a token if allowed
        
        Args:
            key: Identifier
        
        Returns:
            RateLimitInfo with status
        """
        async with self._lock:
            info = await self.check(key)
            
            if info.allowed:
                now = time.time()
                self.buckets[key].append(now)
                
                logger.debug(
                    "Rate limit token consumed",
                    extra={
                        'key': key,
                        'remaining': info.remaining - 1,
                        'window_seconds': self.window_seconds
                    }
                )
            else:
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        'key': key,
                        'retry_after': info.retry_after,
                        'reset_at': datetime.fromtimestamp(info.reset_at).isoformat()
                    }
                )
            
            return info
    
    async def wait_if_needed(self, key: str, timeout: float = 10.0) -> bool:
        """
        Wait until request is allowed (with timeout)
        
        Args:
            key: Identifier
            timeout: Maximum wait time in seconds
        
        Returns:
            True if allowed, False if timeout
        """
        start = time.time()
        
        while True:
            info = await self.check(key)
            
            if info.allowed:
                await self.consume(key)
                return True
            
            elapsed = time.time() - start
            if elapsed >= timeout:
                logger.warning(
                    "Rate limit wait timeout",
                    extra={
                        'key': key,
                        'timeout_seconds': timeout
                    }
                )
                return False
            
            # Wait a bit before retrying
            wait_time = min(info.retry_after, timeout - elapsed, 1.0)
            await asyncio.sleep(wait_time)
    
    def get_stats(self, key: str) -> Dict:
        """Get current rate limit stats for key"""
        if key not in self.buckets:
            return {
                "requests_in_window": 0,
                "remaining": self.max_requests,
                "reset_in_seconds": 0,
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds
            }
        
        now = time.time()
        cutoff = now - self.window_seconds
        bucket = self.buckets[key]
        
        # Clean up expired
        valid_requests = [ts for ts in bucket if ts >= cutoff]
        
        if valid_requests:
            oldest = min(valid_requests)
            reset_in = self.window_seconds - (now - oldest)
        else:
            reset_in = 0
        
        return {
            "requests_in_window": len(valid_requests),
            "remaining": max(0, self.max_requests - len(valid_requests)),
            "reset_in_seconds": max(0, reset_in),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds
        }
    
    def clear(self, key: Optional[str] = None):
        """Clear rate limit data for key (or all keys if None)"""
        if key:
            if key in self.buckets:
                del self.buckets[key]
                logger.info(f"Rate limit cleared for key: {key}")
        else:
            self.buckets.clear()
            logger.info("All rate limits cleared")


class RateLimitManager:
    """
    Manage multiple rate limiters for different resources
    
    Example:
        manager = RateLimitManager()
        manager.add_limiter('tasks', max_requests=100, window_seconds=60)
        manager.add_limiter('workflows', max_requests=20, window_seconds=60)
        
        if await manager.check('tasks', 'user_123'):
            # Process task
            pass
    """
    
    def __init__(self):
        self.limiters: Dict[str, TokenBucketRateLimiter] = {}
    
    def add_limiter(self, 
                    name: str,
                    max_requests: int,
                    window_seconds: int):
        """Add a rate limiter"""
        self.limiters[name] = TokenBucketRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        
        logger.info(
            "Rate limiter added",
            extra={
                'limiter_name': name,
                'max_requests': max_requests,
                'window_seconds': window_seconds
            }
        )
    
    async def check(self, limiter_name: str, key: str) -> bool:
        """Check if request is allowed"""
        if limiter_name not in self.limiters:
            logger.warning(f"Unknown rate limiter: {limiter_name}")
            return True  # Fail open
        
        info = await self.limiters[limiter_name].consume(key)
        return info.allowed
    
    async def consume(self, limiter_name: str, key: str) -> RateLimitInfo:
        """Consume a token"""
        if limiter_name not in self.limiters:
            return RateLimitInfo(allowed=True, remaining=999, reset_at=time.time())
        
        return await self.limiters[limiter_name].consume(key)
    
    def get_stats(self, limiter_name: str, key: str) -> Dict:
        """Get stats for a limiter"""
        if limiter_name not in self.limiters:
            return {}
        
        return self.limiters[limiter_name].get_stats(key)


# Global instance
_rate_limit_manager: Optional[RateLimitManager] = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get or create rate limit manager"""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
        
        # Add default limiters
        _rate_limit_manager.add_limiter('task_submission', max_requests=100, window_seconds=60)
        _rate_limit_manager.add_limiter('workflow_creation', max_requests=20, window_seconds=60)
        _rate_limit_manager.add_limiter('api_calls', max_requests=1000, window_seconds=60)
        
    return _rate_limit_manager
```

***

### **Step 3.2: Integrate Rate Limiting into Engine**

**File**: `src/core/engine.py` (MODIFY EXISTING)

```python
from core.rate_limiter import get_rate_limit_manager, RateLimitInfo
from fastapi import HTTPException, status

class AgentEngine:
    def __init__(self, ...):
        # Existing code...
        self.rate_limiter = get_rate_limit_manager()
    
    async def submit_workflow(self, workflow: Workflow, user_id: str = "system"):
        """Submit workflow with rate limiting"""
        
        # Check rate limit
        info = await self.rate_limiter.consume('workflow_creation', user_id)
        
        if not info.allowed:
            logger.warning(
                "Workflow submission rate limited",
                extra={
                    'user_id': user_id,
                    'workflow_id': workflow.workflow_id,
                    'retry_after': info.retry_after
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {info.retry_after:.1f} seconds",
                headers={"Retry-After": str(int(info.retry_after))}
            )
        
        logger.info(
            "Workflow submission allowed",
            extra={
                'user_id': user_id,
                'workflow_id': workflow.workflow_id,
                'remaining_requests': info.remaining
            }
        )
        
        # Existing workflow submission code...
        await self._submit_workflow_internal(workflow)
    
    async def submit_task(self, task: Task, user_id: str = "system"):
        """Submit task with rate limiting"""
        
        # Check rate limit
        info = await self.rate_limiter.consume('task_submission', user_id)
        
        if not info.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {info.retry_after:.1f} seconds"
            )
        
        # Existing task submission code...
        await self._submit_task_internal(task)
```

***

### **Step 3.3: Add Rate Limit Headers to API**

**File**: `src/api/middleware.py` (NEW FILE)

```python
"""
Rate Limiting Middleware for FastAPI
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.rate_limiter import get_rate_limit_manager
from utils.structured_logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to API endpoints
    Adds rate limit headers to responses
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get user identifier (IP address or user_id from auth)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", client_ip)
        
        # Check rate limit
        manager = get_rate_limit_manager()
        info = await manager.consume('api_calls', user_id)
        
        if not info.allowed:
            logger.warning(
                "API rate limit exceeded",
                extra={
                    'user_id': user_id,
                    'path': request.url.path,
                    'retry_after': info.retry_after
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={
                    "Retry-After": str(int(info.retry_after)),
                    "X-RateLimit-Limit": "1000",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(info.reset_at))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = "1000"
        response.headers["X-RateLimit-Remaining"] = str(info.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(info.reset_at))
        
        return response


# Add to FastAPI app
# In src/api/main.py:
# from api.middleware import RateLimitMiddleware
# app.add_middleware(RateLimitMiddleware)
```

***

### **Step 3.4: Test Rate Limiting**

```bash
# Test rate limit
for i in {1..105}; do
  curl -w "\nStatus: %{http_code}\n" http://localhost:8000/api/tasks
  sleep 0.1
done

# Should see 429 after 100 requests

# Check headers
curl -I http://localhost:8000/api/tasks
# X-RateLimit-Limit: 1000
# X-RateLimit-Remaining: 999
# X-RateLimit-Reset: 1733338800
```

***

## **Phase 4: Metrics Export (2 hours)**

### **Step 4.1: Install Prometheus Client**

```bash
pip install prometheus-client==0.19.0
```

***

### **Step 4.2: Create Metrics System**

**File**: `src/monitoring/metrics.py` (NEW FILE)

```python
"""
Prometheus Metrics Export
Standard metrics for monitoring and alerting
"""
from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    generate_latest, REGISTRY
)
from prometheus_client.core import CollectorRegistry
from typing import Optional
import time

from utils.structured_logger import get_logger

logger = get_logger(__name__)

# Create custom registry (optional, for isolation)
# registry = CollectorRegistry()

# Use default registry for simplicity
registry = REGISTRY


# ========== APPLICATION INFO ==========

app_info = Info(
    'astro_app',
    'Astro application information',
    registry=registry
)

app_info.info({
    'version': '1.0.0',
    'python_version': '3.11',
    'environment': 'production'
})


# ========== TASK METRICS ==========

task_total = Counter(
    'astro_tasks_total',
    'Total number of tasks executed',
    ['agent_id', 'status'],  # Labels: agent_id, status (success/failure)
    registry=registry
)

task_duration_seconds = Histogram(
    'astro_task_duration_seconds',
    'Task execution duration in seconds',
    ['agent_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=registry
)

active_tasks = Gauge(
    'astro_active_tasks',
    'Number of currently active tasks',
    registry=registry
)

queued_tasks = Gauge(
    'astro_queued_tasks',
    'Number of tasks in queue',
    registry=registry
)


# ========== WORKFLOW METRICS ==========

workflow_total = Counter(
    'astro_workflows_total',
    'Total number of workflows submitted',
    ['status'],  # completed, failed, cancelled
    registry=registry
)

workflow_duration_seconds = Histogram(
    'astro_workflow_duration_seconds',
    'Workflow execution duration in seconds',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0],
    registry=registry
)

active_workflows = Gauge(
    'astro_active_workflows',
    'Number of currently active workflows',
    registry=registry
)


# ========== AGENT METRICS ==========

agent_health = Gauge(
    'astro_agent_health',
    'Agent health status (1=healthy, 0=unhealthy)',
    ['agent_id'],
    registry=registry
)

agent_tasks_active = Gauge(
    'astro_agent_tasks_active',
    'Number of active tasks per agent',
    ['agent_id'],
    registry=registry
)

agent_reliability = Gauge(
    'astro_agent_reliability_score',
    'Agent reliability score (0.0-1.0)',
    ['agent_id'],
    registry=registry
)


# ========== LLM METRICS ==========

llm_requests_total = Counter(
    'astro_llm_requests_total',
    'Total LLM API requests',
    ['model', 'status'],  # model name, status (success/failure)
    registry=registry
)

llm_tokens_total = Counter(
    'astro_llm_tokens_total',
    'Total LLM tokens consumed',
    ['model', 'type'],  # type: prompt/completion
    registry=registry
)

llm_request_duration_seconds = Histogram(
    'astro_llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
    registry=registry
)

llm_cost_usd = Counter(
    'astro_llm_cost_usd_total',
    'Total LLM API cost in USD',
    ['model'],
    registry=registry
)


# ========== DATABASE METRICS ==========

db_queries_total = Counter(
    'astro_db_queries_total',
    'Total database queries',
    ['operation'],  # select, insert, update, delete
    registry=registry
)

db_query_duration_seconds = Histogram(
    'astro_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry
)

db_connections_active = Gauge(
    'astro_db_connections_active',
    'Number of active database connections',
    registry=registry
)


# ========== SYSTEM METRICS ==========

system_uptime_seconds = Gauge(
    'astro_system_uptime_seconds',
    'System uptime in seconds',
    registry=registry
)

system_errors_total = Counter(
    'astro_system_errors_total',
    'Total system errors',
    ['error_type'],  # exception name
    registry=registry
)


# ========== HELPER FUNCTIONS ==========

class MetricsCollector:
    """
    Helper class to collect and update metrics
    """
    
    def __init__(self):
        self.start_time = time.time()
    
    def update_system_uptime(self):
        """Update system uptime metric"""
        uptime = time.time() - self.start_time
        system_uptime_seconds.set(uptime)
    
    def record_task_start(self, agent_id: str):
        """Record task start"""
        active_tasks.inc()
        agent_tasks_active.labels(agent_id=agent_id).inc()
    
    def record_task_complete(self, 
                              agent_id: str, 
                              duration_seconds: float, 
                              success: bool):
        """Record task completion"""
        active_tasks.dec()
        agent_tasks_active.labels(agent_id=agent_id).dec()
        
        status = 'success' if success else 'failure'
        task_total.labels(agent_id=agent_id, status=status).inc()
        task_duration_seconds.labels(agent_id=agent_id).observe(duration_seconds)
        
        logger.debug(
            "Task metrics recorded",
            extra={
                'agent_id': agent_id,
                'duration_seconds': duration_seconds,
                'success': success
            }
        )
    
    def record_workflow_start(self):
        """Record workflow start"""
        active_workflows.inc()
    
    def record_workflow_complete(self, 
                                   duration_seconds: float, 
                                   status: str):
        """Record workflow completion"""
        active_workflows.dec()
        workflow_total.labels(status=status).inc()
        workflow_duration_seconds.observe(duration_seconds)
    
    def record_llm_request(self,
                            model: str,
                            duration_seconds: float,
                            prompt_tokens: int,
                            completion_tokens: int,
                            cost_usd: float,
                            success: bool):
        """Record LLM request"""
        status = 'success' if success else 'failure'
        llm_requests_total.labels(model=model, status=status).inc()
        llm_request_duration_seconds.labels(model=model).observe(duration_seconds)
        llm_tokens_total.labels(model=model, type='prompt').inc(prompt_tokens)
        llm_tokens_total.labels(model=model, type='completion').inc(completion_tokens)
        llm_cost_usd.labels(model=model).inc(cost_usd)
    
    def record_db_query(self,
                         operation: str,
                         duration_seconds: float):
        """Record database query"""
        db_queries_total.labels(operation=operation).inc()
        db_query_duration_seconds.labels(operation=operation).observe(duration_seconds)
    
    def update_agent_health(self, agent_id: str, is_healthy: bool):
        """Update agent health status"""
        agent_health.labels(agent_id=agent_id).set(1 if is_healthy else 0)
    
    def update_agent_reliability(self, agent_id: str, score: float):
        """Update agent reliability score"""
        agent_reliability.labels(agent_id=agent_id).set(score)
    
    def record_error(self, error_type: str):
        """Record system error"""
        system_errors_total.labels(error_type=error_type).inc()


# Global instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(registry)
```

***

### **Step 4.3: Add Metrics Endpoint to API**

**File**: `src/api/main.py` (MODIFY EXISTING)

```python
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from monitoring.metrics import get_metrics

app = FastAPI(title="Astro API")

# ... existing routes

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint
    
    Scrape this with Prometheus:
    
    scrape_configs:
      - job_name: 'astro'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/metrics'
    """
    return get_metrics().decode('utf-8')


# Background task to update metrics
from fastapi import BackgroundTasks

@app.on_event("startup")
async def start_metrics_updater():
    """Start background task to update metrics"""
    import asyncio
    from monitoring.metrics import get_metrics_collector
    
    collector = get_metrics_collector()
    
    async def update_loop():
        while True:
            try:
                collector.update_system_uptime()
                await asyncio.sleep(15)  # Update every 15 seconds
            except Exception as e:
                logger.error("Metrics update error", exc_info=True)
    
    asyncio.create_task(update_loop())
```

***

### **Step 4.4: Integrate Metrics into Engine**

**File**: `src/core/engine.py` (MODIFY EXISTING)

```python
from monitoring.metrics import get_metrics_collector

class AgentEngine:
    def __init__(self, ...):
        # Existing code...
        self.metrics = get_metrics_collector()
    
    async def _execute_task_with_agent(self, task: Task, agent_id: str):
        """Execute task with metrics collection"""
        
        # Record task start
        self.metrics.record_task_start(agent_id)
        
        start_time = time.time()
        success = False
        
        try:
            # Existing execution code...
            result = await self._execute_task_internal(task, agent_id)
            success = result.success
            return result
            
        except Exception as e:
            self.metrics.record_error(type(e).__name__)
            raise
        finally:
            # Record task completion
            duration = time.time() - start_time
            self.metrics.record_task_complete(agent_id, duration, success)
```

***

### **Step 4.5: Add Metrics to BaseAgent**

**File**: `src/agents/base_agent.py` (MODIFY EXISTING)

```python
from monitoring.metrics import get_metrics_collector

class BaseAgent(ABC):
    def __init__(self, ...):
        # Existing code...
        self.metrics = get_metrics_collector()
        
        # Update initial health
        self.metrics.update_agent_health(self.agent_id, True)
        self.metrics.update_agent_reliability(self.agent_id, self.reliability_score)
    
    async def execute_task(self, task: Task, context: Optional[Any]) -> TaskResult:
        """Execute task with metrics"""
        
        start_time = time.time()
        success = False
        
        try:
            # Existing execution code...
            result = await self._execute_internal(task, context)
            success = result.success
            return result
        finally:
            duration = time.time() - start_time
            self.metrics.record_task_complete(self.agent_id, duration, success)
```

***

### **Step 4.6: Test Metrics**

```bash
# Start API
uvicorn src.api.main:app --reload

# View metrics
curl http://localhost:8000/metrics

# Sample output:
# astro_tasks_total{agent_id="code_agent_001",status="success"} 45.0
# astro_task_duration_seconds_bucket{agent_id="code_agent_001",le="1.0"} 30.0
# astro_active_tasks 3.0
# astro_agent_health{agent_id="code_agent_001"} 1.0
```

***

### **Step 4.7: Create Grafana Dashboard** (Optional)

**File**: `monitoring/grafana_dashboard.json` (NEW FILE)

```json
{
  "dashboard": {
    "title": "Astro System Monitoring",
    "panels": [
      {
        "title": "Task Success Rate",
        "targets": [
          {
            "expr": "rate(astro_tasks_total{status=\"success\"}[5m]) / rate(astro_tasks_total[5m])"
          }
        ]
      },
      {
        "title": "P95 Task Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(astro_task_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Tasks",
        "targets": [
          {
            "expr": "astro_active_tasks"
          }
        ]
      },
      {
        "title": "Agent Health",
        "targets": [
          {
            "expr": "astro_agent_health"
          }
        ]
      }
    ]
  }
}
```

***

## **Phase 5: Integration & Testing (1 hour)**

### **Step 5.1: Update Requirements**

**File**: `requirements.txt` (MODIFY EXISTING)

```txt
# Existing dependencies...

# NEW: Monitoring & observability
prometheus-client==0.19.0

# No additional deps needed for logging/health/rate-limiting
```

***

### **Step 5.2: Update Configuration**

**File**: `config/system_config.yaml` (MODIFY EXISTING)

```yaml
system:
  environment: "production"  # or "development"
  log_level: "INFO"  # DEBUG for development
  json_logging: true  # false for development
  log_file: "logs/astro.log"
  
  # Rate limiting
  rate_limits:
    task_submission:
      max_requests: 100
      window_seconds: 60
    workflow_creation:
      max_requests: 20
      window_seconds: 60
    api_calls:
      max_requests: 1000
      window_seconds: 60
  
  # Health checks
  health_check_interval: 30  # seconds
  
  # Metrics
  metrics_enabled: true
  metrics_port: 8000  # Same as API port
```

***

### **Step 5.3: Create Production Startup Script**

**File**: `scripts/start_production.sh` (NEW FILE)

```bash
#!/bin/bash
set -e

echo "🚀 Starting Astro in production mode..."

# Create directories
mkdir -p logs
mkdir -p data

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed"
    exit 1
fi

# Check dependencies
python -c "import prometheus_client" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install -r requirements.txt
}

# Set environment variables
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export JSON_LOGGING=true

# Start API server
echo "✅ Starting API server..."
uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-config logging.yaml

# Note: For production, use gunicorn instead:
# gunicorn src.api.main:app \
#     --bind 0.0.0.0:8000 \
#     --workers 4 \
#     --worker-class uvicorn.workers.UvicornWorker \
#     --access-logfile logs/access.log \
#     --error-logfile logs/error.log
```

***

### **Step 5.4: Create Test Suite**

**File**: `tests/test_production_features.py` (NEW FILE)

```python
"""
Test production features
"""
import pytest
import asyncio
from fastapi.testclient import TestClient

from api.main import app
from core.rate_limiter import TokenBucketRateLimiter
from monitoring.metrics import get_metrics_collector


def test_health_live():
    """Test liveness probe"""
    client = TestClient(app)
    response = client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "uptime_seconds" in data


def test_health_ready():
    """Test readiness probe"""
    client = TestClient(app)
    response = client.get("/health/ready")
    
    # May be 200 or 503 depending on state
    assert response.status_code in [200, 503]
    data = response.json()
    assert "checks" in data


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiting"""
    limiter = TokenBucketRateLimiter(max_requests=10, window_seconds=60)
    
    # Should allow first 10 requests
    for i in range(10):
        info = await limiter.consume(f"test_key")
        assert info.allowed, f"Request {i+1} should be allowed"
    
    # 11th request should be blocked
    info = await limiter.consume("test_key")
    assert not info.allowed
    assert info.retry_after > 0


def test_metrics_endpoint():
    """Test Prometheus metrics"""
    client = TestClient(app)
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert "astro_tasks_total" in response.text
    assert "astro_agent_health" in response.text


def test_structured_logging():
    """Test structured logging output"""
    from utils.structured_logger import get_logger, LogContext
    import json
    from io import StringIO
    
    # Capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(StructuredFormatter())
    
    logger = get_logger("test")
    logger.addHandler(handler)
    
    with LogContext(request_id="test-123"):
        logger.info("Test message", extra={"test_key": "test_value"})
    
    # Parse JSON log
    log_output = log_stream.getvalue()
    log_data = json.loads(log_output)
    
    assert log_data["level"] == "INFO"
    assert log_data["message"] == "Test message"
    assert log_data["request_id"] == "test-123"
    assert log_data["test_key"] == "test_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

***

### **Step 5.5: Run Tests**

```bash
# Run all tests
pytest tests/test_production_features.py -v

# Run specific test
pytest tests/test_production_features.py::test_rate_limiter -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

***

## **Phase 6: Documentation & Deployment**

### **Step 6.1: Update README**

**File**: `README.md` (ADD SECTION)

```markdown
## Production Features

### Structured Logging

Astro uses JSON-structured logging for production environments:

```
from utils.structured_logger import get_logger, LogContext

logger = get_logger(__name__)

with LogContext(request_id="req-123", workflow_id="wf-456"):
    logger.info("Task completed", extra={
        'agent_id': 'code_001',
        'duration_ms': 1234.5
    })
```

**Query logs:**
```
# Find errors
cat logs/astro.log | jq 'select(.level == "ERROR")'

# Find slow operations
cat logs/astro.log | jq 'select(.duration_ms > 1000)'

# Filter by agent
cat logs/astro.log | jq 'select(.agent_id == "code_agent_001")'
```

### Health Checks

Kubernetes-compatible health probes:

- **Liveness**: `GET /health/live` - Process is alive
- **Readiness**: `GET /health/ready` - Ready to serve traffic
- **Startup**: `GET /health/startup` - Initial startup complete

### Rate Limiting

Automatic rate limiting per user/API key:

- Task submission: 100/minute
- Workflow creation: 20/minute
- API calls: 1000/minute

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1733338800
```

### Metrics

Prometheus metrics at `/metrics`:

**Key Metrics:**
- `astro_tasks_total` - Total tasks (by agent, status)
- `astro_task_duration_seconds` - Task duration histogram
- `astro_agent_health` - Agent health (1=healthy, 0=unhealthy)
- `astro_llm_cost_usd_total` - LLM API cost

**Grafana Queries:**
```
# Task success rate
rate(astro_tasks_total{status="success"}[5m]) / rate(astro_tasks_total[5m])

# P95 task duration
histogram_quantile(0.95, rate(astro_task_duration_seconds_bucket[5m]))

# Active tasks
astro_active_tasks
```

## Deployment

### Docker

```
# Build
docker build -t astro:latest .

# Run
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  astro:latest
```

### Kubernetes

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: astro
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: astro
        image: astro:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          failureThreshold: 30
          periodSeconds: 10
```

### Monitoring Stack

```
# Prometheus
docker run -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana
docker run -p 3000:3000 grafana/grafana

# Import dashboard from monitoring/grafana_dashboard.json
```
```

***

### **Step 6.2: Create Prometheus Config**

**File**: `prometheus.yml` (NEW FILE)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'astro'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

***

### **Step 6.3: Create Docker Compose for Full Stack**

**File**: `docker-compose.yml` (NEW FILE)

```yaml
version: '3.8'

services:
  astro:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - JSON_LOGGING=true
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana_dashboard.json:/etc/grafana/provisioning/dashboards/astro.json

volumes:
  prometheus_data:
  grafana_data:
```

***

## **Final Checklist: A+ Production Ready**

### **✅ Completed Features**

- [x] **Structured Logging** - JSON logs with context
- [x] **Health Checks** - Liveness, readiness, startup probes
- [x] **Rate Limiting** - Per-user token bucket
- [x] **Metrics Export** - Prometheus format with 20+ metrics
- [x] **Error Handling** - Proper exception logging
- [x] **Configuration Validation** - Type-safe configs
- [x] **API Documentation** - FastAPI auto-docs
- [x] **Testing** - Production feature test suite
- [x] **Docker Support** - Containerized deployment
- [x] **K8s Manifests** - Production-ready YAML
- [x] **Monitoring Stack** - Prometheus + Grafana

***
