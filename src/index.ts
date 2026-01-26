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
import { ARIAConversationEngine } from './aria/conversation-engine';
import { createConversationRouter } from './aria/router';
import { OTISSecurityGateway } from './otis/security-gateway';
import { C0Di3CyberIntelligence } from './codi3/threat-intelligence';
import { SQLiteStorage } from './services/storage';
import { createAuthRouter } from './auth/router';

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

// Middleware
app.use(helmet());
app.use(cors({ origin: process.env.SECURITY_CORS_ORIGIN }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/v1/aria', apiLimiter);
app.use('/api/v1/astro', apiLimiter);

// Logging middleware
app.use((req, res, next) => {
  const start = Date.now();
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
      'Role-Based Access Control (6 roles)',
      'CVaR Risk Scoring',
      'Immutable Audit Logging with HMAC',
      'Threat Management & Incident Tracking',
      'MITRE ATT&CK Knowledge Base',
      'Multi-turn Natural Language Interface',
    ],
    testsPassing: '100+',
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

  // Mount ASTRO Layer A router
  const astroRouter = createAstroRouter(orchestrator);
  app.use('/api/v1/astro', astroRouter);

  // Mount ARIA Layer D router (conversational interface)
  const ariaRouter = createConversationRouter(conversationEngine);
  app.use('/api/v1/aria', ariaRouter);

  // Start server
  server = createServer(app);

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
║ 🎯 Main Endpoint:  POST /api/v1/aria/chat                 ║
║ 📖 Examples:       GET /api/v1/aria/examples              ║
║ 🌐 Server:         http://localhost:${PORT}                  ║
╠════════════════════════════════════════════════════════════╣
║ 💬 Try this: "calculate 2 + 2"                            ║
║             "show agents"                                  ║
║             "help"                                         ║
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

export { app, server, orchestrator, conversationEngine, securityGateway, threatIntelligence };
