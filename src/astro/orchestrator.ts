import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import Joi from 'joi';

// Input validation schemas for tools
const toolInputSchemas: Record<string, Joi.Schema> = {
  read_file: Joi.object({ path: Joi.string().max(256).required() }),
  write_file: Joi.object({ path: Joi.string().max(256).required(), content: Joi.string().max(1024 * 1024).required() }),
  list_dir: Joi.object({ path: Joi.string().max(256).default('.') }),
  math_eval: Joi.object({ expression: Joi.string().max(200).required() }),
  web_search: Joi.object({ query: Joi.string().max(500).required(), maxResults: Joi.number().min(1).max(20).default(5) }),
  http_request: Joi.object({ url: Joi.string().uri().max(2048).required(), method: Joi.string().valid('GET', 'POST', 'PUT', 'DELETE').default('GET'), headers: Joi.object().default({}), data: Joi.any() }),
  git_status: Joi.object({ cwd: Joi.string().max(256) }),
  git_diff: Joi.object({ cwd: Joi.string().max(256), file: Joi.string().max(256) }),
  run_tests: Joi.object({ cwd: Joi.string().max(256), command: Joi.string().max(50) }),
  lint_code: Joi.object({ path: Joi.string().max(256).default('.'), linter: Joi.string().valid('eslint', 'pylint') }),
};

export type ToolContext = {
  requestId: string;
  userId?: string;
  profile: 'core' | 'cyber';
  metadata?: Record<string, unknown>;
};

export type ToolInput = Record<string, unknown>;

export type ToolResult = {
  ok: boolean;
  data?: unknown;
  error?: string;
  elapsedMs: number;
};

export interface ToolDefinition {
  name: string;
  description: string;
  schema?: Record<string, unknown>;
  handler: (input: ToolInput, context: ToolContext) => Promise<ToolResult>;
}

export type AgentConfig = {
  id: string;
  name: string;
  description: string;
  tools: string[];
  routingHint?: string;
};

export type OrchestrationResult = {
  requestId: string;
  agentId: string;
  toolName: string;
  result: ToolResult;
};

export type OrchestrationError = {
  requestId: string;
  error: string;
};

export interface OrchestratorEvents {
  result: (payload: OrchestrationResult) => void;
  error: (payload: OrchestrationError) => void;
}

export class AstroOrchestrator {
  private tools: Map<string, ToolDefinition> = new Map();
  private agents: Map<string, AgentConfig> = new Map();
  private emitter: EventEmitter;

  constructor() {
    this.emitter = new EventEmitter();
  }

  /**
   * Register a tool that agents can call.
   */
  registerTool(def: ToolDefinition): void {
    if (!def?.name || typeof def.handler !== 'function') {
      throw new Error('Invalid tool definition: name and handler are required');
    }

    if (this.tools.has(def.name)) {
      throw new Error(`Tool '${def.name}' is already registered`);
    }

    this.tools.set(def.name, def);
  }

  /**
   * Register an agent with a set of tools it is allowed to use.
   */
  registerAgent(config: AgentConfig): void {
    if (!config?.id || !config?.name) {
      throw new Error('Invalid agent config: id and name are required');
    }

    if (!Array.isArray(config.tools) || config.tools.length === 0) {
      throw new Error('Agent must have at least one tool');
    }

    this.agents.set(config.id, config);
  }

  /**
   * Subscribe to orchestration events (results, errors).
   */
  on<K extends keyof OrchestratorEvents>(
    event: K,
    listener: OrchestratorEvents[K]
  ): void {
    this.emitter.on(event, listener as unknown as (...args: unknown[]) => void);
  }

  /**
   * Orchestrate a single tool call for a given agent.
   * This is intentionally simple: one agent → one tool → one result.
   */
  async orchestrateToolCall(params: {
    agentId: string;
    toolName: string;
    input: ToolInput;
    userId?: string;
    profile?: 'core' | 'cyber';
    metadata?: Record<string, unknown>;
  }): Promise<OrchestrationResult> {
    const requestId = uuidv4();
    const profile = params.profile ?? 'core';

    const agent = this.agents.get(params.agentId);
    if (!agent) {
      const error: OrchestrationError = {
        requestId,
        error: `Agent '${params.agentId}' is not registered`,
      };
      this.emitter.emit('error', error);
      throw new Error(error.error);
    }

    if (!agent.tools.includes(params.toolName)) {
      const error: OrchestrationError = {
        requestId,
        error: `Agent '${agent.id}' is not allowed to use tool '${params.toolName}'`,
      };
      this.emitter.emit('error', error);
      throw new Error(error.error);
    }

    const tool = this.tools.get(params.toolName);
    if (!tool) {
      const error: OrchestrationError = {
        requestId,
        error: `Tool '${params.toolName}' is not registered`,
      };
      this.emitter.emit('error', error);
      throw new Error(error.error);
    }

    const started = Date.now();

    // Validate input against schema if defined
    const schema = toolInputSchemas[params.toolName];
    if (schema) {
      const { error, value } = schema.validate(params.input, { stripUnknown: true });
      if (error) {
        const validationError: OrchestrationError = {
          requestId,
          error: `Invalid input for '${params.toolName}': ${error.message}`,
        };
        this.emitter.emit('error', validationError);
        throw new Error(validationError.error);
      }
      params.input = value;
    }

    try {
      const context: ToolContext = {
        requestId,
        userId: params.userId,
        profile,
        metadata: params.metadata,
      };

      const result = await tool.handler(params.input, context);
      const elapsedMs = Date.now() - started;

      const payload: OrchestrationResult = {
        requestId,
        agentId: agent.id,
        toolName: tool.name,
        result: {
          ...result,
          elapsedMs,
        },
      };

      this.emitter.emit('result', payload);
      return payload;
    } catch (err) {
      const elapsedMs = Date.now() - started;
      const errorMessage =
        err instanceof Error ? err.message : 'Unknown orchestration error';

      const error: OrchestrationError = {
        requestId,
        error: `${errorMessage} (elapsed ${elapsedMs}ms)`,
      };
      this.emitter.emit('error', error);
      throw new Error(error.error);
    }
  }

  /**
   * Introspection helpers (useful for tooling and future UI).
   */
  listAgents(): AgentConfig[] {
    return Array.from(this.agents.values());
  }

  listTools(): ToolDefinition[] {
    return Array.from(this.tools.values());
  }
}
