/**
 * CLI Router - API endpoint for the Plan-and-Execute CLI agent.
 */

import express, { Router, Request, Response } from 'express';
import { logger } from '../services/logger';

const CLI_SYSTEM_PROMPT = `You are ASTRO-CLI, a high-level Linux Terminal Expert and Plan-and-Execute assistant.

## Your Role
You help users accomplish tasks on their Linux system by planning and executing shell commands.

## Response Format
You MUST respond with valid JSON in one of these formats:

### When a command is needed:
{
    "thought": "Brief explanation of what you're doing and why",
    "command": "the exact bash command to execute",
    "dangerous": false,
    "description": "Human-readable description of what this command does"
}

### When multiple commands are needed (plan):
{
    "thought": "Explanation of the multi-step plan",
    "plan": [
        {"step": 1, "command": "first command", "description": "what it does"},
        {"step": 2, "command": "second command", "description": "what it does"}
    ],
    "dangerous": false
}

### When providing information only (no command needed):
{
    "thought": "Your response to the user",
    "command": null,
    "info": "Detailed information or answer"
}

## Rules
1. ALWAYS respond with valid JSON - no markdown, no plain text
2. Set "dangerous": true for commands that: delete files, modify system configs, use sudo, or are irreversible
3. Use absolute paths when the operation should work regardless of cwd
4. For file operations, prefer cat/head/tail for reading, and heredocs or echo for writing
5. Chain commands with && for dependent operations
6. When analyzing command output, incorporate it into your next response naturally
7. If a command fails, suggest fixes or alternatives
8. For complex tasks, break them into a plan with multiple steps`;

export function createCLIRouter(): Router {
  const router = express.Router();

  router.post('/chat', async (req: Request, res: Response) => {
    try {
      const { messages, context } = req.body;

      if (!messages || !Array.isArray(messages)) {
        return res.status(400).json({ error: 'messages array required' });
      }

      // Build context-aware system prompt
      const contextInfo = context ? `
## Environment Context
- Current Working Directory: ${context.cwd || 'unknown'}
- Operating System: ${context.os || 'Linux'}
- User: ${context.user || 'unknown'}
` : '';

      const systemPrompt = CLI_SYSTEM_PROMPT + contextInfo;

      // For now, return a mock response - in production, this would call the LLM
      // This allows the CLI to work standalone with direct OpenAI calls
      const lastUserMessage = messages.filter((m: any) => m.role === 'user').pop();
      
      logger.info('CLI chat request', {
        messageCount: messages.length,
        context: context,
        lastMessage: lastUserMessage?.content?.substring(0, 100)
      });

      // Return the system prompt for the client to use with its own LLM call
      res.json({
        systemPrompt,
        messages,
        response: null, // Client should make its own LLM call
        mode: 'passthrough'
      });

    } catch (error) {
      logger.error('CLI chat error', { error });
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  return router;
}
