import 'express-async-errors';
import dotenv from 'dotenv';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { createServer } from 'http';
import rateLimit from 'express-rate-limit';
import path from 'path';
import { logger } from './services/logger';
import { AstroOrchestrator } from './astro/orchestrator';
import { createAstroRouter } from './astro/router';
import { ARIAConversationEngine, setWorkflowEngine, setLLMManager } from './aria/conversation-engine';
import { createConversationRouter } from './aria/router';
import { OTISSecurityGateway } from './otis/security-gateway';
import { C0Di3CyberIntelligence } from './codi3/threat-intelligence';
import { SQLiteStorage } from './services/storage';
import { createAuthRouter } from './auth/router';
import { WebSocketServer } from './services/websocket';
import { PluginLoader } from './plugins/plugin-loader';
import { WorkflowEngine, createWorkflowRouter } from './workflows/workflow-engine';
import { createMetricsRouter, metricsCollector, dashboardHtml } from './services/metrics';
import { llmManager } from './services/llm';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const NODE_ENV = process.env.NODE_ENV || 'development';
const PROFILE = process.env.PROFILE || 'core';
const DATA_PATH =
  process.env.DATA_PATH || path.join(process.cwd(), 'data', 'astro.db');

let orchestrator: AstroOrchestrator;
let securityGateway: OTISSecurityGateway;
let threatIntelligence: C0Di3CyberIntelligence;
let conversationEngine: ARIAConversationEngine;
let server: ReturnType<typeof createServer>;
let wsServer: WebSocketServer;
let pluginLoader: PluginLoader;
let workflowEngine: WorkflowEngine;

// Middleware
app.use(helmet({ contentSecurityPolicy: false })); // Allow inline scripts for simple UI
app.use(cors({ origin: process.env.SECURITY_CORS_ORIGIN }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// Serve the simple web interface
app.use(express.static(path.join(__dirname, '..', 'public')));

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/v1/aria', apiLimiter);
app.use('/api/v1/astro', apiLimiter);

// Logging middleware with metrics
app.use((req, res, next) => {
  const start = Date.now();
  metricsCollector.recordRequest(req.path);
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info('HTTP Request', {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration,
    });
  });
  next();
});

// Health check endpoint
app.get('/api/v1/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: NODE_ENV,
    profile: PROFILE,
    uptime: process.uptime(),
  });
});

// Version endpoint
app.get('/api/v1/version', (req, res) => {
  res.json({
    version: '1.0.0',
    name: 'ASTRO Ultimate System',
    profile: PROFILE,
    layers: {
      a_astro: { status: 'active', description: 'Tool Orchestration' },
      b_otis: { status: 'active', description: 'Security (RBAC, CVaR, Audit)' },
      c_codi3: { status: 'active', description: 'Cyber Intelligence' },
      d_aria: { status: 'active', description: 'Natural Language Conversation' },
    },
    features: [
      'Tool Orchestration with Agent Registry',
      'Plugin System for Custom Tools',
      'Multi-model LLM Support (OpenAI, Anthropic, Ollama)',
      'Workflow Automation',
      'Metrics Dashboard',
      'Role-Based Access Control (6 roles)',
      'CVaR Risk Scoring',
      'Immutable Audit Logging with HMAC',
      'Threat Management & Incident Tracking',
      'MITRE ATT&CK Knowledge Base',
      'Multi-turn Natural Language Interface',
      'WebSocket Real-time Communication',
    ],
    llmProviders: llmManager.list(),
    plugins: pluginLoader?.listPlugins().map(p => p.manifest.name) || [],
  });
});

// Auth routes
const authRouter = createAuthRouter();
app.use('/api/v1/auth', authRouter);

async function bootstrap() {
  const storage = new SQLiteStorage(DATA_PATH);
  await storage.init();

  // Create core systems
  orchestrator = new AstroOrchestrator(); // Layer A: ASTRO
  securityGateway = new OTISSecurityGateway(storage); // Layer B: OTIS
  await securityGateway.init();
  threatIntelligence = new C0Di3CyberIntelligence(storage); // Layer C: C0Di3
  await threatIntelligence.init();
  conversationEngine = new ARIAConversationEngine( // Layer D: ARIA
    orchestrator,
    securityGateway,
    threatIntelligence,
    storage
  );

  // Initialize Plugin System
  pluginLoader = new PluginLoader();
  const plugins = await pluginLoader.loadAllPlugins();
  plugins.flatMap(p => p.tools).forEach(tool => {
    try { orchestrator.registerTool(tool); } catch { /* already registered */ }
  });
  logger.info(`Loaded ${plugins.length} plugins with ${plugins.flatMap(p => p.tools).length} tools`);

  // Initialize Workflow Engine
  workflowEngine = new WorkflowEngine();
  setWorkflowEngine(workflowEngine);
  setLLMManager(llmManager);
  logger.info(`Loaded ${workflowEngine.list().length} workflows`);

  // Mount ASTRO Layer A router
  const astroRouter = createAstroRouter(orchestrator);
  app.use('/api/v1/astro', astroRouter);

  // Mount ARIA Layer D router (conversational interface)
  const ariaRouter = createConversationRouter(conversationEngine);
  app.use('/api/v1/aria', ariaRouter);

  // Mount Workflow router
  const workflowRouter = createWorkflowRouter(workflowEngine, orchestrator);
  app.use('/api/v1/workflows', workflowRouter);

  // Mount Metrics router
  const metricsRouter = createMetricsRouter();
  app.use('/api/v1/metrics', metricsRouter);

  // Metrics Dashboard HTML
  app.get('/dashboard', (_, res) => {
    res.setHeader('Content-Type', 'text/html');
    res.send(dashboardHtml);
  });

  // LLM endpoint
  app.post('/api/v1/llm/chat', async (req, res) => {
    try {
      const { messages, provider, model, temperature, maxTokens } = req.body;
      const response = await llmManager.chat(messages, { provider, model, temperature, maxTokens });
      res.json(response);
    } catch (e) {
      res.status(400).json({ error: String(e) });
    }
  });

  app.get('/api/v1/llm/providers', (_, res) => res.json(llmManager.list()));

  // Start server
  server = createServer(app);

  // Initialize WebSocket server
  wsServer = new WebSocketServer(server, conversationEngine);
  logger.info('WebSocket server initialized', { path: '/ws' });

  server.listen(PORT, () => {
    logger.info('✅ Ultimate System Started', {
      port: PORT,
      environment: NODE_ENV,
      profile: PROFILE,
      layers: [
        '✓ Layer A: ASTRO (Orchestration)',
        '✓ Layer B: OTIS (Security)',
        '✓ Layer C: C0Di3 (Cyber Intelligence)',
        '✓ Layer D: ARIA (Conversational Interface)',
      ],
      newFeatures: [
        '✓ Plugin System',
        '✓ Multi-model LLM',
        '✓ Workflow Automation',
        '✓ Metrics Dashboard',
      ],
      mainEndpoint: `POST /api/v1/aria/chat`,
      examplesEndpoint: `GET /api/v1/aria/examples`,
      timestamp: new Date().toISOString(),
    });

    console.log(`
╔════════════════════════════════════════════════════════════╗
║         ASTRO Ultimate System v1.0.0 - Live               ║
╠════════════════════════════════════════════════════════════╣
║ Layer A: ASTRO Orchestration         [✓ ACTIVE]            ║
║ Layer B: OTIS Security               [✓ ACTIVE]            ║
║ Layer C: C0Di3 Intelligence          [✓ ACTIVE]            ║
║ Layer D: ARIA Conversation           [✓ ACTIVE]            ║
╠════════════════════════════════════════════════════════════╣
║ 🔌 Plugins:        ${String(plugins.length).padEnd(3)} loaded                             ║
║ 🤖 LLM Providers:  ${llmManager.list().join(', ').padEnd(30)}   ║
║ 🔄 Workflows:      ${String(workflowEngine.list().length).padEnd(3)} saved                              ║
╠════════════════════════════════════════════════════════════╣
║ 🎯 Chat:           POST /api/v1/aria/chat                 ║
║ 📊 Dashboard:      GET /dashboard                         ║
║ 🔄 Workflows:      /api/v1/workflows                      ║
║ 📈 Metrics:        /api/v1/metrics                        ║
║ 🌐 Server:         http://localhost:${PORT}                  ║
╚════════════════════════════════════════════════════════════╝
  `);
  });

  // 404 handler - must be after all routers are mounted
  app.use((req, res) => {
    res.status(404).json({
      error: 'Not Found',
      path: req.path,
      availableEndpoints: [
        'POST /api/v1/aria/chat - Main conversational interface',
        'GET /api/v1/aria/sessions/:sessionId - Get conversation history',
        'POST /api/v1/aria/sessions - Create new session',
        'DELETE /api/v1/aria/sessions/:sessionId - End session',
        'GET /api/v1/aria/examples - Get example commands',
        'POST /api/v1/astro/execute - Execute tool (raw API)',
        'GET /api/v1/astro/agents - List agents',
        'GET /api/v1/astro/tools - List tools',
        'GET /api/v1/workflows - List workflows',
        'POST /api/v1/workflows - Create workflow',
        'POST /api/v1/workflows/:id/execute - Execute workflow',
        'GET /api/v1/metrics - Get metrics',
        'GET /dashboard - Metrics dashboard',
        'POST /api/v1/llm/chat - LLM chat',
        'GET /api/v1/llm/providers - List LLM providers',
        'POST /api/v1/auth/dev-token - Issue dev JWT (non-production)',
        'GET /api/v1/health - Health check',
        'GET /api/v1/version - Version info',
      ],
    });
  });

  // Error handler
  app.use(
    (
      err: Error,
      _req: express.Request,
      res: express.Response,
      _next: express.NextFunction
    ) => {
      logger.error('Unhandled error', { error: err.message, stack: err.stack });
      res.status(500).json({
        error: 'Internal Server Error',
        message: NODE_ENV === 'development' ? err.message : undefined,
      });
    }
  );
}

bootstrap().catch((error) => {
  logger.error('Failed to start server', { error: error instanceof Error ? error.message : error });
  process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server?.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server?.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

export { app, server, wsServer, orchestrator, conversationEngine, securityGateway, threatIntelligence, pluginLoader, workflowEngine, llmManager };
