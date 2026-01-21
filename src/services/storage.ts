import sqlite3 from 'sqlite3';
import path from 'path';
import { promises as fs } from 'fs';

export type StoredSession = {
  sessionId: string;
  userId: string;
  userRole: string;
  conversationHistory: Array<{
    timestamp: string;
    role: 'user' | 'system';
    content: string;
    intent?: string;
    toolName?: string;
    agentId?: string;
    result?: unknown;
    error?: string;
    sessionId?: string;
    riskScore?: number;
    requiresApproval?: boolean;
  }>;
  activeAgent?: string;
  metadata: Record<string, unknown>;
  updatedAt: string;
};

export type StoredApproval = {
  approvalId: string;
  sessionId: string;
  toolName: string;
  agentId: string;
  parameters: Record<string, unknown>;
  riskScore: number;
  createdAt: string;
};

export type StoredAuditLog = {
  id: string;
  timestamp: string;
  userId: string;
  role: string;
  action: string;
  resource: string;
  decision: string;
  riskScore?: number;
  metadata?: Record<string, unknown>;
  signature: string;
};

export class SQLiteStorage {
  private db: sqlite3.Database | null = null;
  private readonly dbPath: string;

  constructor(dbPath: string) {
    this.dbPath = dbPath;
  }

  async init(): Promise<void> {
    await fs.mkdir(path.dirname(this.dbPath), { recursive: true });
    await this.open();
    await this.run(`
      CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      )
    `);
    await this.run(`
      CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        userId TEXT NOT NULL,
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        resource TEXT NOT NULL,
        decision TEXT NOT NULL,
        riskScore REAL,
        metadata TEXT,
        signature TEXT NOT NULL
      )
    `);
    await this.run(`
      CREATE TABLE IF NOT EXISTS sessions (
        sessionId TEXT PRIMARY KEY,
        userId TEXT NOT NULL,
        userRole TEXT NOT NULL,
        conversationHistory TEXT NOT NULL,
        activeAgent TEXT,
        metadata TEXT NOT NULL,
        updatedAt TEXT NOT NULL
      )
    `);
    await this.run(`
      CREATE TABLE IF NOT EXISTS approvals (
        approvalId TEXT PRIMARY KEY,
        sessionId TEXT NOT NULL,
        toolName TEXT NOT NULL,
        agentId TEXT NOT NULL,
        parameters TEXT NOT NULL,
        riskScore REAL NOT NULL,
        createdAt TEXT NOT NULL
      )
    `);
    await this.run(`
      CREATE TABLE IF NOT EXISTS threats (
        id TEXT PRIMARY KEY,
        payload TEXT NOT NULL
      )
    `);
    await this.run(`
      CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        payload TEXT NOT NULL
      )
    `);
    await this.run(`
      CREATE TABLE IF NOT EXISTS knowledge_entries (
        id TEXT PRIMARY KEY,
        payload TEXT NOT NULL
      )
    `);
  }

  private async open(): Promise<void> {
    if (this.db) {
      return;
    }

    await new Promise<void>((resolve, reject) => {
      const db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) {
          reject(err);
          return;
        }
        this.db = db;
        resolve();
      });
    });
  }

  private async run(sql: string, params: Array<unknown> = []): Promise<void> {
    if (!this.db) {
      throw new Error('Database not initialized');
    }
    await new Promise<void>((resolve, reject) => {
      this.db!.run(sql, params, (err) => {
        if (err) {
          reject(err);
          return;
        }
        resolve();
      });
    });
  }

  private async get<T>(sql: string, params: Array<unknown> = []): Promise<T | undefined> {
    if (!this.db) {
      throw new Error('Database not initialized');
    }
    return new Promise<T | undefined>((resolve, reject) => {
      this.db!.get(sql, params, (err, row) => {
        if (err) {
          reject(err);
          return;
        }
        resolve(row as T | undefined);
      });
    });
  }

  private async all<T>(sql: string, params: Array<unknown> = []): Promise<T[]> {
    if (!this.db) {
      throw new Error('Database not initialized');
    }
    return new Promise<T[]>((resolve, reject) => {
      this.db!.all(sql, params, (err, rows) => {
        if (err) {
          reject(err);
          return;
        }
        resolve(rows as T[]);
      });
    });
  }

  async getSetting(key: string): Promise<string | undefined> {
    const row = await this.get<{ value: string }>(
      'SELECT value FROM settings WHERE key = ?',
      [key]
    );
    return row?.value;
  }

  async setSetting(key: string, value: string): Promise<void> {
    await this.run(
      'INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value',
      [key, value]
    );
  }

  async appendAuditLog(entry: StoredAuditLog): Promise<void> {
    await this.run(
      `
      INSERT INTO audit_logs
        (id, timestamp, userId, role, action, resource, decision, riskScore, metadata, signature)
      VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `,
      [
        entry.id,
        entry.timestamp,
        entry.userId,
        entry.role,
        entry.action,
        entry.resource,
        entry.decision,
        entry.riskScore ?? null,
        entry.metadata ? JSON.stringify(entry.metadata) : null,
        entry.signature,
      ]
    );
  }

  async getAuditLogs(): Promise<StoredAuditLog[]> {
    const rows = await this.all<StoredAuditLog>('SELECT * FROM audit_logs ORDER BY timestamp ASC');
    return rows.map((row) => ({
      ...row,
      metadata: row.metadata ? JSON.parse(row.metadata as unknown as string) : undefined,
    }));
  }

  async saveSession(session: StoredSession): Promise<void> {
    await this.run(
      `
      INSERT INTO sessions
        (sessionId, userId, userRole, conversationHistory, activeAgent, metadata, updatedAt)
      VALUES
        (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(sessionId) DO UPDATE SET
        userId = excluded.userId,
        userRole = excluded.userRole,
        conversationHistory = excluded.conversationHistory,
        activeAgent = excluded.activeAgent,
        metadata = excluded.metadata,
        updatedAt = excluded.updatedAt
    `,
      [
        session.sessionId,
        session.userId,
        session.userRole,
        JSON.stringify(session.conversationHistory),
        session.activeAgent ?? null,
        JSON.stringify(session.metadata),
        session.updatedAt,
      ]
    );
  }

  async getSession(sessionId: string): Promise<StoredSession | undefined> {
    const row = await this.get<StoredSession>(
      'SELECT * FROM sessions WHERE sessionId = ?',
      [sessionId]
    );
    if (!row) {
      return undefined;
    }
    return {
      ...row,
      conversationHistory: JSON.parse(row.conversationHistory as unknown as string),
      metadata: JSON.parse(row.metadata as unknown as string),
    };
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.run('DELETE FROM sessions WHERE sessionId = ?', [sessionId]);
  }

  async saveApproval(approval: StoredApproval): Promise<void> {
    await this.run(
      `
      INSERT INTO approvals
        (approvalId, sessionId, toolName, agentId, parameters, riskScore, createdAt)
      VALUES
        (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(approvalId) DO UPDATE SET
        sessionId = excluded.sessionId,
        toolName = excluded.toolName,
        agentId = excluded.agentId,
        parameters = excluded.parameters,
        riskScore = excluded.riskScore,
        createdAt = excluded.createdAt
    `,
      [
        approval.approvalId,
        approval.sessionId,
        approval.toolName,
        approval.agentId,
        JSON.stringify(approval.parameters),
        approval.riskScore,
        approval.createdAt,
      ]
    );
  }

  async getApprovals(): Promise<StoredApproval[]> {
    const rows = await this.all<StoredApproval>('SELECT * FROM approvals ORDER BY createdAt ASC');
    return rows.map((row) => ({
      ...row,
      parameters: JSON.parse(row.parameters as unknown as string),
    }));
  }

  async deleteApproval(approvalId: string): Promise<void> {
    await this.run('DELETE FROM approvals WHERE approvalId = ?', [approvalId]);
  }

  async saveThreat(id: string, payload: unknown): Promise<void> {
    await this.run(
      'INSERT INTO threats (id, payload) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET payload = excluded.payload',
      [id, JSON.stringify(payload)]
    );
  }

  async saveIncident(id: string, payload: unknown): Promise<void> {
    await this.run(
      'INSERT INTO incidents (id, payload) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET payload = excluded.payload',
      [id, JSON.stringify(payload)]
    );
  }

  async saveKnowledgeEntry(id: string, payload: unknown): Promise<void> {
    await this.run(
      'INSERT INTO knowledge_entries (id, payload) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET payload = excluded.payload',
      [id, JSON.stringify(payload)]
    );
  }

  async loadThreats<T>(): Promise<T[]> {
    const rows = await this.all<{ payload: string }>('SELECT payload FROM threats');
    return rows.map((row) => JSON.parse(row.payload));
  }

  async loadIncidents<T>(): Promise<T[]> {
    const rows = await this.all<{ payload: string }>('SELECT payload FROM incidents');
    return rows.map((row) => JSON.parse(row.payload));
  }

  async loadKnowledgeEntries<T>(): Promise<T[]> {
    const rows = await this.all<{ payload: string }>('SELECT payload FROM knowledge_entries');
    return rows.map((row) => JSON.parse(row.payload));
  }
}
