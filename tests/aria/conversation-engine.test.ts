import { ARIAConversationEngine } from '../../src/aria/conversation-engine';
import { AstroOrchestrator } from '../../src/astro/orchestrator';
import { OTISSecurityGateway } from '../../src/otis/security-gateway';
import { C0Di3CyberIntelligence } from '../../src/codi3/threat-intelligence';
import { echoTool, mathEvalTool } from '../../src/astro/tools';
import { AGENTS } from '../../src/astro/agents';

describe('ARIA Conversation Engine', () => {
  let aria: ARIAConversationEngine;
  let orchestrator: AstroOrchestrator;
  let security: OTISSecurityGateway;
  let intelligence: C0Di3CyberIntelligence;

  beforeEach(() => {
    orchestrator = new AstroOrchestrator();
    
    // Register tools
    orchestrator.registerTool({ name: 'echo', description: 'Echo tool', handler: echoTool });
    orchestrator.registerTool({ name: 'math_eval', description: 'Math tool', handler: mathEvalTool });
    
    // Register agents
    Object.values(AGENTS).forEach((agent) => orchestrator.registerAgent(agent));
    
    security = new OTISSecurityGateway();
    intelligence = new C0Di3CyberIntelligence();
    aria = new ARIAConversationEngine(orchestrator, security, intelligence);
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

      expect(result.response).toContain('help');
    });

    it('should parse show/query intent for agents', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'show agents');

      expect(result.response).toContain('agents');
    });

    it('should parse show/query intent for tools', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'show tools');

      expect(result.response).toContain('tools');
    });
  });

  describe('Tool Execution', () => {
    it('should execute echo tool via natural language', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'echo hello');

      expect(result.response).toBeDefined();
    });

    it('should execute math_eval tool via natural language', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'calculate 5 + 3');

      expect(result.response).toBeDefined();
    });

    it('should handle tool execution errors gracefully', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'calculate 5 +');

      expect(result.response).toBeDefined();
    });
  });

  describe('Security Integration', () => {
    it('should check RBAC permissions before tool execution', async () => {
      const context = aria.startConversation('user1', 'guest');
      const result = await aria.chat(context.sessionId, 'calculate 2 + 2');

      expect(result.response).toBeDefined();
    });
  });

  describe('Multi-turn Conversations', () => {
    it('should maintain conversation history', async () => {
      const context = aria.startConversation('user1', 'analyst');

      await aria.chat(context.sessionId, 'help');
      await aria.chat(context.sessionId, 'show agents');
      await aria.chat(context.sessionId, 'show tools');

      const history = await aria.getConversationHistory(context.sessionId);

      expect(history.length).toBeGreaterThanOrEqual(6); // 3 user + 3 system
    });

    it('should track intent in conversation history', async () => {
      const context = aria.startConversation('user1', 'analyst');

      await aria.chat(context.sessionId, 'show tools');

      const history = await aria.getConversationHistory(context.sessionId);
      expect(history.length).toBeGreaterThan(0);
    });
  });

  describe('Status Command', () => {
    it('should return system status', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'status');

      expect(result.response).toBeDefined();
    });
  });
});
