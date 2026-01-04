import express, { Router } from 'express';
import { AstroOrchestrator, ToolInput } from './orchestrator';
import { echoTool, httpRequestTool, mathEvalTool } from './tools';
import { AGENTS } from './agents';
import { logger } from '../services/logger';

export function createAstroRouter(orchestrator: AstroOrchestrator): Router {
  const router = express.Router();

  // Register built-in tools at router creation time
  orchestrator.registerTool({
    name: 'echo',
    description: 'Echo tool - returns input as-is for testing',
    handler: echoTool,
  });

  orchestrator.registerTool({
    name: 'http_request',
    description:
      'Make HTTP requests to whitelisted domains. Input: { url, method?, headers?, data? }',
    handler: httpRequestTool,
  });

  orchestrator.registerTool({
    name: 'math_eval',
    description:
      'Evaluate mathematical expressions. Input: { expression }. Supports +, -, *, /, parentheses.',
    handler: mathEvalTool,
  });

  // Register predefined agents
  Object.values(AGENTS).forEach((agent) => {
    orchestrator.registerAgent(agent);
  });

  // Set up event listeners for logging
  orchestrator.on('result', (payload) => {
    logger.info('Orchestration result', {
      requestId: payload.requestId,
      agentId: payload.agentId,
      toolName: payload.toolName,
      ok: payload.result.ok,
      elapsedMs: payload.result.elapsedMs,
    });
  });

  orchestrator.on('error', (payload) => {
    logger.warn('Orchestration error', {
      requestId: payload.requestId,
      error: payload.error,
    });
  });

  /**
   * POST /api/v1/astro/execute
   * Execute a tool for a given agent.
   * Body: { agentId: string, toolName: string, input: object, userId?: string, metadata?: object }
   */
  router.post('/execute', async (req, res, next) => {
    try {
      const { agentId, toolName, input, userId, metadata } = req.body;

      if (!agentId || !toolName || !input) {
        return res.status(400).json({
          error: 'Missing required fields: agentId, toolName, input',
        });
      }

      const result = await orchestrator.orchestrateToolCall({
        agentId,
        toolName,
        input: input as ToolInput,
        userId,
        profile: (process.env.PROFILE as 'core' | 'cyber') || 'core',
        metadata,
      });

      return res.json(result);
    } catch (error) {
      next(error);
    }
  });

  /**
   * GET /api/v1/astro/agents
   * List all available agents.
   */
  router.get('/agents', (req, res) => {
    const agents = orchestrator.listAgents();
    res.json({
      agents: agents.map((agent) => ({
        id: agent.id,
        name: agent.name,
        description: agent.description,
        tools: agent.tools,
        routingHint: agent.routingHint,
      })),
    });
  });

  /**
   * GET /api/v1/astro/tools
   * List all available tools.
   */
  router.get('/tools', (req, res) => {
    const tools = orchestrator.listTools();
    res.json({
      tools: tools.map((tool) => ({
        name: tool.name,
        description: tool.description,
        schema: tool.schema,
      })),
    });
  });

  /**
   * GET /api/v1/astro/agents/:agentId
   * Get details about a specific agent.
   */
  router.get('/agents/:agentId', (req, res) => {
    const { agentId } = req.params;
    const agents = orchestrator.listAgents();
    const agent = agents.find((a) => a.id === agentId);

    if (!agent) {
      return res.status(404).json({ error: `Agent '${agentId}' not found` });
    }

    res.json({ agent });
  });

  return router;
}
