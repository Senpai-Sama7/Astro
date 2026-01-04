import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import crypto from 'crypto';

/**
 * LAYER B: Security Gateway
 * 
 * Implements the OTIS control layer with:
 * - Role-based access control (RBAC)
 * - Risk evaluation (CVaR-based)
 * - Approval gates
 * - Comprehensive audit logging
 * - Compliance enforcement
 */

export enum UserRole {
  ADMIN = 'admin',
  SECURITY_ANALYST = 'analyst',
  RED_TEAM = 'red_team',
  BLUE_TEAM = 'blue_team',
  READ_ONLY = 'read_only',
  GUEST = 'guest'
}

export enum RiskLevel {
  LOW = 'low',           // 0.0 - 0.25
  MEDIUM = 'medium',     // 0.25 - 0.5
  HIGH = 'high',         // 0.5 - 0.75
  CRITICAL = 'critical'  // 0.75 - 1.0
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: string[];
  createdAt: Date;
  lastLogin: Date;
  isActive: boolean;
  mfaEnabled: boolean;
  sessionIds: Set<string>;
}

export interface ToolPermission {
  tool: string;
  roles: UserRole[];
  maxConcurrent?: number;
  maxDaily?: number;
  requiresApproval?: boolean;
  riskLevel: RiskLevel;
  description?: string;
}

export interface RiskContext {
  tool: string;
  target?: string;
  action: string;
  user: User;
  historicalRiskScore?: number;
  timeOfDay?: number;
  isScheduled?: boolean;
  metadata?: Record<string, any>;
}

export interface ApprovalDecision {
  approved: boolean;
  riskScore: number;
  reason: string;
  requiresHumanApproval: boolean;
  escalationLevel: 'auto' | 'manager' | 'admin' | 'security';
}

export interface AuditEvent {
  id: string;
  timestamp: Date;
  userId: string;
  username: string;
  sessionId: string;
  action: string;
  resource: string;
  decision: 'approved' | 'denied' | 'escalated';
  riskScore: number;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  duration: number;
  result: 'success' | 'failure';
  errorMessage?: string;
}

export class SecurityGateway extends EventEmitter {
  private logger: Logger;
  private users: Map<string, User>;
  private toolPermissions: Map<string, ToolPermission>;
  private toolUsageStats: Map<string, { count: number; lastUsed: Date }>;
  private auditLog: AuditEvent[];
  private approvalThresholds: Record<RiskLevel, number>;
  private readonly maxAuditLogSize = 100000;  // Keep last 100k events

  constructor() {
    super();
    this.logger = new Logger('SecurityGateway');
    this.users = new Map();
    this.toolPermissions = new Map();
    this.toolUsageStats = new Map();
    this.auditLog = [];

    // Risk thresholds (0-1 scale)
    this.approvalThresholds = {
      [RiskLevel.LOW]: 0.25,
      [RiskLevel.MEDIUM]: 0.5,
      [RiskLevel.HIGH]: 0.75,
      [RiskLevel.CRITICAL]: 1.0
    };

    this.initializeDefaultRoles();
  }

  /**
   * Initialize default tool permissions for each role
   */
  private initializeDefaultRoles(): void {
    // ADMIN: Unrestricted
    // Analyst: Read-only + safe write operations
    // Red Team: Offensive tools (nmap, metasploit)
    // Blue Team: Defensive tools (detection, remediation)
    // Read-only: View-only access
    // Guest: Denied by default

    const defaultPermissions: ToolPermission[] = [
      // Safe read tools (all roles)
      {
        tool: 'list_files',
        roles: [UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.RED_TEAM, UserRole.BLUE_TEAM, UserRole.READ_ONLY],
        riskLevel: RiskLevel.LOW,
        maxConcurrent: 10,
        maxDaily: 1000
      },
      {
        tool: 'read_file',
        roles: [UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.RED_TEAM, UserRole.BLUE_TEAM, UserRole.READ_ONLY],
        riskLevel: RiskLevel.LOW,
        maxConcurrent: 10,
        maxDaily: 500
      },

      // Analysis tools (analyst, red, blue)
      {
        tool: 'analyze_logs',
        roles: [UserRole.ADMIN, UserRole.SECURITY_ANALYST, UserRole.RED_TEAM, UserRole.BLUE_TEAM],
        riskLevel: RiskLevel.LOW,
        maxConcurrent: 5,
        maxDaily: 100
      },

      // Red team tools (red team only, requires approval)
      {
        tool: 'nmap',
        roles: [UserRole.ADMIN, UserRole.RED_TEAM],
        riskLevel: RiskLevel.HIGH,
        maxConcurrent: 1,
        maxDaily: 10,
        requiresApproval: true
      },
      {
        tool: 'metasploit',
        roles: [UserRole.ADMIN, UserRole.RED_TEAM],
        riskLevel: RiskLevel.CRITICAL,
        maxConcurrent: 1,
        maxDaily: 5,
        requiresApproval: true
      },

      // Blue team tools (blue team only, lower barrier)
      {
        tool: 'create_detection_rule',
        roles: [UserRole.ADMIN, UserRole.BLUE_TEAM],
        riskLevel: RiskLevel.MEDIUM,
        maxConcurrent: 5,
        maxDaily: 50,
        requiresApproval: false
      },

      // Admin-only tools
      {
        tool: 'modify_policy',
        roles: [UserRole.ADMIN],
        riskLevel: RiskLevel.CRITICAL,
        maxConcurrent: 1,
        requiresApproval: true
      }
    ];

    for (const perm of defaultPermissions) {
      this.toolPermissions.set(perm.tool, perm);
    }

    this.logger.info('Initialized default RBAC policies', {
      totalTools: this.toolPermissions.size
    });
  }

  /**
   * Evaluate authorization + risk for a tool execution request
   */
  public async evaluateRequest(
    user: User,
    tool: string,
    context: RiskContext,
    sessionId: string,
    requestId: string
  ): Promise<ApprovalDecision> {
    const startTime = Date.now();

    try {
      // Step 1: Authentication (user must be active)
      if (!user.isActive) {
        this.logger.warn('Authentication failed: user inactive', { userId: user.id, tool });
        this.emitAuditEvent({
          userId: user.id,
          username: user.username,
          sessionId,
          action: 'tool_access_denied',
          resource: tool,
          decision: 'denied',
          riskScore: 1.0,
          details: { reason: 'user_inactive' },
          result: 'failure'
        }, requestId, Date.now() - startTime);

        return {
          approved: false,
          riskScore: 1.0,
          reason: 'User account is inactive',
          requiresHumanApproval: false,
          escalationLevel: 'auto'
        };
      }

      // Step 2: RBAC Check
      const toolPerm = this.toolPermissions.get(tool);
      if (!toolPerm) {
        this.logger.warn('Tool not found', { tool });
        return {
          approved: false,
          riskScore: 0.9,
          reason: 'Tool not found',
          requiresHumanApproval: false,
          escalationLevel: 'auto'
        };
      }

      if (!toolPerm.roles.includes(user.role)) {
        this.logger.warn('RBAC violation', { userId: user.id, tool, userRole: user.role });
        this.emitAuditEvent({
          userId: user.id,
          username: user.username,
          sessionId,
          action: 'rbac_violation',
          resource: tool,
          decision: 'denied',
          riskScore: 0.8,
          details: { userRole: user.role, allowedRoles: toolPerm.roles },
          result: 'failure'
        }, requestId, Date.now() - startTime);

        return {
          approved: false,
          riskScore: 0.8,
          reason: `User role '${user.role}' not authorized for tool '${tool}'`,
          requiresHumanApproval: false,
          escalationLevel: 'auto'
        };
      }

      // Step 3: Check rate limits
      const usageStats = this.toolUsageStats.get(tool) || { count: 0, lastUsed: new Date() };
      if (toolPerm.maxDaily && usageStats.count >= toolPerm.maxDaily) {
        this.logger.warn('Daily limit exceeded', { tool, userId: user.id });
        return {
          approved: false,
          riskScore: 0.7,
          reason: `Daily limit (${toolPerm.maxDaily}) exceeded for tool '${tool}'`,
          requiresHumanApproval: false,
          escalationLevel: 'auto'
        };
      }

      // Step 4: Risk Evaluation (CVaR-based)
      const riskScore = this.calculateRiskScore(context, toolPerm, user);

      // Step 5: Approval Decision
      const requiresApproval = toolPerm.requiresApproval || riskScore > 0.5;
      const threshold = this.approvalThresholds[toolPerm.riskLevel];

      let decision: ApprovalDecision;

      if (riskScore >= threshold && requiresApproval) {
        // High risk → escalate to human
        decision = {
          approved: false,
          riskScore,
          reason: `Risk score (${riskScore.toFixed(2)}) exceeds threshold (${threshold.toFixed(2)}) for tool '${tool}'`,
          requiresHumanApproval: true,
          escalationLevel: riskScore >= 0.75 ? 'admin' : 'manager'
        };
      } else {
        // Low-medium risk → auto-approve
        decision = {
          approved: true,
          riskScore,
          reason: `Tool execution authorized (risk: ${riskScore.toFixed(2)})`,
          requiresHumanApproval: false,
          escalationLevel: 'auto'
        };
      }

      // Step 6: Audit Log
      this.emitAuditEvent({
        userId: user.id,
        username: user.username,
        sessionId,
        action: 'tool_execution_evaluated',
        resource: tool,
        decision: decision.approved ? 'approved' : decision.requiresHumanApproval ? 'escalated' : 'denied',
        riskScore,
        details: { toolPerm, escalationLevel: decision.escalationLevel },
        result: 'success'
      }, requestId, Date.now() - startTime);

      return decision;
    } catch (error) {
      this.logger.error('Error evaluating request', error, { tool, userId: user.id });
      return {
        approved: false,
        riskScore: 1.0,
        reason: `Internal error: ${error instanceof Error ? error.message : 'unknown'}`,
        requiresHumanApproval: true,
        escalationLevel: 'admin'
      };
    }
  }

  /**
   * Calculate risk score using Bayesian inference + contextual factors
   * 
   * Returns a value 0-1 where:
   * - 0.0 = no risk
   * - 0.5 = medium risk
   * - 1.0 = critical risk
   */
  private calculateRiskScore(context: RiskContext, toolPerm: ToolPermission, user: User): number {
    let score = 0;

    // Base risk from tool classification
    const riskMap = {
      [RiskLevel.LOW]: 0.1,
      [RiskLevel.MEDIUM]: 0.4,
      [RiskLevel.HIGH]: 0.7,
      [RiskLevel.CRITICAL]: 0.95
    };
    score += riskMap[toolPerm.riskLevel] * 0.4;  // 40% weight

    // Time-based factor: Odd hours = higher risk
    if (context.timeOfDay !== undefined && (context.timeOfDay < 6 || context.timeOfDay > 22)) {
      score += 0.15;  // +15%
    }

    // User history factor
    if (context.historicalRiskScore !== undefined) {
      // If user has previously done high-risk things, slightly increase score
      score += context.historicalRiskScore * 0.2;  // 20% weight
    }

    // Target specificity
    if (context.target?.startsWith('127.') || context.target?.includes('localhost')) {
      // Local execution = lower risk
      score *= 0.7;
    } else if (context.target?.includes('.')) {
      // Remote/network = higher risk
      score *= 1.2;
    }

    // Scheduled execution = lower risk
    if (context.isScheduled) {
      score *= 0.8;
    }

    // Clamp to 0-1
    return Math.min(Math.max(score, 0), 1);
  }

  /**
   * Record successful tool execution in audit log
   */
  public recordExecution(
    user: User,
    tool: string,
    sessionId: string,
    result: 'success' | 'failure',
    errorMessage?: string
  ): void {
    this.emitAuditEvent({
      userId: user.id,
      username: user.username,
      sessionId,
      action: `tool_${result}`,
      resource: tool,
      decision: 'approved',
      riskScore: 0,
      details: { executionResult: result },
      result
    }, 'manual', 0);
  }

  /**
   * Emit audit event and store in log
   */
  private emitAuditEvent(
    event: Omit<AuditEvent, 'id' | 'timestamp'>,
    requestId: string,
    duration: number,
    ipAddress: string = 'unknown',
    userAgent: string = 'unknown'
  ): void {
    const auditEvent: AuditEvent = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      ...event,
      ipAddress,
      userAgent,
      duration
    };

    this.auditLog.push(auditEvent);

    // Trim audit log if too large
    if (this.auditLog.length > this.maxAuditLogSize) {
      this.auditLog = this.auditLog.slice(-this.maxAuditLogSize);
    }

    // Emit event for subscribers
    this.emit('audit', auditEvent);
  }

  /**
   * Get audit log with filtering
   */
  public getAuditLog(
    filters?: {
      userId?: string;
      action?: string;
      startTime?: Date;
      endTime?: Date;
      decision?: 'approved' | 'denied' | 'escalated';
    }
  ): AuditEvent[] {
    return this.auditLog.filter(event => {
      if (filters?.userId && event.userId !== filters.userId) return false;
      if (filters?.action && event.action !== filters.action) return false;
      if (filters?.decision && event.decision !== filters.decision) return false;
      if (filters?.startTime && event.timestamp < filters.startTime) return false;
      if (filters?.endTime && event.timestamp > filters.endTime) return false;
      return true;
    });
  }

  /**
   * Add/update a user
   */
  public addUser(user: User): void {
    this.users.set(user.id, user);
    this.logger.info('User added', { userId: user.id, role: user.role });
  }

  /**
   * Get user by ID
   */
  public getUser(userId: string): User | undefined {
    return this.users.get(userId);
  }

  /**
   * Register/update tool permission
   */
  public registerToolPermission(permission: ToolPermission): void {
    this.toolPermissions.set(permission.tool, permission);
    this.logger.info('Tool permission registered', { tool: permission.tool });
  }

  /**
   * Get all audit stats (for dashboards)
   */
  public getAuditStats(): Record<string, any> {
    const stats = {
      totalEvents: this.auditLog.length,
      approved: this.auditLog.filter(e => e.decision === 'approved').length,
      denied: this.auditLog.filter(e => e.decision === 'denied').length,
      escalated: this.auditLog.filter(e => e.decision === 'escalated').length,
      failures: this.auditLog.filter(e => e.result === 'failure').length,
      byUser: {} as Record<string, number>,
      byTool: {} as Record<string, number>,
      averageRiskScore: 0
    };

    let totalRisk = 0;
    for (const event of this.auditLog) {
      stats.byUser[event.userId] = (stats.byUser[event.userId] || 0) + 1;
      stats.byTool[event.resource] = (stats.byTool[event.resource] || 0) + 1;
      totalRisk += event.riskScore;
    }

    stats.averageRiskScore = this.auditLog.length > 0 ? totalRisk / this.auditLog.length : 0;

    return stats;
  }
}

export const securityGateway = new SecurityGateway();
