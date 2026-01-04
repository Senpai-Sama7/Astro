import { AstroOrchestrator, ToolContext } from '../../src/astro/orchestrator';
import { echoTool, httpRequestTool, mathEvalTool } from '../../src/astro/tools';
import { AGENTS } from '../../src/astro/agents';

describe('AstroOrchestrator', () => {
  let orchestrator: AstroOrchestrator;

  beforeEach(() => {
    orchestrator = new AstroOrchestrator();
  });

  describe('Tool Registration', () => {
    it('should register a tool', () => {
      orchestrator.registerTool({
        name: 'test-tool',
        description: 'A test tool',
        handler: async () => ({ ok: true, elapsedMs: 0 }),
      });

      const tools = orchestrator.listTools();
      expect(tools).toHaveLength(1);
      expect(tools[0].name).toBe('test-tool');
    });

    it('should prevent duplicate tool registration', () => {
      orchestrator.registerTool({
        name: 'test-tool',
        description: 'A test tool',
        handler: async () => ({ ok: true, elapsedMs: 0 }),
      });

      expect(() => {
        orchestrator.registerTool({
          name: 'test-tool',
          description: 'Another test tool',
          handler: async () => ({ ok: true, elapsedMs: 0 }),
        });
      }).toThrow(`Tool 'test-tool' is already registered`);
    });

    it('should require tool name and handler', () => {
      expect(() => {
        orchestrator.registerTool({
          name: '',
          description: 'A test tool',
          handler: async () => ({ ok: true, elapsedMs: 0 }),
        });
      }).toThrow();
    });
  });

  describe('Agent Registration', () => {
    it('should register an agent', () => {
      orchestrator.registerAgent({
        id: 'test-agent',
        name: 'Test Agent',
        description: 'A test agent',
        tools: ['test-tool'],
      });

      const agents = orchestrator.listAgents();
      expect(agents).toHaveLength(1);
      expect(agents[0].id).toBe('test-agent');
    });

    it('should require agent id and name', () => {
      expect(() => {
        orchestrator.registerAgent({
          id: '',
          name: 'Test Agent',
          description: 'A test agent',
          tools: ['test-tool'],
        });
      }).toThrow();
    });

    it('should require at least one tool', () => {
      expect(() => {
        orchestrator.registerAgent({
          id: 'test-agent',
          name: 'Test Agent',
          description: 'A test agent',
          tools: [],
        });
      }).toThrow('Agent must have at least one tool');
    });
  });

  describe('Tool Orchestration', () => {
    beforeEach(() => {
      orchestrator.registerTool({
        name: 'echo',
        description: 'Echo tool',
        handler: echoTool,
      });

      orchestrator.registerAgent({
        id: 'test-agent',
        name: 'Test Agent',
        description: 'A test agent',
        tools: ['echo'],
      });
    });

    it('should orchestrate a successful tool call', async () => {
      const result = await orchestrator.orchestrateToolCall({
        agentId: 'test-agent',
        toolName: 'echo',
        input: { message: 'hello' },
        userId: 'user123',
      });

      expect(result.result.ok).toBe(true);
      expect(result.result.data).toEqual({
        echo: { message: 'hello' },
        context: {
          requestId: expect.any(String),
          profile: 'core',
        },
      });
      expect(result.result.elapsedMs).toBeGreaterThanOrEqual(0);
    });

    it('should fail if agent does not exist', async () => {
      await expect(
        orchestrator.orchestrateToolCall({
          agentId: 'nonexistent-agent',
          toolName: 'echo',
          input: {},
        })
      ).rejects.toThrow('Agent \'nonexistent-agent\' is not registered');
    });

    it('should fail if agent does not have access to tool', async () => {
      orchestrator.registerTool({
        name: 'forbidden-tool',
        description: 'A tool the agent cannot access',
        handler: async () => ({ ok: true, elapsedMs: 0 }),
      });

      await expect(
        orchestrator.orchestrateToolCall({
          agentId: 'test-agent',
          toolName: 'forbidden-tool',
          input: {},
        })
      ).rejects.toThrow('is not allowed to use tool');
    });

    it('should fail if tool does not exist', async () => {
      orchestrator.registerAgent({
        id: 'another-agent',
        name: 'Another Agent',
        description: 'Another test agent',
        tools: ['nonexistent-tool'],
      });

      await expect(
        orchestrator.orchestrateToolCall({
          agentId: 'another-agent',
          toolName: 'nonexistent-tool',
          input: {},
        })
      ).rejects.toThrow('Tool \'nonexistent-tool\' is not registered');
    });
  });

  describe('Events', () => {
    beforeEach(() => {
      orchestrator.registerTool({
        name: 'echo',
        description: 'Echo tool',
        handler: echoTool,
      });

      orchestrator.registerAgent({
        id: 'test-agent',
        name: 'Test Agent',
        description: 'A test agent',
        tools: ['echo'],
      });
    });

    it('should emit result event on successful tool call', async () => {
      const resultHandler = jest.fn();
      orchestrator.on('result', resultHandler);

      await orchestrator.orchestrateToolCall({
        agentId: 'test-agent',
        toolName: 'echo',
        input: { message: 'test' },
      });

      expect(resultHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          agentId: 'test-agent',
          toolName: 'echo',
          result: expect.objectContaining({ ok: true }),
        })
      );
    });

    it('should emit error event on failed tool call', async () => {
      const errorHandler = jest.fn();
      orchestrator.on('error', errorHandler);

      try {
        await orchestrator.orchestrateToolCall({
          agentId: 'test-agent',
          toolName: 'nonexistent-tool',
          input: {},
        });
      } catch {
        // Expected
      }

      expect(errorHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          requestId: expect.any(String),
          error: expect.stringContaining('not registered'),
        })
      );
    });
  });
});
