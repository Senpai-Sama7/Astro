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

export class WebSocketServer {
  private io: SocketIOServer;
  private conversationEngine: ARIAConversationEngine;

  constructor(httpServer: HTTPServer, conversationEngine: ARIAConversationEngine) {
    this.conversationEngine = conversationEngine;
    this.io = new SocketIOServer(httpServer, {
      cors: { origin: process.env.SECURITY_CORS_ORIGIN || '*', methods: ['GET', 'POST'] },
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
        const secret = process.env.JWT_SECRET || 'astro-dev-secret';
        const payload = jwt.verify(token as string, secret) as { userId?: string; sub?: string; role?: RoleType };
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

  private setupHandlers() {
    this.io.on('connection', (socket: AuthenticatedSocket) => {
      logger.info('WebSocket connected', { userId: socket.userId, socketId: socket.id });

      // Start session
      const context = this.conversationEngine.startConversation(socket.userId!, socket.role!);
      socket.sessionId = context.sessionId;
      socket.emit('session', { sessionId: context.sessionId });

      // Chat message
      socket.on('chat', async (data: { message: string }) => {
        if (!socket.sessionId) return;

        try {
          socket.emit('typing', { status: 'thinking' });

          const result = await this.conversationEngine.chat(socket.sessionId, data.message);

          socket.emit('response', {
            response: result.response,
            toolExecuted: result.toolExecuted,
            requiresApproval: result.requiresApproval,
            approvalId: result.approvalId,
          });
        } catch (error) {
          socket.emit('error', { message: error instanceof Error ? error.message : 'Unknown error' });
        }
      });

      // Stream chat (for streaming responses)
      socket.on('chat:stream', async (data: { message: string }) => {
        if (!socket.sessionId) return;

        try {
          socket.emit('stream:start', {});

          // Simulate streaming by chunking response
          const result = await this.conversationEngine.chat(socket.sessionId, data.message);
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
          socket.emit('stream:error', { message: error instanceof Error ? error.message : 'Unknown error' });
        }
      });

      // Approval
      socket.on('approve', async (data: { approvalId: string }) => {
        if (!socket.sessionId) return;
        const result = await this.conversationEngine.chat(socket.sessionId, 'yes');
        socket.emit('response', result);
      });

      socket.on('deny', async () => {
        if (!socket.sessionId) return;
        const result = await this.conversationEngine.chat(socket.sessionId, 'no');
        socket.emit('response', result);
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
    return new Promise(resolve => setTimeout(resolve, ms));
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
