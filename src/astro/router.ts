import express, { Router } from 'express';
import { AstroOrchestrator, ToolInput } from './orchestrator';
import {
  echoTool,
  httpRequestTool,
  mathEvalTool,
  webSearchTool,
  contentExtractTool,
  readFileTool,
  writeFileTool,
  listDirTool,
  gitStatusTool,
  gitDiffTool,
  runTestsTool,
  lintCodeTool,
  saveKnowledgeTool,
  retrieveKnowledgeTool,
} from './tools';
import { AGENTS } from './agents';
import { logger } from '../services/logger';
import { authenticateRequest } from '../middleware/auth';

export function createAstroRouter(orchestrator: AstroOrchestrator): Router {
  const router = express.Router();
  router.use(authenticateRequest);

  // Register built-in tools at router creation time
  orchestrator.registerTool({
    name: 'echo',
    description: 'Echo tool - returns input as-is for testing',
    handler: echoTool,
  });

  orchestrator.registerTool({
    name: 'http_request',
    description: 'Make HTTP requests to whitelisted domains. Input: { url, method?, headers?, data? }',
    handler: httpRequestTool,
  });

  orchestrator.registerTool({
    name: 'math_eval',
    description: 'Evaluate mathematical expressions. Input: { expression }. Supports +, -, *, /, parentheses.',
    handler: mathEvalTool,
  });

  // Research Agent tools
  orchestrator.registerTool({
    name: 'web_search',
    description: 'Search the web using DuckDuckGo. Input: { query, maxResults? }',
    handler: webSearchTool,
  });

  orchestrator.registerTool({
    name: 'content_extract',
    description: 'Extract text content from a URL. Input: { url }',
    handler: contentExtractTool,
  });

  // FileSystem Agent tools
  orchestrator.registerTool({
    name: 'read_file',
    description: 'Read file contents. Input: { path }',
    handler: readFileTool,
  });

  orchestrator.registerTool({
    name: 'write_file',
    description: 'Write content to file. Input: { path, content }',
    handler: writeFileTool,
  });

  orchestrator.registerTool({
    name: 'list_dir',
    description: 'List directory contents. Input: { path? }',
    handler: listDirTool,
  });

  // Git Agent tools
  orchestrator.registerTool({
    name: 'git_status',
    description: 'Get git status. Input: { cwd? }',
    handler: gitStatusTool,
  });

  orchestrator.registerTool({
    name: 'git_diff',
    description: 'Get git diff. Input: { cwd?, file? }',
    handler: gitDiffTool,
  });

  // Test Agent tools
  orchestrator.registerTool({
    name: 'run_tests',
    description: 'Run test suite. Input: { command?, cwd? }',
    handler: runTestsTool,
  });

  // Analysis Agent tools
  orchestrator.registerTool({
    name: 'lint_code',
    description: 'Run linter on code. Input: { path?, linter? }',
    handler: lintCodeTool,
  });

  // Knowledge Agent tools
  orchestrator.registerTool({
    name: 'save_knowledge',
    description: 'Save knowledge to persistent storage. Input: { key, value }',
    handler: saveKnowledgeTool,
  });

  orchestrator.registerTool({
    name: 'retrieve_knowledge',
    description: 'Retrieve knowledge from storage. Input: { key? }',
    handler: retrieveKnowledgeTool,
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
