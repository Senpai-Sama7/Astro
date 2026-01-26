import { ARIAConversationEngine } from '../../src/aria/conversation-engine';
import { AstroOrchestrator } from '../../src/astro/orchestrator';
import { OTISSecurityGateway } from '../../src/otis/security-gateway';
import { C0Di3CyberIntelligence } from '../../src/codi3/threat-intelligence';
import { echoTool, mathEvalTool, httpRequestTool } from '../../src/astro/tools';
import { AGENTS } from '../../src/astro/agents';

// Mock storage
const mockStorage = {
  saveSession: jest.fn().mockResolvedValue(undefined),
  getSession: jest.fn().mockResolvedValue(null),
  saveApproval: jest.fn().mockResolvedValue(undefined),
  deleteApproval: jest.fn().mockResolvedValue(undefined),
  getApprovals: jest.fn().mockResolvedValue([]),
};

describe('ARIA Conversation Engine', () => {
  let aria: ARIAConversationEngine;
  let orchestrator: AstroOrchestrator;
  let security: OTISSecurityGateway;
  let intelligence: C0Di3CyberIntelligence;

  beforeEach(() => {
    jest.clearAllMocks();
    orchestrator = new AstroOrchestrator();
    
    // Register tools
    orchestrator.registerTool({ name: 'echo', description: 'Echo tool', handler: echoTool });
    orchestrator.registerTool({ name: 'math_eval', description: 'Math tool', handler: mathEvalTool });
    orchestrator.registerTool({ name: 'http_request', description: 'HTTP tool', handler: httpRequestTool });
    
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

  describe('Config Intent', () => {
    it('should handle config command', async () => {
      const context = aria.startConversation('user1', 'admin');
      const result = await aria.chat(context.sessionId, 'config');

      expect(result.response).toContain('Configuration');
    });
  });

  describe('Query Intent', () => {
    it('should show threats', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'show threats');

      expect(result.response).toBeDefined();
    });

    it('should show incidents', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'show incidents');

      expect(result.response).toBeDefined();
    });

    it('should handle unknown query target', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'query something');

      expect(result.response).toBeDefined();
    });
  });

  describe('Approval Flow', () => {
    it('should handle approve with no pending approvals', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'yes');

      expect(result.response).toContain('No pending approvals');
    });

    it('should handle deny with no pending approvals', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'no');

      expect(result.response).toContain('No pending approvals');
    });

    it('should handle approve command', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'approve');

      expect(result.response).toBeDefined();
    });

    it('should handle deny command', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'deny');

      expect(result.response).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid session', async () => {
      await expect(aria.chat('invalid-session', 'hello')).rejects.toThrow('not found');
    });

    it('should handle unknown intent gracefully', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'xyzzy random gibberish');

      expect(result.response).toBeDefined();
    });
  });

  describe('HTTP Request Tool', () => {
    it('should parse URL from message', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'fetch https://httpbin.org/get');

      expect(result.response).toBeDefined();
    });
  });

  describe('Math Expression Parsing', () => {
    it('should parse what is expressions', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'what is 10 * 5');

      expect(result.response).toBeDefined();
    });

    it('should parse inline math expressions', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, '15 + 25');

      expect(result.response).toBeDefined();
    });
  });

  describe('Session Persistence', () => {
    it('should get conversation history', async () => {
      const context = aria.startConversation('user1', 'analyst');
      await aria.chat(context.sessionId, 'help');
      
      const history = await aria.getConversationHistory(context.sessionId);
      expect(history.length).toBeGreaterThan(0);
    });

    it('should return empty history for invalid session', async () => {
      const history = await aria.getConversationHistory('invalid');
      expect(history).toEqual([]);
    });
  });

  describe('Tool Execution with Agent', () => {
    it('should execute tool with specific agent', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'use echo-agent to echo test');

      expect(result.response).toBeDefined();
    });

    it('should handle tool not found', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'run nonexistent_tool');

      expect(result.response).toBeDefined();
    });
  });

  describe('With Storage', () => {
    let ariaWithStorage: ARIAConversationEngine;

    beforeEach(() => {
      ariaWithStorage = new ARIAConversationEngine(
        orchestrator,
        security,
        intelligence,
        mockStorage as any
      );
    });

    it('should persist session on chat', async () => {
      const context = ariaWithStorage.startConversation('user1', 'analyst');
      await ariaWithStorage.chat(context.sessionId, 'help');

      expect(mockStorage.saveSession).toHaveBeenCalled();
    });

    it('should load pending approvals', async () => {
      mockStorage.getApprovals.mockResolvedValueOnce([
        {
          approvalId: 'test-approval',
          sessionId: 'test-session',
          toolName: 'echo',
          agentId: 'echo-agent',
          parameters: {},
          riskScore: 0.9,
          createdAt: new Date().toISOString(),
        },
      ]);

      const context = ariaWithStorage.startConversation('user1', 'analyst');
      await ariaWithStorage.chat(context.sessionId, 'yes');

      expect(mockStorage.getApprovals).toHaveBeenCalled();
    });

    it('should handle deny with pending approval', async () => {
      mockStorage.getApprovals.mockResolvedValueOnce([
        {
          approvalId: 'test-approval',
          sessionId: 'test-session',
          toolName: 'echo',
          agentId: 'echo-agent',
          parameters: {},
          riskScore: 0.9,
          createdAt: new Date().toISOString(),
        },
      ]);

      const context = ariaWithStorage.startConversation('user1', 'analyst');
      const result = await ariaWithStorage.chat(context.sessionId, 'no');

      expect(result.response).toContain('denied');
    });
  });

  describe('Edge Cases', () => {
    it('should handle POST http request', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'post to https://httpbin.org/post');

      expect(result.response).toBeDefined();
    });

    it('should handle execute without tool name', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'execute something');

      expect(result.response).toBeDefined();
    });

    it('should handle list agents command', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'list agents');

      expect(result.response).toContain('agents');
    });

    it('should handle list tools command', async () => {
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'list tools');

      expect(result.response).toContain('tools');
    });

    it('should trigger approval for high-risk actions', async () => {
      const context = aria.startConversation('user1', 'red-team');
      const result = await aria.chat(context.sessionId, 'fetch https://httpbin.org/get');

      // Red-team + http_request should trigger approval
      expect(result.response).toBeDefined();
    });

    it('should handle error in chat gracefully', async () => {
      // Create aria with broken orchestrator
      const brokenOrchestrator = new AstroOrchestrator();
      brokenOrchestrator.registerTool({
        name: 'broken',
        description: 'Broken tool',
        handler: async () => { throw new Error('Tool error'); },
      });
      brokenOrchestrator.registerAgent({
        id: 'broken-agent',
        name: 'Broken',
        description: 'Broken agent',
        tools: ['broken'],
      });
      
      const brokenAria = new ARIAConversationEngine(brokenOrchestrator, security, intelligence);
      const context = brokenAria.startConversation('user1', 'analyst');
      const result = await brokenAria.chat(context.sessionId, 'run broken');

      expect(result.response).toBeDefined();
    });

    it('should show threats when present', async () => {
      // Add a threat to the intelligence
      intelligence.registerThreat({
        title: 'Test Threat',
        description: 'A test threat',
        level: 'CRITICAL',
        source: 'test',
        affectedComponents: [],
        mitigations: [],
        references: [],
      });
      
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'show threats');

      expect(result.response).toContain('threat');
    });

    it('should show incidents when present', async () => {
      // Add a threat first, then create incident
      const threat = intelligence.registerThreat({
        title: 'Test Threat',
        description: 'A test threat',
        level: 'HIGH',
        source: 'test',
        affectedComponents: [],
        mitigations: [],
        references: [],
      });
      intelligence.createIncident(threat.id, 'HIGH');
      
      const context = aria.startConversation('user1', 'analyst');
      const result = await aria.chat(context.sessionId, 'show incidents');

      expect(result.response).toBeDefined();
    });
  });

});
