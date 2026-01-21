import { randomBytes, createHmac } from 'crypto';
import { v4 as uuidv4 } from 'uuid';
import { SQLiteStorage } from '../services/storage';

export type RoleType = 'admin' | 'analyst' | 'red-team' | 'blue-team' | 'read-only' | 'guest';

export interface RBACPolicy {
  role: RoleType;
  permissions: {
    canRegisterTools: boolean;
    canRegisterAgents: boolean;
    canExecuteTools: boolean;
    canViewAudit: boolean;
    canManageUsers: boolean;
    canModifyRisk: boolean;
  };
}

export const RBAC_POLICIES: Record<RoleType, RBACPolicy> = {
  admin: {
    role: 'admin',
    permissions: {
      canRegisterTools: true,
      canRegisterAgents: true,
      canExecuteTools: true,
      canViewAudit: true,
      canManageUsers: true,
      canModifyRisk: true,
    },
  },
  analyst: {
    role: 'analyst',
    permissions: {
      canRegisterTools: false,
      canRegisterAgents: false,
      canExecuteTools: true,
      canViewAudit: true,
      canManageUsers: false,
      canModifyRisk: false,
    },
  },
  'red-team': {
    role: 'red-team',
    permissions: {
      canRegisterTools: true,
      canRegisterAgents: true,
      canExecuteTools: true,
      canViewAudit: false,
      canManageUsers: false,
      canModifyRisk: false,
    },
  },
  'blue-team': {
    role: 'blue-team',
    permissions: {
      canRegisterTools: true,
      canRegisterAgents: true,
      canExecuteTools: true,
      canViewAudit: true,
      canManageUsers: false,
      canModifyRisk: true,
    },
  },
  'read-only': {
    role: 'read-only',
    permissions: {
      canRegisterTools: false,
      canRegisterAgents: false,
      canExecuteTools: false,
      canViewAudit: true,
      canManageUsers: false,
      canModifyRisk: false,
    },
  },
  guest: {
    role: 'guest',
    permissions: {
      canRegisterTools: false,
      canRegisterAgents: false,
      canExecuteTools: false,
      canViewAudit: false,
      canManageUsers: false,
      canModifyRisk: false,
    },
  },
};

export interface AuditLogEntry {
  id: string;
  timestamp: Date;
  userId: string;
  role: RoleType;
  action: string;
  resource: string;
  decision: 'APPROVED' | 'DENIED' | 'PENDING';
  riskScore?: number;
  metadata?: Record<string, unknown>;
  signature: string; // HMAC signature for tamper-evidence
}

/**
 * OTIS Security Gateway
 * Manages RBAC, risk scoring, approval workflows, and immutable audit logs.
 */
export class OTISSecurityGateway {
  private auditLog: AuditLogEntry[] = [];
  private signingKey: string; // Secret key for audit log signatures
  private riskThreshold: number = 0.5; // CVaR threshold (default 50%)
  private storage?: SQLiteStorage;

  constructor(storage?: SQLiteStorage) {
    this.storage = storage;
    this.signingKey = randomBytes(32).toString('hex');
  }

  async init(): Promise<void> {
    if (!this.storage) {
      return;
    }

    const storedKey = await this.storage.getSetting('otis.signingKey');
    if (storedKey) {
      this.signingKey = storedKey;
    } else {
      this.signingKey = randomBytes(32).toString('hex');
      await this.storage.setSetting('otis.signingKey', this.signingKey);
    }

    const storedLogs = await this.storage.getAuditLogs();
    this.auditLog = storedLogs.map((entry) => ({
      id: entry.id,
      timestamp: new Date(entry.timestamp),
      userId: entry.userId,
      role: entry.role as RoleType,
      action: entry.action,
      resource: entry.resource,
      decision: entry.decision as AuditLogEntry['decision'],
      riskScore: entry.riskScore,
      metadata: entry.metadata,
      signature: entry.signature,
    }));
  }

  /**
   * Check if a role has permission for an action.
   */
  hasPermission(
    role: RoleType,
    permission: keyof RBACPolicy['permissions']
  ): boolean {
    const policy = RBAC_POLICIES[role];
    if (!policy) {
      return false;
    }
    return policy.permissions[permission];
  }

  /**
   * Calculate risk score for an action (0-1 scale).
   * This is a simplified CVaR algorithm.
   * In production, this would use historical incident data.
   */
  calculateRiskScore(params: {
    role: RoleType;
    action: string;
    resource: string;
    toolName?: string;
  }): number {
    let baseScore = 0.1; // Base risk

    // Red team actions are higher risk
    if (params.role === 'red-team') {
      baseScore += 0.3;
    }

    // Tool registration is higher risk
    if (params.action === 'register_tool') {
      baseScore += 0.2;
    }

    // Sensitive tools are higher risk
    const sensitiveTool = ['http_request', 'math_eval'].includes(
      params.toolName || ''
    );
    if (sensitiveTool) {
      baseScore += 0.15;
    }

    // Cap at 1.0
    return Math.min(baseScore, 1.0);
  }

  /**
   * Log an action to the immutable audit log.
   * Each entry is signed with HMAC to prevent tampering.
   */
  logAction(entry: Omit<AuditLogEntry, 'id' | 'signature'>): AuditLogEntry {
    const id = uuidv4();
    const timestamp = entry.timestamp || new Date();

    // Create HMAC signature over the entry
    const entryString = JSON.stringify({
      id,
      timestamp: timestamp.toISOString(),
      userId: entry.userId,
      role: entry.role,
      action: entry.action,
      resource: entry.resource,
      decision: entry.decision,
      riskScore: entry.riskScore,
    });

    const signature = createHmac('sha256', this.signingKey)
      .update(entryString)
      .digest('hex');

    const logEntry: AuditLogEntry = {
      ...entry,
      id,
      timestamp,
      signature,
    };

    // Append-only: never modify or delete previous entries
    this.auditLog.push(logEntry);
    if (this.storage) {
      void this.storage.appendAuditLog({
        id: logEntry.id,
        timestamp: logEntry.timestamp.toISOString(),
        userId: logEntry.userId,
        role: logEntry.role,
        action: logEntry.action,
        resource: logEntry.resource,
        decision: logEntry.decision,
        riskScore: logEntry.riskScore,
        metadata: logEntry.metadata,
        signature: logEntry.signature,
      });
    }
    return logEntry;
  }

  /**
   * Retrieve audit log (filtered by role permissions).
   */
  getAuditLog(
    requestingRole: RoleType,
    filter?: {
      userId?: string;
      action?: string;
      resource?: string;
      startDate?: Date;
      endDate?: Date;
    }
  ): AuditLogEntry[] {
    // Only certain roles can view audit logs
    if (!this.hasPermission(requestingRole, 'canViewAudit')) {
      return [];
    }

    let entries = [...this.auditLog];

    if (filter?.userId) {
      entries = entries.filter((e) => e.userId === filter.userId);
    }
    if (filter?.action) {
      entries = entries.filter((e) => e.action === filter.action);
    }
    if (filter?.resource) {
      entries = entries.filter((e) => e.resource === filter.resource);
    }
    if (filter?.startDate) {
      entries = entries.filter((e) => e.timestamp >= filter.startDate!);
    }
    if (filter?.endDate) {
      entries = entries.filter((e) => e.timestamp <= filter.endDate!);
    }

    return entries;
  }

  /**
   * Verify the integrity of audit log entries (detect tampering).
   */
  verifyAuditLogIntegrity(): {
    valid: boolean;
    tamperedCount: number;
    invalidEntries: string[];
  } {
    const invalidEntries: string[] = [];
    for (const entry of this.auditLog) {
      const entryString = JSON.stringify({
        id: entry.id,
        timestamp: entry.timestamp.toISOString(),
        userId: entry.userId,
        role: entry.role,
        action: entry.action,
        resource: entry.resource,
        decision: entry.decision,
        riskScore: entry.riskScore,
      });

      const expectedSignature = createHmac('sha256', this.signingKey)
        .update(entryString)
        .digest('hex');

      if (expectedSignature !== entry.signature) {
        invalidEntries.push(entry.id);
      }
    }

    return {
      valid: invalidEntries.length === 0,
      tamperedCount: invalidEntries.length,
      invalidEntries,
    };
  }

  /**
   * Set the risk threshold (CVaR). Actions above this score require approval.
   */
  setRiskThreshold(threshold: number): void {
    if (threshold < 0 || threshold > 1) {
      throw new Error('Risk threshold must be between 0 and 1');
    }
    this.riskThreshold = threshold;
  }

  /**
   * Check if an action requires approval based on risk score.
   */
  requiresApproval(riskScore: number): boolean {
    return riskScore >= this.riskThreshold;
  }

  /**
   * Get RBAC policy for a role.
   */
  getRBACPolicy(role: RoleType): RBACPolicy | null {
    return RBAC_POLICIES[role] || null;
  }
}
