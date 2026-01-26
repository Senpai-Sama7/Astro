import { EventEmitter } from 'events';
import { AstroOrchestrator } from '../astro/orchestrator';
import { OTISSecurityGateway, RoleType } from '../otis/security-gateway';
import { C0Di3CyberIntelligence } from '../codi3/threat-intelligence';
import { SQLiteStorage } from '../services/storage';
import { metricsCollector } from '../services/metrics';

export interface ConversationContext {
  userId: string;
  sessionId: string;
  userRole: RoleType;
  conversationHistory: ConversationTurn[];
  agentAssignments: Map<string, string>;
  activeAgent?: string;
  metadata: Record<string, unknown>;
}

export interface ConversationTurn {
  timestamp: Date;
  role: 'user' | 'system';
  content: string;
  intent?: string;
  toolName?: string;
  agentId?: string;
  parameters?: Record<string, unknown>;
  sessionId?: string;
  result?: unknown;
  error?: string;
  riskScore?: number;
  requiresApproval?: boolean;
}

export interface ParsedUserIntent {
  intent: string;
  confidence: number;
  toolName?: string;
  agentId?: string;
  parameters?: Record<string, unknown>;
  naturalText: string;
}

// External dependencies injected at runtime
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let workflowEngine: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let llmManager: any = null;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function setWorkflowEngine(engine: any) { workflowEngine = engine; }
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function setLLMManager(manager: any) { llmManager = manager; }

/**
 * ARIA: Advanced Reasoning Interface for Agents
 * Conversational natural language layer - the ONLY interface users need.
 */
export class ARIAConversationEngine extends EventEmitter {
  private orchestrator: AstroOrchestrator;
  private securityGateway: OTISSecurityGateway;
  private threatIntelligence: C0Di3CyberIntelligence;
  private contexts: Map<string, ConversationContext> = new Map();
  private pendingApprovals: Map<string, ConversationTurn> = new Map();
  private storage?: SQLiteStorage;

  constructor(
    orchestrator: AstroOrchestrator,
    security: OTISSecurityGateway,
    intelligence: C0Di3CyberIntelligence,
    storage?: SQLiteStorage
  ) {
    super();
    this.orchestrator = orchestrator;
    this.securityGateway = security;
    this.threatIntelligence = intelligence;
    this.storage = storage;
  }

  startConversation(userId: string, userRole: RoleType): ConversationContext {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const context: ConversationContext = {
      userId, sessionId, userRole,
      conversationHistory: [],
      agentAssignments: new Map(),
      metadata: { profile: process.env.PROFILE || 'core' },
    };
    this.contexts.set(sessionId, context);
    void this.persistSession(context);
    return context;
  }

  async chat(sessionId: string, userMessage: string): Promise<{
    response: string;
    toolExecuted?: boolean;
    result?: unknown;
    requiresApproval?: boolean;
    approvalId?: string;
  }> {
    const context = await this.getContext(sessionId);
    if (!context) throw new Error(`Session '${sessionId}' not found`);

    const userTurn: ConversationTurn = { timestamp: new Date(), role: 'user', content: userMessage };
    context.conversationHistory.push(userTurn);

    try {
      const intent = this.parseIntent(userMessage);
      userTurn.intent = intent.intent;

      let response: string;
      let result: unknown;
      let toolExecuted = false;
      let requiresApproval = false;
      let approvalId: string | undefined;

      switch (intent.intent) {
        case 'execute':
          ({ response, result, toolExecuted, requiresApproval, approvalId } = 
            await this.handleExecute(context, intent, userMessage));
          break;
        case 'workflow':
          response = await this.handleWorkflow(context, intent, userMessage);
          break;
        case 'llm':
          response = await this.handleLLM(context, userMessage);
          break;
        case 'metrics':
          response = this.handleMetrics();
          break;
        case 'query':
          response = await this.handleQuery(context, intent);
          break;
        case 'help':
          response = this.handleHelp();
          break;
        case 'status':
          response = this.handleStatus(context);
          break;
        case 'config':
          response = `⚙️ Configuration management coming soon. Current settings:\n• Profile: ${context.metadata.profile}\n• Role: ${context.userRole}`;
          break;
        case 'approve':
          ({ response, result, toolExecuted } = await this.handleApproval(context, true));
          break;
        case 'deny':
          response = (await this.handleApproval(context, false)).response;
          break;
        default:
          // Try LLM for unknown intents if available
          if (llmManager) {
            response = await this.handleLLM(context, userMessage);
          } else {
            response = `I'm not sure what you mean. Try "help" to see what I can do.`;
          }
      }

      context.conversationHistory.push({ timestamp: new Date(), role: 'system', content: response, result });
      void this.persistSession(context);

      return { response, toolExecuted, result, requiresApproval, approvalId };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      context.conversationHistory.push({ timestamp: new Date(), role: 'system', content: `Error: ${errorMsg}`, error: errorMsg });
      return { response: `Sorry, something went wrong: ${errorMsg}` };
    }
  }

  private parseIntent(msg: string): ParsedUserIntent {
    const lower = msg.toLowerCase();
    const base = { naturalText: msg };

    // Workflow intents
    if (/\b(workflow|automat|pipeline)\b/i.test(lower)) {
      const action = /\b(run|execute|start)\b/i.test(lower) ? 'run' : 
                     /\b(create|make|new)\b/i.test(lower) ? 'create' : 'list';
      const nameMatch = msg.match(/(?:workflow|pipeline)\s+["']?(\w+)["']?/i);
      return { intent: 'workflow', confidence: 0.9, parameters: { action, name: nameMatch?.[1] }, ...base };
    }

    // LLM/AI intents
    if (/\b(ask|chat with|use)\s+(gpt|claude|llama|ai|llm|openai|anthropic)/i.test(lower) ||
        /\b(generate|write|explain|summarize|translate)\b/i.test(lower)) {
      return { intent: 'llm', confidence: 0.85, ...base };
    }

    // Metrics intents
    if (/\b(metric|stat|dashboard|performance|usage|how.*(doing|running))\b/i.test(lower)) {
      return { intent: 'metrics', confidence: 0.9, ...base };
    }

    // Help
    if (/\b(help|what can|how do i|commands?)\b/i.test(lower)) {
      return { intent: 'help', confidence: 0.95, ...base };
    }

    // Config
    if (/\b(config|configure|settings?)\b/i.test(lower)) {
      return { intent: 'config', confidence: 0.9, ...base };
    }

    // Status
    if (/\b(status|session|who am i)\b/i.test(lower)) {
      return { intent: 'status', confidence: 0.9, ...base };
    }

    // Query
    if (/\b(show|list|get|tell me about)\b/i.test(lower)) {
      const target = /agent/i.test(lower) ? 'agents' : /tool/i.test(lower) ? 'tools' :
                     /threat/i.test(lower) ? 'threats' : /incident/i.test(lower) ? 'incidents' :
                     /plugin/i.test(lower) ? 'plugins' : /provider/i.test(lower) ? 'providers' : '';
      return { intent: 'query', confidence: 0.85, parameters: { target }, ...base };
    }

    // Approval
    if (/^(yes|approve|ok|go ahead|do it)\b/i.test(lower)) return { intent: 'approve', confidence: 0.9, ...base };
    if (/^(no|deny|cancel|stop)\b/i.test(lower)) return { intent: 'deny', confidence: 0.9, ...base };

    // Tool execution - math
    if (/\b(calculate|compute|what('s| is))\b.*\d/i.test(lower)) {
      const expr = msg.match(/(?:calculate|compute|what(?:'s| is))\s+(.+)/i)?.[1] || 
                   msg.match(/([0-9+\-*/().\s]+)/)?.[1];
      return { intent: 'execute', confidence: 0.85, toolName: 'math_eval', parameters: { expression: expr?.trim() }, ...base };
    }

    // Tool execution - HTTP
    if (/https?:\/\//.test(msg)) {
      const url = msg.match(/https?:\/\/[^\s]+/)?.[0];
      return { intent: 'execute', confidence: 0.8, toolName: 'http_request', parameters: { url, method: 'GET' }, ...base };
    }

    // Tool execution - file operations
    if (/\b(read|open)\s+(file|the file)\b/i.test(lower)) {
      const path = msg.match(/(?:read|open)\s+(?:file\s+)?["']?([^\s"']+)["']?/i)?.[1];
      return { intent: 'execute', confidence: 0.8, toolName: 'read_file', parameters: { path }, ...base };
    }
    if (/\b(write|save|create)\s+(file|to file)\b/i.test(lower)) {
      return { intent: 'execute', confidence: 0.8, toolName: 'write_file', parameters: {}, ...base };
    }
    if (/\b(list|show)\s+(dir|directory|folder|files)\b/i.test(lower)) {
      return { intent: 'execute', confidence: 0.8, toolName: 'list_dir', parameters: {}, ...base };
    }

    // Tool execution - git
    if (/\bgit\s+status\b/i.test(lower)) {
      return { intent: 'execute', confidence: 0.9, toolName: 'git_status', parameters: {}, ...base };
    }
    if (/\bgit\s+diff\b/i.test(lower)) {
      return { intent: 'execute', confidence: 0.9, toolName: 'git_diff', parameters: {}, ...base };
    }

    // Tool execution - search
    if (/\b(search|find|look up)\b/i.test(lower)) {
      const query = msg.match(/(?:search|find|look up)\s+(?:for\s+)?["']?(.+?)["']?$/i)?.[1];
      return { intent: 'execute', confidence: 0.8, toolName: 'web_search', parameters: { query }, ...base };
    }

    // Default - try LLM or unknown
    return { intent: 'unknown', confidence: 0.3, ...base };
  }

  private async handleExecute(context: ConversationContext, intent: ParsedUserIntent, userMessage: string): Promise<{
    response: string; result?: unknown; toolExecuted: boolean; requiresApproval: boolean; approvalId?: string;
  }> {
    if (!intent.toolName) {
      return { response: `I couldn't figure out which tool to use. Can you be more specific?`, toolExecuted: false, requiresApproval: false };
    }

    const agentId = this.findAgent(intent.toolName);
    if (!agentId) {
      return { response: `No agent can run '${intent.toolName}'. Try "show tools" to see what's available.`, toolExecuted: false, requiresApproval: false };
    }

    if (!this.securityGateway.hasPermission(context.userRole, 'canExecuteTools')) {
      return { response: `Your role doesn't allow tool execution.`, toolExecuted: false, requiresApproval: false };
    }

    const riskScore = this.securityGateway.calculateRiskScore({
      role: context.userRole, action: 'execute_tool', resource: intent.toolName, toolName: intent.toolName,
    });

    if (this.securityGateway.requiresApproval(riskScore)) {
      const approvalId = `approval_${Date.now()}`;
      this.pendingApprovals.set(approvalId, {
        timestamp: new Date(), role: 'user', content: userMessage,
        toolName: intent.toolName, agentId, parameters: intent.parameters || {},
        sessionId: context.sessionId, riskScore, requiresApproval: true,
      });
      return {
        response: `⚠️ This action has ${(riskScore * 100).toFixed(0)}% risk and needs approval. Say "yes" to proceed or "no" to cancel.`,
        toolExecuted: false, requiresApproval: true, approvalId,
      };
    }

    try {
      const start = Date.now();
      const result = await this.orchestrator.orchestrateToolCall({
        agentId, toolName: intent.toolName, input: intent.parameters || {},
        userId: context.userId, profile: (context.metadata.profile as 'core' | 'cyber') || 'core',
      });
      metricsCollector.recordToolExecution(intent.toolName, Date.now() - start);
      return { response: this.formatResult(intent.toolName, result), result, toolExecuted: true, requiresApproval: false };
    } catch (e) {
      metricsCollector.recordToolExecution(intent.toolName, 0, true);
      return { response: `Failed: ${e instanceof Error ? e.message : e}`, toolExecuted: false, requiresApproval: false };
    }
  }

  private async handleWorkflow(context: ConversationContext, intent: ParsedUserIntent, msg: string): Promise<string> {
    if (!workflowEngine) return `Workflow system not available.`;

    const action = intent.parameters?.action as string;
    const name = intent.parameters?.name as string;

    if (action === 'list' || !action) {
      const workflows = workflowEngine.list() as { id: string; name: string; description: string }[];
      if (!workflows.length) return `No workflows yet. Say "create workflow [name]" to make one.`;
      return `📋 Your workflows:\n${workflows.map(w => `• ${w.name} (${w.id}): ${w.description || 'No description'}`).join('\n')}`;
    }

    if (action === 'run' && name) {
      const workflows = workflowEngine.list() as { id: string; name: string }[];
      const wf = workflows.find(w => w.name.toLowerCase() === name.toLowerCase() || w.id === name);
      if (!wf) return `Workflow "${name}" not found. Say "show workflows" to see available ones.`;
      try {
        const results = await workflowEngine.execute(wf.id, this.orchestrator, context.userId);
        return `✅ Workflow "${wf.name}" completed!\n\nResults:\n${JSON.stringify(results, null, 2)}`;
      } catch (e) {
        return `❌ Workflow failed: ${e instanceof Error ? e.message : e}`;
      }
    }

    if (action === 'create') {
      return `To create a workflow, I need more details. Tell me:\n1. What should it be called?\n2. What steps should it have?\n\nExample: "Create a workflow called 'daily-check' that runs git status then lists files"`;
    }

    return `I can help with workflows. Try:\n• "show workflows" - list your workflows\n• "run workflow [name]" - execute a workflow\n• "create workflow" - make a new one`;
  }

  private async handleLLM(context: ConversationContext, msg: string): Promise<string> {
    if (!llmManager) return `LLM not configured. Add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env`;

    // Extract the actual question/prompt
    const prompt = msg.replace(/^(ask|chat with|use)\s+(gpt|claude|llama|ai|llm|openai|anthropic)\s*/i, '').trim() || msg;
    
    // Detect provider preference
    let provider: string | undefined;
    if (/claude|anthropic/i.test(msg)) provider = 'anthropic';
    else if (/gpt|openai/i.test(msg)) provider = 'openai';
    else if (/llama|ollama/i.test(msg)) provider = 'ollama';

    try {
      const response = await llmManager.chat(
        [{ role: 'user', content: prompt }],
        { provider }
      );
      return `🤖 ${response.content}`;
    } catch (e) {
      return `LLM error: ${e instanceof Error ? e.message : e}`;
    }
  }

  private handleMetrics(): string {
    const m = metricsCollector.getMetrics();
    const uptime = Math.floor(m.system.uptime / 1000);
    const mem = (m.system.memory.used / 1024 / 1024).toFixed(1);
    const errorRate = m.tools.executions ? ((m.tools.errors / m.tools.executions) * 100).toFixed(1) : '0';

    return `📊 System Status:

• Uptime: ${uptime}s
• Memory: ${mem}MB
• Requests: ${m.requests.total}
• Tool executions: ${m.tools.executions}
• Error rate: ${errorRate}%
• Avg latency: ${m.latency.avg.toFixed(1)}ms

Top tools: ${Object.entries(m.tools.byTool).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([t, c]) => `${t}(${c})`).join(', ') || 'none yet'}`;
  }

  private async handleQuery(context: ConversationContext, intent: ParsedUserIntent): Promise<string> {
    const target = (intent.parameters?.target as string) || '';

    if (target === 'agents' || !target) {
      const agents = this.orchestrator.listAgents();
      return `🤖 Available agents:\n${agents.map(a => `• ${a.name}: ${a.description}\n  Tools: ${a.tools.join(', ')}`).join('\n\n')}`;
    }
    if (target === 'tools') {
      const tools = this.orchestrator.listTools();
      return `🔧 Available tools:\n${tools.map(t => `• ${t.name}: ${t.description}`).join('\n')}`;
    }
    if (target === 'threats') {
      const threats = this.threatIntelligence.getCriticalThreats();
      return threats.length ? `🚨 Critical threats:\n${threats.map(t => `• [${t.level}] ${t.title}`).join('\n')}` : `✅ No critical threats detected.`;
    }
    if (target === 'incidents') {
      const incidents = this.threatIntelligence.getOpenIncidents();
      return incidents.length ? `📍 Open incidents:\n${incidents.map(i => `• [${i.status}] Severity: ${i.severity}`).join('\n')}` : `✅ No open incidents.`;
    }
    if (target === 'plugins') {
      const tools = this.orchestrator.listTools().filter(t => t.name.includes(':'));
      return tools.length ? `🔌 Plugin tools:\n${tools.map(t => `• ${t.name}: ${t.description}`).join('\n')}` : `No plugins loaded.`;
    }
    if (target === 'providers') {
      return llmManager ? `🤖 LLM providers: ${llmManager.list().join(', ')}` : `LLM not configured.`;
    }

    return `Try: "show agents", "show tools", "show workflows", "show plugins", or "show providers"`;
  }

  private handleHelp(): string {
    return `
👋 Hi! I'm ARIA, your AI assistant. Just talk to me naturally!

**Things I can do:**

🧮 **Math**: "what's 42 * 17?" or "calculate 100 / 4"
🌐 **Web**: "fetch https://api.example.com/data"
📁 **Files**: "read file config.json" or "list directory"
🔍 **Search**: "search for TypeScript tutorials"
📊 **Git**: "git status" or "git diff"

🔄 **Workflows**: "show workflows" or "run workflow daily-check"
🤖 **AI Chat**: "ask Claude to explain recursion" or "use GPT to write a poem"
📈 **Stats**: "how's the system doing?" or "show metrics"

📋 **Info**: "show agents", "show tools", "show plugins"
❓ **Help**: "help" or "what can you do?"

Just type what you need - no special commands required!`;
  }

  private handleStatus(context: ConversationContext): string {
    return `📊 Session: ${context.sessionId.slice(0, 20)}...
👤 User: ${context.userId} (${context.userRole})
💬 Messages: ${context.conversationHistory.length}
⏳ Pending approvals: ${this.pendingApprovals.size}`;
  }

  private async handleApproval(context: ConversationContext, approved: boolean): Promise<{
    response: string; result?: unknown; toolExecuted: boolean;
  }> {
    // Load from storage if empty
    if (this.pendingApprovals.size === 0 && this.storage) {
      const approvals = await this.storage.getApprovals();
      for (const a of approvals) {
        this.pendingApprovals.set(a.approvalId, {
          timestamp: new Date(a.createdAt), role: 'user', content: 'Pending',
          toolName: a.toolName, agentId: a.agentId, parameters: a.parameters,
          sessionId: a.sessionId, riskScore: a.riskScore, requiresApproval: true,
        });
      }
    }

    const entry = Array.from(this.pendingApprovals.entries())
      .find(([, t]) => t.sessionId === context.sessionId) || this.pendingApprovals.entries().next().value;
    
    if (!entry) return { response: `Nothing pending to ${approved ? 'approve' : 'deny'}. No pending approvals.`, toolExecuted: false };

    const [approvalId, turn] = entry;
    this.pendingApprovals.delete(approvalId);
    if (this.storage) await this.storage.deleteApproval(approvalId);

    if (!approved) return { response: `❌ Action denied. Cancelled.`, toolExecuted: false };

    if (!turn.toolName || !turn.agentId) return { response: `Invalid approval state.`, toolExecuted: false };

    try {
      const result = await this.orchestrator.orchestrateToolCall({
        agentId: turn.agentId, toolName: turn.toolName, input: turn.parameters || {},
        userId: context.userId, profile: (context.metadata.profile as 'core' | 'cyber') || 'core',
      });
      return { response: `✅ Approved!\n${this.formatResult(turn.toolName, result)}`, result, toolExecuted: true };
    } catch (e) {
      return { response: `Failed: ${e instanceof Error ? e.message : e}`, toolExecuted: false };
    }
  }

  private findAgent(toolName: string): string | undefined {
    return this.orchestrator.listAgents().find(a => a.tools.includes(toolName))?.id;
  }

  private formatResult(tool: string, result: unknown): string {
    const r = (result as { result?: { ok?: boolean; data?: unknown } })?.result;
    if (tool === 'math_eval' && r?.ok) return `✅ Result: **${(r.data as { result?: unknown })?.result}**`;
    if (tool === 'echo') return `🔊 ${JSON.stringify(r)}`;
    return `✅ Done: ${JSON.stringify(r, null, 2).slice(0, 500)}`;
  }

  async getConversationHistory(sessionId: string): Promise<ConversationTurn[]> {
    return (await this.getContext(sessionId))?.conversationHistory || [];
  }

  endConversation(sessionId: string): void {
    this.contexts.delete(sessionId);
    this.storage?.deleteSession(sessionId);
  }

  private async getContext(sessionId: string): Promise<ConversationContext | undefined> {
    const existing = this.contexts.get(sessionId);
    if (existing) return existing;
    if (!this.storage) return undefined;

    const stored = await this.storage.getSession(sessionId);
    if (!stored) return undefined;

    const context: ConversationContext = {
      userId: stored.userId, sessionId: stored.sessionId, userRole: stored.userRole as RoleType,
      conversationHistory: stored.conversationHistory.map(t => ({ ...t, timestamp: new Date(t.timestamp) })),
      agentAssignments: new Map(), activeAgent: stored.activeAgent, metadata: stored.metadata,
    };
    this.contexts.set(sessionId, context);
    return context;
  }

  private async persistSession(context: ConversationContext): Promise<void> {
    await this.storage?.saveSession({
      sessionId: context.sessionId, userId: context.userId, userRole: context.userRole,
      conversationHistory: context.conversationHistory.map(t => ({ ...t, timestamp: t.timestamp.toISOString() })),
      activeAgent: context.activeAgent, metadata: context.metadata, updatedAt: new Date().toISOString(),
    });
  }
}
