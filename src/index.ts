import 'express-async-errors';
import dotenv from 'dotenv';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { createServer } from 'http';
import { logger } from './services/logger';
import { AstroOrchestrator } from './astro/orchestrator';
import { createAstroRouter } from './astro/router';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const NODE_ENV = process.env.NODE_ENV || 'development';
const PROFILE = process.env.PROFILE || 'core';

// Create ASTRO orchestrator (Layer A)
const orchestrator = new AstroOrchestrator();

// Middleware
app.use(helmet());
app.use(cors({ origin: process.env.SECURITY_CORS_ORIGIN }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

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
    version: '1.0.0-alpha.1',
    name: 'Ultimate System',
    profile: PROFILE,
    layers: {
      a: 'ASTRO (Orchestration) - IMPLEMENTED',
      b: 'OTIS (Security) - IN PROGRESS',
      c: 'C0Di3 (Cyber Intelligence) - PLANNED',
    },
  });
});

// Mount ASTRO Layer A router
const astroRouter = createAstroRouter(orchestrator);
app.use('/api/v1/astro', astroRouter);

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found' });
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

// Start server
const server = createServer(app);

server.listen(PORT, () => {
  logger.info('Ultimate System Started', {
    port: PORT,
    environment: NODE_ENV,
    profile: PROFILE,
    layers: ['ASTRO (Layer A)', 'OTIS (Layer B - pending)', 'C0Di3 (Layer C - pending)'],
    timestamp: new Date().toISOString(),
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

export { app, server, orchestrator };
