import { AgentConfig } from './orchestrator';

/**
 * Predefined agent configurations.
 * Each agent has a specific set of tools it is authorized to use.
 */

export const AGENTS: Record<string, AgentConfig> = {
  'general-assistant': {
    id: 'general-assistant',
    name: 'General Assistant',
    description:
      'A general-purpose agent that can echo, make HTTP requests, and perform math',
    tools: ['echo', 'http_request', 'math_eval'],
    routingHint: 'Use for varied, exploratory tasks',
  },

  'analyst-agent': {
    id: 'analyst-agent',
    name: 'Analyst Agent',
    description: 'An agent focused on data retrieval and analysis',
    tools: ['http_request', 'math_eval'],
    routingHint: 'Use for data analysis and fetch tasks',
  },

  'echo-agent': {
    id: 'echo-agent',
    name: 'Echo Agent',
    description: 'An agent that only echoes input (testing/debugging)',
    tools: ['echo'],
    routingHint: 'Use for testing orchestration',
  },

  'math-agent': {
    id: 'math-agent',
    name: 'Math Agent',
    description: 'An agent specialized in mathematical calculations',
    tools: ['math_eval'],
    routingHint: 'Use for calculations',
  },
};
