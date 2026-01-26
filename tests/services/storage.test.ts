import { SQLiteStorage, StoredSession, StoredApproval, StoredAuditLog } from '../../src/services/storage';
import * as fs from 'fs';
import * as path from 'path';

describe('SQLiteStorage', () => {
  let storage: SQLiteStorage;
  const testDbPath = path.join(__dirname, '../../data/test-storage.db');

  beforeAll(async () => {
    // Clean up any existing test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
    storage = new SQLiteStorage(testDbPath);
    await storage.init();
  });

  afterAll(() => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('Settings', () => {
    it('should save and retrieve a setting', async () => {
      await storage.setSetting('test-key', 'test-value');
      const value = await storage.getSetting('test-key');
      expect(value).toBe('test-value');
    });

    it('should return undefined for non-existent setting', async () => {
      const value = await storage.getSetting('non-existent-key');
      expect(value).toBeUndefined();
    });
  });

  describe('Sessions', () => {
    const testSession: StoredSession = {
      sessionId: 'test-session-1',
      userId: 'user-1',
      userRole: 'admin',
      conversationHistory: [
        { timestamp: new Date().toISOString(), role: 'user', content: 'Hello' },
        { timestamp: new Date().toISOString(), role: 'system', content: 'Hi there!' },
      ],
      activeAgent: 'general-assistant',
      metadata: { source: 'test' },
      updatedAt: new Date().toISOString(),
    };

    it('should save and retrieve a session', async () => {
      await storage.saveSession(testSession);
      const retrieved = await storage.getSession('test-session-1');
      expect(retrieved).toBeDefined();
      expect(retrieved?.sessionId).toBe('test-session-1');
      expect(retrieved?.userId).toBe('user-1');
    });

    it('should return undefined for non-existent session', async () => {
      const session = await storage.getSession('non-existent-session');
      expect(session).toBeUndefined();
    });

    it('should delete a session', async () => {
      const sessionToDelete: StoredSession = {
        ...testSession,
        sessionId: 'session-to-delete',
      };
      await storage.saveSession(sessionToDelete);
      await storage.deleteSession('session-to-delete');
      const deleted = await storage.getSession('session-to-delete');
      expect(deleted).toBeUndefined();
    });
  });

  describe('Approvals', () => {
    const testApproval: StoredApproval = {
      approvalId: 'approval-1',
      sessionId: 'session-1',
      toolName: 'http_request',
      agentId: 'general-assistant',
      parameters: { url: 'https://example.com' },
      riskScore: 0.6,
      createdAt: new Date().toISOString(),
    };

    it('should save and retrieve approvals', async () => {
      await storage.saveApproval(testApproval);
      const approvals = await storage.getApprovals();
      expect(approvals.length).toBeGreaterThan(0);
    });

    it('should delete an approval', async () => {
      const approvalToDelete: StoredApproval = {
        ...testApproval,
        approvalId: 'approval-to-delete',
      };
      await storage.saveApproval(approvalToDelete);
      await storage.deleteApproval('approval-to-delete');
      // Verify deletion by checking approvals list
      const approvals = await storage.getApprovals();
      const found = approvals.find((a) => a.approvalId === 'approval-to-delete');
      expect(found).toBeUndefined();
    });
  });

  describe('Audit Logs', () => {
    const testAuditLog: StoredAuditLog = {
      id: 'audit-1',
      timestamp: new Date().toISOString(),
      userId: 'user-1',
      role: 'admin',
      action: 'execute_tool',
      resource: 'math_eval',
      decision: 'allowed',
      riskScore: 0.3,
      metadata: { expression: '2+2' },
      signature: 'test-signature-hash',
    };

    it('should append and retrieve audit logs', async () => {
      await storage.appendAuditLog(testAuditLog);
      const logs = await storage.getAuditLogs();
      expect(logs.length).toBeGreaterThan(0);
    });
  });

  describe('Threats', () => {
    it('should save and load threats', async () => {
      const threat = { id: 'threat-1', name: 'Test Threat', severity: 'high' };
      await storage.saveThreat('threat-1', threat);
      const threats = await storage.loadThreats();
      expect(threats.length).toBeGreaterThan(0);
    });
  });

  describe('Incidents', () => {
    it('should save and load incidents', async () => {
      const incident = { id: 'incident-1', title: 'Test Incident', severity: 'medium' };
      await storage.saveIncident('incident-1', incident);
      const incidents = await storage.loadIncidents();
      expect(incidents.length).toBeGreaterThan(0);
    });
  });

  describe('Knowledge Entries', () => {
    it('should save and load knowledge entries', async () => {
      const entry = { id: 'knowledge-1', key: 'test-key', value: 'test-value' };
      await storage.saveKnowledgeEntry('knowledge-1', entry);
      const entries = await storage.loadKnowledgeEntries();
      expect(entries.length).toBeGreaterThan(0);
    });
  });
});
