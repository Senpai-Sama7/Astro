import { AgentConfig } from './orchestrator';

/**
 * Predefined agent configurations.
 * Each agent has a specific set of tools it is authorized to use.
 */

export const AGENTS: Record<string, AgentConfig> = {
  // ============================================
  // SPECIALIZED AGENTS (matching frontend)
  // ============================================

  'research-agent': {
    id: 'research-agent',
    name: 'Research Agent',
    description: 'Web search, content extraction, and summarization. Finds and synthesizes information from across the internet.',
    tools: ['web_search', 'content_extract', 'http_request'],
    routingHint: 'Use for research, web search, and information gathering',
  },

  'code-agent': {
    id: 'code-agent',
    name: 'Code Agent',
    description: 'Generates, executes, and debugs code. Full AST validation for safety.',
    tools: ['echo', 'math_eval'],
    routingHint: 'Use for code generation and execution tasks',
  },

  'filesystem-agent': {
    id: 'filesystem-agent',
    name: 'FileSystem Agent',
    description: 'Creates, reads, and organizes files. Path-validated operations restricted to the workspace directory.',
    tools: ['read_file', 'write_file', 'list_dir'],
    routingHint: 'Use for file operations and data processing',
  },

  'git-agent': {
    id: 'git-agent',
    name: 'Git Agent',
    description: 'Version control operations: status, diff, commit, branch, checkout. Manages your repository seamlessly.',
    tools: ['git_status', 'git_diff'],
    routingHint: 'Use for version control and repository management',
  },

  'test-agent': {
    id: 'test-agent',
    name: 'Test Agent',
    description: 'Runs test suites across frameworks: pytest, npm test, cargo test, go test. Enables TDD workflows.',
    tools: ['run_tests'],
    routingHint: 'Use for running tests and TDD workflows',
  },

  'analysis-agent': {
    id: 'analysis-agent',
    name: 'Analysis Agent',
    description: 'Static code analysis and linting. Runs pylint, eslint, and other quality tools on your codebase.',
    tools: ['lint_code'],
    routingHint: 'Use for code quality analysis and linting',
  },

  'knowledge-agent': {
    id: 'knowledge-agent',
    name: 'Knowledge Agent',
    description: 'Semantic memory persistence. Saves and retrieves architectural decisions, context, and learnings.',
    tools: ['save_knowledge', 'retrieve_knowledge'],
    routingHint: 'Use for storing and retrieving knowledge and context',
  },

  // ============================================
  // UTILITY AGENTS
  // ============================================

  'general-assistant': {
    id: 'general-assistant',
    name: 'General Assistant',
    description: 'A general-purpose agent that can echo, make HTTP requests, and perform math',
    tools: ['echo', 'http_request', 'math_eval'],
    routingHint: 'Use for varied, exploratory tasks',
  },

  'math-agent': {
    id: 'math-agent',
    name: 'Math Agent',
    description: 'An agent specialized in mathematical calculations',
    tools: ['math_eval'],
    routingHint: 'Use for calculations',
  },

  'echo-agent': {
    id: 'echo-agent',
    name: 'Echo Agent',
    description: 'An agent that only echoes input (testing/debugging)',
    tools: ['echo'],
    routingHint: 'Use for testing orchestration',
  },
};
