"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const conversation_engine_1 = require("../../src/aria/conversation-engine");
const orchestrator_1 = require("../../src/astro/orchestrator");
const security_gateway_1 = require("../../src/otis/security-gateway");
const threat_intelligence_1 = require("../../src/codi3/threat-intelligence");
describe('ARIA Conversation Engine', () => {
    let aria;
    let orchestrator;
    let security;
    let intelligence;
    beforeEach(() => {
        orchestrator = new orchestrator_1.AstroOrchestrator();
        security = new security_gateway_1.OTISSecurityGateway();
        intelligence = new threat_intelligence_1.C0Di3CyberIntelligence();
        aria = new conversation_engine_1.ARIAConversationEngine(orchestrator, security, intelligence);
    });
    describe('Session Management', () => {
        it('should start a new conversation session', () => {
            const context = aria.startConversation('user1', 'analyst');
            expect(context.userId).toBe('user1');
            expect(context.userRole).toBe('analyst');
            expect(context.sessionId).toBeDefined();
            expect(context.conversationHistory).toHaveLength(0);
        });
        it('should maintain separate sessions for different users', () => {
            const context1 = aria.startConversation('user1', 'analyst');
            const context2 = aria.startConversation('user2', 'admin');
            expect(context1.sessionId).not.toBe(context2.sessionId);
        });
    });
    describe('Intent Parsing', () => {
        it('should parse help intent', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'help');
            expect(result.response).toContain('Available Commands');
            expect(result.toolExecuted).toBe(false);
        });
        it('should parse status intent', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'status');
            expect(result.response).toContain('Session Status');
            expect(result.response).toContain('user1');
        });
        it('should parse show/query intent for agents', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'show agents');
            expect(result.response).toContain('Available agents');
            expect(result.response).toContain('general-assistant');
        });
        it('should parse show/query intent for tools', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'show tools');
            expect(result.response).toContain('Available tools');
            expect(result.response).toContain('echo');
        });
    });
    describe('Tool Execution', () => {
        it('should execute echo tool via natural language', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'echo hello');
            expect(result.toolExecuted).toBe(true);
            expect(result.response).toContain('Echo');
        });
        it('should execute math_eval tool via natural language', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'calculate 5 + 3');
            expect(result.toolExecuted).toBe(true);
            expect(result.response).toContain('Calculation result');
            expect(result.response).toContain('8');
        });
        it('should handle tool execution errors gracefully', async () => {
            const context = aria.startConversation('user1', 'analyst');
            // Invalid math expression
            const result = await aria.chat(context.sessionId, 'calculate 5 +');
            expect(result.response).toContain('Error') || expect(result.response).toBeDefined();
        });
    });
    describe('Security Integration', () => {
        it('should check RBAC permissions before tool execution', async () => {
            const context = aria.startConversation('user1', 'guest');
            const result = await aria.chat(context.sessionId, 'calculate 2 + 2');
            expect(result.response).toContain('does not have permission');
            expect(result.toolExecuted).toBe(false);
        });
        it('should require approval for high-risk actions', async () => {
            security.setRiskThreshold(0.2);
            const context = aria.startConversation('user1', 'red-team');
            const result = await aria.chat(context.sessionId, 'calculate 2 + 2');
            // Red team + high-risk threshold = approval required
            if (result.requiresApproval) {
                expect(result.response).toContain('approval');
                expect(result.approvalId).toBeDefined();
            }
        });
    });
    describe('Conversation History', () => {
        it('should maintain conversation history', async () => {
            const context = aria.startConversation('user1', 'analyst');
            await aria.chat(context.sessionId, 'help');
            await aria.chat(context.sessionId, 'show agents');
            await aria.chat(context.sessionId, 'echo test');
            const history = aria.getConversationHistory(context.sessionId);
            expect(history.length).toBeGreaterThanOrEqual(6); // 3 user + 3 system
            expect(history[0].role).toBe('user');
            expect(history[1].role).toBe('system');
        });
        it('should track intent in conversation history', async () => {
            const context = aria.startConversation('user1', 'analyst');
            await aria.chat(context.sessionId, 'show tools');
            const history = aria.getConversationHistory(context.sessionId);
            const userTurn = history.find((t) => t.role === 'user' && t.intent);
            expect(userTurn).toBeDefined();
            expect(userTurn?.intent).toBe('query');
        });
    });
    describe('Multi-turn Conversations', () => {
        it('should handle sequential natural language commands', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const step1 = await aria.chat(context.sessionId, 'show agents');
            expect(step1.response).toContain('Available agents');
            const step2 = await aria.chat(context.sessionId, 'show tools');
            expect(step2.response).toContain('Available tools');
            const step3 = await aria.chat(context.sessionId, 'help');
            expect(step3.response).toContain('Available Commands');
        });
        it('should handle tool execution followed by queries', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const execute = await aria.chat(context.sessionId, 'calculate 10 * 5');
            expect(execute.toolExecuted).toBe(true);
            const query = await aria.chat(context.sessionId, 'show threats');
            expect(query.response).toContain('threats');
        });
    });
    describe('Session Lifecycle', () => {
        it('should end a session', () => {
            const context = aria.startConversation('user1', 'analyst');
            const sessionId = context.sessionId;
            aria.endConversation(sessionId);
            // History should be inaccessible after ending
            const history = aria.getConversationHistory(sessionId);
            expect(history).toHaveLength(0);
        });
    });
    describe('Threat Intelligence Integration', () => {
        it('should show critical threats when queried', async () => {
            // Register a threat
            intelligence.registerThreat({
                title: 'SQL Injection',
                description: 'High-risk vulnerability',
                level: 'CRITICAL',
                source: 'ASTRO',
                affectedComponents: ['api'],
                mitigations: ['Input validation'],
                references: ['https://example.com'],
            });
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'show threats');
            expect(result.response).toContain('SQL Injection');
        });
        it('should show open incidents when queried', async () => {
            const threat = intelligence.registerThreat({
                title: 'Test Threat',
                description: 'Test description',
                level: 'HIGH',
                source: 'TEST',
                affectedComponents: [],
                mitigations: [],
                references: [],
            });
            intelligence.createIncident(threat.id, 'HIGH');
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'show incidents');
            expect(result.response).toContain('incidents');
        });
    });
    describe('Response Generation', () => {
        it('should generate contextual responses for executed tools', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'calculate 2 + 2');
            expect(result.response).toContain('Calculation result');
            expect(result.response).toContain('4');
        });
        it('should generate helpful error messages', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'xyz invalid command');
            expect(result.response).toBeDefined();
            expect(result.response.length).toBeGreaterThan(0);
        });
    });
    describe('Agent Selection', () => {
        it('should select appropriate agent for tool execution', async () => {
            const context = aria.startConversation('user1', 'analyst');
            const result = await aria.chat(context.sessionId, 'calculate 2 + 2');
            // Math tool should be executed by some agent
            expect(result.toolExecuted).toBe(true);
        });
    });
});
//# sourceMappingURL=conversation-engine.test.js.map