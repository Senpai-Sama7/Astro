import { Server as SocketIOServer, Socket } from 'socket.io';
import { Server as HTTPServer } from 'http';
import jwt from 'jsonwebtoken';
import { ARIAConversationEngine } from '../aria/conversation-engine';
import { logger } from '../services/logger';
import { RoleType } from '../otis/security-gateway';

interface AuthenticatedSocket extends Socket {
  userId?: string;
  role?: RoleType;
  sessionId?: string;
}

// Rate limiter for WebSocket messages
const messageRateLimiter = new Map<string, number[]>();
const RATE_LIMIT_WINDOW_MS = 60000; // 1 minute
const RATE_LIMIT_MAX_MESSAGES = 60; // 60 messages per minute
const MAX_MESSAGE_LENGTH = 4000;

function checkRateLimit(userId: string): boolean {
  const now = Date.now();
  const timestamps = messageRateLimiter.get(userId) || [];
  const recent = timestamps.filter((t) => now - t < RATE_LIMIT_WINDOW_MS);

  if (recent.length >= RATE_LIMIT_MAX_MESSAGES) {
    return false;
  }

  recent.push(now);
  messageRateLimiter.set(userId, recent);
  return true;
}

export class WebSocketServer {
  private io: SocketIOServer;
  private conversationEngine: ARIAConversationEngine;

  constructor(httpServer: HTTPServer, conversationEngine: ARIAConversationEngine) {
    this.conversationEngine = conversationEngine;
    const allowedOrigins = (process.env.SECURITY_CORS_ORIGIN || '')
      .split(',')
      .map((origin) => origin.trim())
      .filter(Boolean);

    this.io = new SocketIOServer(httpServer, {
      cors: {
        origin: (origin, callback) => {
          if (!origin || allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
            return callback(null, true);
          }
          return callback(new Error('CORS origin not allowed'));
        },
        methods: ['GET', 'POST'],
      },
      path: '/ws',
    });

    this.setupMiddleware();
    this.setupHandlers();
  }

  private setupMiddleware() {
    // Auth middleware
    this.io.use((socket: AuthenticatedSocket, next) => {
      const token = socket.handshake.auth.token || socket.handshake.query.token;
      if (!token) {
        return next(new Error('Authentication required'));
      }

      try {
        const secret = process.env.JWT_SECRET;
        if (!secret) {
          if (process.env.NODE_ENV === 'production') {
            logger.error('JWT_SECRET not set in production');
            return next(new Error('Server configuration error'));
          }
          logger.warn('JWT_SECRET not set; using insecure default (dev only)');
        }
        const jwtSecret = secret || 'astro-dev-secret';
        const payload = jwt.verify(token as string, jwtSecret) as {
          userId?: string;
          sub?: string;
          role?: RoleType;
        };
        socket.userId = payload.userId || payload.sub;
        socket.role = payload.role;
        if (!socket.userId || !socket.role) {
          return next(new Error('Invalid token'));
        }
        next();
      } catch {
        next(new Error('Invalid token'));
      }
    });
  }

  private validateMessageInput(data: unknown): data is { message: string } {
    if (!data || typeof data !== 'object') return false;
    const candidate = data as { message?: unknown };
    return (
      typeof candidate.message === 'string' &&
      candidate.message.trim().length > 0 &&
      candidate.message.length <= MAX_MESSAGE_LENGTH
    );
  }

  private setupHandlers() {
    this.io.on('connection', (socket: AuthenticatedSocket) => {
      logger.info('WebSocket connected', { userId: socket.userId, socketId: socket.id });

      // Start session
      const context = this.conversationEngine.startConversation(socket.userId!, socket.role!);
      socket.sessionId = context.sessionId;
      socket.emit('session', { sessionId: context.sessionId });

      // Chat message
      socket.on('chat', async (data: unknown) => {
        if (!socket.sessionId || !socket.userId) return;

        if (!this.validateMessageInput(data)) {
          socket.emit('error', { message: 'Invalid message payload' });
          return;
        }

        if (!checkRateLimit(socket.userId)) {
          socket.emit('error', { message: 'Rate limit exceeded. Please wait.' });
          return;
        }

        try {
          socket.emit('typing', { status: 'thinking' });

          const result = await this.conversationEngine.chat(socket.sessionId, data.message.trim());

          socket.emit('response', {
            response: result.response,
            toolExecuted: result.toolExecuted,
            requiresApproval: result.requiresApproval,
            approvalId: result.approvalId,
          });
        } catch (error) {
          socket.emit('error', {
            message: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      });

      // Stream chat (for streaming responses)
      socket.on('chat:stream', async (data: unknown) => {
        if (!socket.sessionId || !socket.userId) return;

        if (!this.validateMessageInput(data)) {
          socket.emit('stream:error', { message: 'Invalid message payload' });
          return;
        }

        if (!checkRateLimit(socket.userId)) {
          socket.emit('stream:error', { message: 'Rate limit exceeded. Please wait.' });
          return;
        }

        try {
          socket.emit('stream:start', {});

          // Simulate streaming by chunking response
          const result = await this.conversationEngine.chat(socket.sessionId, data.message.trim());
          const chunks = this.chunkResponse(result.response);

          for (const chunk of chunks) {
            socket.emit('stream:chunk', { content: chunk });
            await this.delay(50); // Simulate streaming delay
          }

          socket.emit('stream:end', {
            toolExecuted: result.toolExecuted,
            requiresApproval: result.requiresApproval,
          });
        } catch (error) {
          socket.emit('stream:error', {
            message: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      });

      // Approval
      socket.on('approve', async (data: { approvalId: string }) => {
        if (!socket.sessionId || !data?.approvalId) return;
        try {
          const result = await this.conversationEngine.chat(socket.sessionId, 'yes');
          socket.emit('response', result);
        } catch (error) {
          socket.emit('error', {
            message: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      });

      socket.on('deny', async () => {
        if (!socket.sessionId) return;
        try {
          const result = await this.conversationEngine.chat(socket.sessionId, 'no');
          socket.emit('response', result);
        } catch (error) {
          socket.emit('error', {
            message: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      });

      // Disconnect
      socket.on('disconnect', () => {
        logger.info('WebSocket disconnected', { userId: socket.userId, socketId: socket.id });
      });
    });
  }

  private chunkResponse(text: string, chunkSize = 20): string[] {
    const words = text.split(' ');
    const chunks: string[] = [];
    for (let i = 0; i < words.length; i += chunkSize) {
      chunks.push(words.slice(i, i + chunkSize).join(' '));
    }
    return chunks;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  close() {
    void this.io.close();
  }

  // Broadcast to all connected clients
  broadcast(event: string, data: unknown) {
    this.io.emit(event, data);
  }

  // Send to specific user
  sendToUser(userId: string, event: string, data: unknown) {
    const sockets = Array.from(this.io.sockets.sockets.values()) as AuthenticatedSocket[];
    for (const socket of sockets) {
      if (socket.userId === userId) {
        socket.emit(event, data);
      }
    }
  }
}
