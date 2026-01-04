import { Router, Request, Response } from 'express';
import { ARIAConversationEngine } from './conversation-engine';
import { RoleType } from '../otis/security-gateway';

export interface ConversationRequest {
  sessionId?: string;
  userId: string;
  userRole: RoleType;
  message: string;
}

export interface ConversationResponse {
  sessionId: string;
  message: string;
  response: string;
  toolExecuted?: boolean;
  result?: unknown;
  requiresApproval?: boolean;
  approvalId?: string;
  conversationHistory?: Array<{ role: string; content: string }>;
}

export function createConversationRouter(
  conversationEngine: ARIAConversationEngine
): Router {
  const router = Router();

  /**
   * POST /api/v1/aria/chat
   * Main conversation endpoint - turn-by-turn natural language interface.
   */
  router.post('/chat', async (req: Request, res: Response) => {
    try {
      const { sessionId: incomingSessionId, userId, userRole, message } = req.body as ConversationRequest;

      if (!userId || !userRole || !message) {
        return res.status(400).json({
          error: 'Missing required fields: userId, userRole, message',
        });
      }

      let sessionId = incomingSessionId;

      // Create new session if not provided
      if (!sessionId) {
        const context = conversationEngine.startConversation(userId, userRole);
        sessionId = context.sessionId;
      }

      // Process message through conversation engine
      const chatResult = await conversationEngine.chat(sessionId, message);

      // Get conversation history
      const history = conversationEngine.getConversationHistory(sessionId);

      const response: ConversationResponse = {
        sessionId,
        message,
        response: chatResult.response,
        toolExecuted: chatResult.toolExecuted,
        result: chatResult.result,
        requiresApproval: chatResult.requiresApproval,
        approvalId: chatResult.approvalId,
        conversationHistory: history.slice(-10).map((turn) => ({
          role: turn.role,
          content: turn.content,
        })),
      };

      res.json(response);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      res.status(500).json({ error: errorMsg });
    }
  });

  /**
   * GET /api/v1/aria/sessions/:sessionId
   * Get conversation history for a session.
   */
  router.get('/sessions/:sessionId', (req: Request, res: Response) => {
    try {
      const { sessionId } = req.params;

      const history = conversationEngine.getConversationHistory(sessionId);

      if (history.length === 0) {
        return res.status(404).json({
          error: `Session '${sessionId}' not found or has no history`,
        });
      }

      res.json({
        sessionId,
        turnCount: history.length,
        history: history.map((turn) => ({
          timestamp: turn.timestamp,
          role: turn.role,
          content: turn.content,
          intent: turn.intent,
          toolName: turn.toolName,
          riskScore: turn.riskScore,
        })),
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      res.status(500).json({ error: errorMsg });
    }
  });

  /**
   * POST /api/v1/aria/sessions
   * Create a new conversation session.
   */
  router.post('/sessions', (req: Request, res: Response) => {
    try {
      const { userId, userRole } = req.body;

      if (!userId || !userRole) {
        return res.status(400).json({
          error: 'Missing required fields: userId, userRole',
        });
      }

      const context = conversationEngine.startConversation(userId, userRole);

      res.json({
        sessionId: context.sessionId,
        userId: context.userId,
        userRole: context.userRole,
        startedAt: new Date(),
        message: `Session started. Type "help" for available commands.`,
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      res.status(500).json({ error: errorMsg });
    }
  });

  /**
   * DELETE /api/v1/aria/sessions/:sessionId
   * End a conversation session.
   */
  router.delete('/sessions/:sessionId', (req: Request, res: Response) => {
    try {
      const { sessionId } = req.params;

      conversationEngine.endConversation(sessionId);

      res.json({
        message: `Session '${sessionId}' ended.`,
      });
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      res.status(500).json({ error: errorMsg });
    }
  });

  /**
   * GET /api/v1/aria/examples
   * Get example commands and queries.
   */
  router.get('/examples', (_req: Request, res: Response) => {
    res.json({
      examples: [
        {
          category: 'Execute Tools',
          commands: [
            'echo hello world',
            'calculate 5 + 3 * 2',
            'fetch https://httpbin.org/get',
          ],
        },
        {
          category: 'Query Information',
          commands: [
            'show agents',
            'show tools',
            'show threats',
            'show incidents',
          ],
        },
        {
          category: 'System',
          commands: [
            'help',
            'status',
          ],
        },
        {
          category: 'Approval',
          commands: [
            'yes',
            'no',
            'approve',
            'deny',
          ],
        },
      ],
    });
  });

  return router;
}
