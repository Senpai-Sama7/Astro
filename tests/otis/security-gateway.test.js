"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const security_gateway_1 = require("../../src/otis/security-gateway");
describe('OTIS Security Gateway', () => {
    let gateway;
    beforeEach(() => {
        gateway = new security_gateway_1.OTISSecurityGateway();
    });
    describe('RBAC', () => {
        it('should allow admin all permissions', () => {
            const policy = security_gateway_1.RBAC_POLICIES['admin'];
            expect(gateway.hasPermission('admin', 'canRegisterTools')).toBe(true);
            expect(gateway.hasPermission('admin', 'canRegisterAgents')).toBe(true);
            expect(gateway.hasPermission('admin', 'canExecuteTools')).toBe(true);
            expect(gateway.hasPermission('admin', 'canViewAudit')).toBe(true);
            expect(gateway.hasPermission('admin', 'canManageUsers')).toBe(true);
            expect(gateway.hasPermission('admin', 'canModifyRisk')).toBe(true);
        });
        it('should restrict analyst to read-only + execute', () => {
            expect(gateway.hasPermission('analyst', 'canRegisterTools')).toBe(false);
            expect(gateway.hasPermission('analyst', 'canRegisterAgents')).toBe(false);
            expect(gateway.hasPermission('analyst', 'canExecuteTools')).toBe(true);
            expect(gateway.hasPermission('analyst', 'canViewAudit')).toBe(true);
            expect(gateway.hasPermission('analyst', 'canManageUsers')).toBe(false);
        });
        it('should restrict guest to no permissions', () => {
            expect(gateway.hasPermission('guest', 'canRegisterTools')).toBe(false);
            expect(gateway.hasPermission('guest', 'canRegisterAgents')).toBe(false);
            expect(gateway.hasPermission('guest', 'canExecuteTools')).toBe(false);
            expect(gateway.hasPermission('guest', 'canViewAudit')).toBe(false);
        });
        it('should allow red-team to register but not view audit', () => {
            expect(gateway.hasPermission('red-team', 'canRegisterTools')).toBe(true);
            expect(gateway.hasPermission('red-team', 'canRegisterAgents')).toBe(true);
            expect(gateway.hasPermission('red-team', 'canViewAudit')).toBe(false);
        });
    });
    describe('Risk Scoring', () => {
        it('should assign base risk for normal actions', () => {
            const score = gateway.calculateRiskScore({
                role: 'analyst',
                action: 'execute_tool',
                resource: 'echo',
            });
            expect(score).toBeGreaterThan(0);
            expect(score).toBeLessThan(1);
        });
        it('should increase risk for red-team actions', () => {
            const analystScore = gateway.calculateRiskScore({
                role: 'analyst',
                action: 'execute_tool',
                resource: 'http_request',
            });
            const redTeamScore = gateway.calculateRiskScore({
                role: 'red-team',
                action: 'execute_tool',
                resource: 'http_request',
            });
            expect(redTeamScore).toBeGreaterThan(analystScore);
        });
        it('should increase risk for tool registration', () => {
            const executeScore = gateway.calculateRiskScore({
                role: 'analyst',
                action: 'execute_tool',
                resource: 'echo',
            });
            const registerScore = gateway.calculateRiskScore({
                role: 'analyst',
                action: 'register_tool',
                resource: 'new_tool',
            });
            expect(registerScore).toBeGreaterThan(executeScore);
        });
        it('should increase risk for sensitive tools', () => {
            const echoScore = gateway.calculateRiskScore({
                role: 'analyst',
                action: 'execute_tool',
                resource: 'echo',
                toolName: 'echo',
            });
            const httpScore = gateway.calculateRiskScore({
                role: 'analyst',
                action: 'execute_tool',
                resource: 'http_request',
                toolName: 'http_request',
            });
            expect(httpScore).toBeGreaterThan(echoScore);
        });
    });
    describe('Audit Logging', () => {
        it('should log actions to the audit log', () => {
            const entry = gateway.logAction({
                userId: 'user123',
                role: 'analyst',
                action: 'execute_tool',
                resource: 'echo',
                decision: 'APPROVED',
                timestamp: new Date(),
            });
            expect(entry.id).toBeDefined();
            expect(entry.signature).toBeDefined();
            expect(entry.userId).toBe('user123');
        });
        it('should maintain append-only property', () => {
            gateway.logAction({
                userId: 'user1',
                role: 'analyst',
                action: 'action1',
                resource: 'resource1',
                decision: 'APPROVED',
            });
            gateway.logAction({
                userId: 'user2',
                role: 'admin',
                action: 'action2',
                resource: 'resource2',
                decision: 'APPROVED',
            });
            const logs = gateway.getAuditLog('admin');
            expect(logs).toHaveLength(2);
            expect(logs[0].userId).toBe('user1');
            expect(logs[1].userId).toBe('user2');
        });
        it('should filter audit log by userId', () => {
            gateway.logAction({
                userId: 'user1',
                role: 'analyst',
                action: 'action1',
                resource: 'resource1',
                decision: 'APPROVED',
            });
            gateway.logAction({
                userId: 'user2',
                role: 'admin',
                action: 'action2',
                resource: 'resource2',
                decision: 'APPROVED',
            });
            const logs = gateway.getAuditLog('admin', { userId: 'user1' });
            expect(logs).toHaveLength(1);
            expect(logs[0].userId).toBe('user1');
        });
        it('should restrict audit log access by role', () => {
            gateway.logAction({
                userId: 'user1',
                role: 'analyst',
                action: 'action1',
                resource: 'resource1',
                decision: 'APPROVED',
            });
            // Guest cannot view audit log
            const guestLogs = gateway.getAuditLog('guest');
            expect(guestLogs).toHaveLength(0);
            // Admin can view audit log
            const adminLogs = gateway.getAuditLog('admin');
            expect(adminLogs).toHaveLength(1);
        });
    });
    describe('Integrity Verification', () => {
        it('should verify audit log integrity', () => {
            gateway.logAction({
                userId: 'user1',
                role: 'analyst',
                action: 'action1',
                resource: 'resource1',
                decision: 'APPROVED',
            });
            const integrity = gateway.verifyAuditLogIntegrity();
            expect(integrity.valid).toBe(true);
            expect(integrity.tamperedCount).toBe(0);
        });
        it('should detect tampered entries', () => {
            const entry = gateway.logAction({
                userId: 'user1',
                role: 'analyst',
                action: 'action1',
                resource: 'resource1',
                decision: 'APPROVED',
            });
            // Tamper with the entry (simulate by directly modifying the log)
            // Note: In real scenario, this would be much harder to do
            const logs = gateway.getAuditLog('admin');
            if (logs[0]) {
                logs[0].signature = 'tampered_signature';
            }
            const integrity = gateway.verifyAuditLogIntegrity();
            expect(integrity.valid).toBe(false);
            expect(integrity.tamperedCount).toBeGreaterThan(0);
        });
    });
    describe('Risk Threshold', () => {
        it('should set risk threshold', () => {
            gateway.setRiskThreshold(0.75);
            expect(gateway.requiresApproval(0.8)).toBe(true);
            expect(gateway.requiresApproval(0.7)).toBe(false);
        });
        it('should reject invalid threshold', () => {
            expect(() => gateway.setRiskThreshold(-0.1)).toThrow();
            expect(() => gateway.setRiskThreshold(1.1)).toThrow();
        });
        it('should require approval for high-risk actions', () => {
            gateway.setRiskThreshold(0.5);
            expect(gateway.requiresApproval(0.6)).toBe(true);
            expect(gateway.requiresApproval(0.4)).toBe(false);
        });
    });
});
//# sourceMappingURL=security-gateway.test.js.map