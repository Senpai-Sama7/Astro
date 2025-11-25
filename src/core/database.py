"""
Database Persistence Layer

REFACTORED: Native async database operations using aiosqlite.
- True async I/O without blocking the event loop
- Connection pooling via async context managers
- Maintains backward compatibility with sync API for CLI/scripts
"""
import json
import sqlite3
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

# Import aiosqlite for native async SQLite
try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False
    logging.warning("aiosqlite not installed. Async DB operations will use thread fallback.")

logger = logging.getLogger("DatabaseManager")

class DatabaseManager:
    def __init__(self, db_path: str = "ecosystem.db", connection_timeout: float = 30.0):
        self.db_path = db_path
        self.connection_timeout = connection_timeout
        self._async_initialized = False
        self._closed = False
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Agents table
        c.execute('''CREATE TABLE IF NOT EXISTS agents
                     (agent_id TEXT PRIMARY KEY, 
                      config TEXT,
                      state TEXT,
                      reliability_score REAL,
                      last_updated TIMESTAMP)''')
                      
        # Workflows table
        c.execute('''CREATE TABLE IF NOT EXISTS workflows
                     (workflow_id TEXT PRIMARY KEY,
                      name TEXT,
                      status TEXT,
                      priority TEXT,
                      created_at TIMESTAMP)''')
                      
        # Tasks table
        c.execute('''CREATE TABLE IF NOT EXISTS tasks
                     (task_id TEXT PRIMARY KEY,
                      workflow_id TEXT,
                      description TEXT,
                      status TEXT,
                      assigned_agent TEXT,
                      result TEXT,
                      created_at TIMESTAMP,
                      completed_at TIMESTAMP,
                      FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id))''')
                      
        # Metrics table
        c.execute('''CREATE TABLE IF NOT EXISTS metrics
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      agent_id TEXT,
                      metric_type TEXT,
                      value REAL,
                      timestamp TIMESTAMP)''')
                      
        # Create Indices
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_workflow_id ON tasks(workflow_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_metrics_agent_id ON metrics(agent_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
                      
        conn.commit()
        conn.close()

    # ========== ASYNC INITIALIZATION ==========
    
    async def _ensure_async_init(self):
        """Ensure async schema is initialized (idempotent)"""
        if self._async_initialized:
            return
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path) as db:
                # Enable WAL mode for better concurrency
                await db.execute('PRAGMA journal_mode=WAL')
                await db.commit()
        
        self._async_initialized = True
    
    # ========== SYNC HELPERS ==========
    
    def _execute_write(self, sql: str, params: tuple):
        """Execute a sync write operation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(sql, params)
                conn.commit()
        except Exception as e:
            logger.error(f"DB Write Error: {e}")
            raise
    
    # ========== SYNC API (Backward Compatible) ==========
    
    def save_agent(self, agent_id: str, config: Dict, state: str, reliability: float):
        """Sync save agent (blocks caller)"""
        sql = '''INSERT OR REPLACE INTO agents 
                 (agent_id, config, state, reliability_score, last_updated)
                 VALUES (?, ?, ?, ?, ?)'''
        params = (agent_id, json.dumps(config), state, reliability, datetime.now().isoformat())
        self._execute_write(sql, params)

    def save_workflow(self, workflow_id: str, name: str, status: str, priority: str):
        """Sync save workflow (blocks caller)"""
        sql = '''INSERT OR REPLACE INTO workflows 
                 (workflow_id, name, status, priority, created_at)
                 VALUES (?, ?, ?, ?, ?)'''
        params = (workflow_id, name, status, priority, datetime.now().isoformat())
        self._execute_write(sql, params)

    def save_task(self, task_id: str, workflow_id: str, description: str, status: str, 
                  assigned_agent: Optional[str] = None, result: Optional[Dict] = None):
        """Sync save task (blocks caller)"""
        sql = '''INSERT OR REPLACE INTO tasks 
                 (task_id, workflow_id, description, status, assigned_agent, result, created_at, completed_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
        now = datetime.now().isoformat()
        params = (task_id, workflow_id, description, status, assigned_agent, 
                  json.dumps(result) if result else None, now, 
                  now if status == 'completed' else None)
        self._execute_write(sql, params)

    def log_metric(self, agent_id: str, metric_type: str, value: float):
        """Sync log metric (blocks caller)"""
        sql = '''INSERT INTO metrics (agent_id, metric_type, value, timestamp)
                 VALUES (?, ?, ?, ?)'''
        params = (agent_id, metric_type, value, datetime.now().isoformat())
        self._execute_write(sql, params)
    
    # ========== ASYNC API (Native aiosqlite) ==========
    
    async def save_agent_async(self, agent_id: str, config: Dict, state: str, reliability: float):
        """Async save agent using native aiosqlite"""
        await self._ensure_async_init()
        sql = '''INSERT OR REPLACE INTO agents 
                 (agent_id, config, state, reliability_score, last_updated)
                 VALUES (?, ?, ?, ?, ?)'''
        params = (agent_id, json.dumps(config), state, reliability, datetime.now().isoformat())
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(sql, params)
                await db.commit()
        else:
            # Fallback to thread executor
            await asyncio.to_thread(self.save_agent, agent_id, config, state, reliability)
    
    async def save_workflow_async(self, workflow_id: str, name: str, status: str, priority: str):
        """Async save workflow using native aiosqlite"""
        await self._ensure_async_init()
        sql = '''INSERT OR REPLACE INTO workflows 
                 (workflow_id, name, status, priority, created_at)
                 VALUES (?, ?, ?, ?, ?)'''
        params = (workflow_id, name, status, priority, datetime.now().isoformat())
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(sql, params)
                await db.commit()
        else:
            await asyncio.to_thread(self.save_workflow, workflow_id, name, status, priority)
    
    async def save_task_async(self, task_id: str, workflow_id: str, description: str, status: str, 
                               assigned_agent: Optional[str] = None, result: Optional[Dict] = None):
        """Async save task using native aiosqlite"""
        await self._ensure_async_init()
        sql = '''INSERT OR REPLACE INTO tasks 
                 (task_id, workflow_id, description, status, assigned_agent, result, created_at, completed_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
        params = (task_id, workflow_id, description, status, assigned_agent, 
                  json.dumps(result) if result else None, datetime.now().isoformat(), 
                  datetime.now().isoformat() if status == 'completed' else None)
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(sql, params)
                await db.commit()
        else:
            await asyncio.to_thread(self.save_task, task_id, workflow_id, description, status, assigned_agent, result)
    
    async def log_metric_async(self, agent_id: str, metric_type: str, value: float):
        """Async log metric using native aiosqlite"""
        await self._ensure_async_init()
        sql = '''INSERT INTO metrics (agent_id, metric_type, value, timestamp)
                 VALUES (?, ?, ?, ?)'''
        params = (agent_id, metric_type, value, datetime.now().isoformat())
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(sql, params)
                await db.commit()
        else:
            await asyncio.to_thread(self.log_metric, agent_id, metric_type, value)
    
    async def get_recent_metrics_async(self, agent_id: str, metric_type: str, limit: int = 100) -> List[Dict]:
        """Async fetch recent metrics using native aiosqlite"""
        await self._ensure_async_init()
        sql = '''SELECT value, timestamp FROM metrics 
                 WHERE agent_id = ? AND metric_type = ?
                 ORDER BY timestamp DESC LIMIT ?'''
        params = (agent_id, metric_type, limit)
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path, timeout=self.connection_timeout) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    return [{'value': row[0], 'timestamp': row[1]} for row in rows]
        else:
            # Fallback - run in thread to avoid blocking
            def _sync_read():
                with sqlite3.connect(self.db_path, timeout=self.connection_timeout) as conn:
                    cursor = conn.execute(sql, params)
                    return cursor.fetchall()
            rows = await asyncio.to_thread(_sync_read)
            return [{'value': row[0], 'timestamp': row[1]} for row in rows]
    
    async def get_agent_stats_async(self, agent_id: str) -> Dict[str, Any]:
        """Async fetch aggregated stats using native aiosqlite"""
        await self._ensure_async_init()
        sql = '''SELECT metric_type, AVG(value) as avg_val, COUNT(*) as count
                 FROM metrics WHERE agent_id = ?
                 GROUP BY metric_type'''
        params = (agent_id,)
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path, timeout=self.connection_timeout) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    return {row[0]: {'avg': row[1], 'count': row[2]} for row in rows if row[0]}
        else:
            # Fallback - run in thread to avoid blocking
            def _sync_read():
                with sqlite3.connect(self.db_path, timeout=self.connection_timeout) as conn:
                    cursor = conn.execute(sql, params)
                    return cursor.fetchall()
            rows = await asyncio.to_thread(_sync_read)
            return {row[0]: {'avg': row[1], 'count': row[2]} for row in rows if row[0]}
    
    async def get_all_agents_async(self) -> List[Dict]:
        """Async fetch all registered agents"""
        await self._ensure_async_init()
        sql = 'SELECT agent_id, config, state, reliability_score, last_updated FROM agents'
        
        def _parse_row(row) -> Dict:
            """Safely parse a row with error handling for JSON"""
            try:
                config = json.loads(row[1]) if row[1] else {}
            except (json.JSONDecodeError, TypeError):
                config = {}
                logger.warning(f"Failed to parse config for agent {row[0]}")
            return {
                'agent_id': row[0],
                'config': config,
                'state': row[2],
                'reliability_score': row[3],
                'last_updated': row[4]
            }
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path, timeout=self.connection_timeout) as db:
                async with db.execute(sql) as cursor:
                    rows = await cursor.fetchall()
                    return [_parse_row(row) for row in rows]
        else:
            # Fallback - run in thread to avoid blocking
            def _sync_read():
                with sqlite3.connect(self.db_path, timeout=self.connection_timeout) as conn:
                    cursor = conn.execute(sql)
                    return cursor.fetchall()
            rows = await asyncio.to_thread(_sync_read)
            return [_parse_row(row) for row in rows]
    
    def close(self):
        """Cleanup resources and mark as closed"""
        self._closed = True
        logger.info("Database manager closed")
    
    async def prune_old_metrics_async(self, days: int = 30) -> int:
        """Remove metrics older than specified days. Returns count of deleted rows."""
        await self._ensure_async_init()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        sql = 'DELETE FROM metrics WHERE timestamp < ?'
        params = (cutoff,)
        
        if HAS_AIOSQLITE:
            async with aiosqlite.connect(self.db_path, timeout=self.connection_timeout) as db:
                cursor = await db.execute(sql, params)
                await db.commit()
                return cursor.rowcount
        else:
            def _sync_delete():
                with sqlite3.connect(self.db_path, timeout=self.connection_timeout) as conn:
                    cursor = conn.execute(sql, params)
                    conn.commit()
                    return cursor.rowcount
            return await asyncio.to_thread(_sync_delete)
    
    async def get_database_stats_async(self) -> Dict[str, Any]:
        """Get database statistics for monitoring"""
        await self._ensure_async_init()
        stats = {}
        
        tables = ['agents', 'workflows', 'tasks', 'metrics']
        for table in tables:
            sql = f'SELECT COUNT(*) FROM {table}'
            if HAS_AIOSQLITE:
                async with aiosqlite.connect(self.db_path, timeout=self.connection_timeout) as db:
                    async with db.execute(sql) as cursor:
                        row = await cursor.fetchone()
                        stats[f'{table}_count'] = row[0] if row else 0
            else:
                def _sync_count(t=table):
                    with sqlite3.connect(self.db_path, timeout=self.connection_timeout) as conn:
                        cursor = conn.execute(f'SELECT COUNT(*) FROM {t}')
                        row = cursor.fetchone()
                        return row[0] if row else 0
                stats[f'{table}_count'] = await asyncio.to_thread(_sync_count)
        
        return stats
    
    def backup(self, backup_path: str):
        """Create a backup of the database"""
        import shutil
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def restore(self, backup_path: str):
        """Restore database from backup"""
        import shutil
        try:
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

# CLI interface
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Management CLI')
    parser.add_argument('command', choices=['backup', 'restore'], help='Command to execute')
    parser.add_argument('--db', default='ecosystem.db', help='Database file path')
    parser.add_argument('--file', required=True, help='Backup file path')
    
    args = parser.parse_args()
    
    db = DatabaseManager(args.db)
    
    if args.command == 'backup':
        if db.backup(args.file):
            print(f"✅ Backup created: {args.file}")
            sys.exit(0)
        else:
            print(f"❌ Backup failed")
            sys.exit(1)
    elif args.command == 'restore':
        if db.restore(args.file):
            print(f"✅ Database restored from: {args.file}")
            sys.exit(0)
        else:
            print(f"❌ Restore failed")
            sys.exit(1)
