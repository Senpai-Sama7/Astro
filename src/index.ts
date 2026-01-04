import 'express-async-errors';
import dotenv from 'dotenv';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import { createServer } from 'http';
import { logger } from './services/logger';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const NODE_ENV = process.env.NODE_ENV || 'development';
const PROFILE = process.env.PROFILE || 'core';

// Middleware
app.use(helmet());
app.use(cors({ origin: process.env.SECURITY_CORS_ORIGIN || '*' }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

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
    version: '1.0.0-alpha.0',
    name: 'Ultimate System',
    profile: PROFILE,
  });
});

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

export { app, server };
