import { EventEmitter } from 'events';
import { AstroOrchestrator } from '../astro/orchestrator';
import { OTISSecurityGateway, RoleType } from '../otis/security-gateway';
import { C0Di3CyberIntelligence } from '../codi3/threat-intelligence';
import { SQLiteStorage } from '../services/storage';

export interface ConversationContext {
  userId: string;
  sessionId: string;
  userRole: RoleType;
  conversationHistory: ConversationTurn[];
  agentAssignments: Map<string, string>; // toolName -> agentId
  activeAgent?: string;
  metadata: Record<string, unknown>;
}

export interface ConversationTurn {
  timestamp: Date;
  role: 'user' | 'system';
  content: string;
  intent?: string; // Parsed intent (execute_tool, query_status, get_help, etc)
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
  intent: string; // execute, query, help, status, config, approve, deny
  confidence: number; // 0.0-1.0
  toolName?: string;
  agentId?: string;
  parameters?: Record<string, unknown>;
  naturalText: string;
}

/**
 * ARIA: Advanced Reasoning Interface for Agents
 * Conversational natural language layer that drives the entire system.
 * Handles intent parsing, tool orchestration, security checks, and response generation.
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

  /**
   * Start a new conversation session.
   */
  startConversation(userId: string, userRole: RoleType): ConversationContext {
    const sessionId = this.generateSessionId();
    const context: ConversationContext = {
      userId,
      sessionId,
      userRole,
      conversationHistory: [],
      agentAssignments: new Map(),
      metadata: { profile: (process.env.PROFILE as 'core' | 'cyber') || 'core' },
    };

    this.contexts.set(sessionId, context);
    void this.persistSession(context);

    return context;
  }

  /**
   * Main conversation handler - processes natural language input.
   */
  async chat(
    sessionId: string,
    userMessage: string
  ): Promise<{
    response: string;
    toolExecuted?: boolean;
    result?: unknown;
    requiresApproval?: boolean;
    approvalId?: string;
  }> {
    const context = await this.getContext(sessionId);
    if (!context) {
      throw new Error(`Session '${sessionId}' not found`);
    }

    // Add user message to history
    const userTurn: ConversationTurn = {
      timestamp: new Date(),
      role: 'user',
      content: userMessage,
    };
    context.conversationHistory.push(userTurn);

    try {
      // Parse intent from natural language
      const parsedIntent = this.parseIntent(userMessage);
      userTurn.intent = parsedIntent.intent;
      userTurn.toolName = parsedIntent.toolName;
      userTurn.agentId = parsedIntent.agentId;

      // Route based on intent
      let response: string;
      let result: unknown;
      let toolExecuted = false;
      let requiresApproval = false;
      let approvalId: string | undefined;
      let riskScore: number | undefined;

      switch (parsedIntent.intent) {
        case 'execute':
          ({
            response,
            result,
            toolExecuted,
            requiresApproval,
            approvalId,
            riskScore,
          } = await this.handleExecuteIntent(
            context,
            parsedIntent,
            userMessage
          ));
          userTurn.riskScore = riskScore;
          break;

        case 'query':
          response = await this.handleQueryIntent(context, parsedIntent);
          break;

        case 'help':
          response = this.handleHelpIntent(context, parsedIntent);
          break;

        case 'status':
          response = this.handleStatusIntent(context);
          break;

        case 'config':
          response = await this.handleConfigIntent(context, parsedIntent);
          break;

        case 'approve':
          ({
            response,
            result,
            toolExecuted,
          } = await this.handleApprovalIntent(context, parsedIntent, true));
          break;

        case 'deny':
          response = await this.handleApprovalIntent(
            context,
            parsedIntent,
            false
          ).then((r) => r.response);
          break;

        default:
          response = `I'm not sure what you're asking. Try "help" for available commands.`;
      }

      // Add system response to history
      const systemTurn: ConversationTurn = {
        timestamp: new Date(),
        role: 'system',
        content: response,
        result,
      };
      context.conversationHistory.push(systemTurn);
      void this.persistSession(context);

      // Log to security gateway
      this.securityGateway.logAction({
        timestamp: new Date(),
        userId: context.userId,
        role: context.userRole,
        action: parsedIntent.intent,
        resource: parsedIntent.toolName || 'conversation',
        decision: requiresApproval ? 'PENDING' : 'APPROVED',
        riskScore: userTurn.riskScore,
        metadata: {
          sessionId,
          intent: parsedIntent.intent,
          confidence: parsedIntent.confidence,
        },
      });

      return {
        response,
        toolExecuted,
        result,
        requiresApproval,
        approvalId,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const systemTurn: ConversationTurn = {
        timestamp: new Date(),
        role: 'system',
        content: `Error: ${errorMessage}`,
        error: errorMessage,
      };
      context.conversationHistory.push(systemTurn);
      void this.persistSession(context);

      return {
        response: `Sorry, I encountered an error: ${errorMessage}`,
      };
    }
  }

  /**
   * Parse natural language to extract intent and parameters.
   */
  private parseIntent(userMessage: string): ParsedUserIntent {
    const lower = userMessage.toLowerCase();

    // Help intent
    if (
      lower.includes('help') ||
      lower.includes('what can') ||
      lower.includes('how do i')
    ) {
      return {
        intent: 'help',
        confidence: 0.95,
        naturalText: userMessage,
      };
    }

    // Status intent
    if (
      lower.includes('status') ||
      lower.includes('what\'s happening') ||
      lower.includes('what is happening')
    ) {
      return {
        intent: 'status',
        confidence: 0.9,
        naturalText: userMessage,
      };
    }

    // Query intent
    if (
      lower.includes('show') ||
      lower.includes('list') ||
      lower.includes('get') ||
      lower.includes('tell me')
    ) {
      let queryTarget = '';
      if (lower.includes('agent')) queryTarget = 'agents';
      else if (lower.includes('tool')) queryTarget = 'tools';
      else if (lower.includes('threat')) queryTarget = 'threats';
      else if (lower.includes('incident')) queryTarget = 'incidents';

      return {
        intent: 'query',
        confidence: 0.85,
        parameters: { target: queryTarget },
        naturalText: userMessage,
      };
    }

    // Config intent
    if (lower.includes('config') || lower.includes('set') || lower.includes('configure')) {
      return {
        intent: 'config',
        confidence: 0.8,
        naturalText: userMessage,
      };
    }

    // Approval intent
    if (lower.includes('approve') || lower.includes('yes')) {
      return {
        intent: 'approve',
        confidence: 0.9,
        naturalText: userMessage,
      };
    }

    if (lower.includes('deny') || lower.includes('no')) {
      return {
        intent: 'deny',
        confidence: 0.9,
        naturalText: userMessage,
      };
    }

    // Execute intent (tool usage)
    // Try to match tool names
    const toolNames = ['echo', 'http_request', 'math_eval'];
    let matchedTool: string | undefined;
    for (const tool of toolNames) {
      if (lower.includes(tool.replace('_', ' ')) || lower.includes(tool)) {
        matchedTool = tool;
        break;
      }
    }

    // Extract parameters from natural language
    const parameters: Record<string, unknown> = {};

    if (matchedTool === 'echo') {
      const match = userMessage.match(/echo[:\s]+["']?([^"'\n]+)["']?/i);
      if (match) parameters.input = match[1];
    }

    if (matchedTool === 'math_eval') {
      const match = userMessage.match(/(?:calculate|compute|evaluate)\s+(?:the\s+)?([^.!?]+)/i);
      if (match) parameters.expression = match[1].trim();
    }

    if (matchedTool === 'http_request') {
      const urlMatch = userMessage.match(
        /https?:\/\/[^\s]+|fetch\s+([^\s]+)/i
      );
      if (urlMatch) parameters.url = urlMatch[0] || urlMatch[1];
      parameters.method = lower.includes('post') ? 'POST' : 'GET';
    }

    if (matchedTool) {
      return {
        intent: 'execute',
        confidence: Object.keys(parameters).length > 0 ? 0.85 : 0.65,
        toolName: matchedTool,
        parameters,
        naturalText: userMessage,
      };
    }

    // Default: treat as general query or help request
    return {
      intent: 'query',
      confidence: 0.5,
      naturalText: userMessage,
    };
  }

  /**
   * Handle execute intent - orchestrate tool execution.
   */
  private async handleExecuteIntent(
    context: ConversationContext,
    parsedIntent: ParsedUserIntent,
    userMessage: string
  ): Promise<{
    response: string;
    result?: unknown;
    toolExecuted: boolean;
    requiresApproval: boolean;
    approvalId?: string;
    riskScore?: number;
  }> {
    if (!parsedIntent.toolName) {
      return {
        response: `I found a tool mention but couldn't parse the parameters. Can you be more specific?`,
        toolExecuted: false,
        requiresApproval: false,
        riskScore: undefined,
      };
    }

    // Find best agent for this tool
    const agentId = this.findBestAgent(context, parsedIntent.toolName);
    if (!agentId) {
      return {
        response: `No agent available to execute tool '${parsedIntent.toolName}'. Your role might not have permission.`,
        toolExecuted: false,
        requiresApproval: false,
        riskScore: undefined,
      };
    }

    // Check RBAC
    if (!this.securityGateway.hasPermission(context.userRole, 'canExecuteTools')) {
      return {
        response: `Your role '${context.userRole}' does not have permission to execute tools.`,
        toolExecuted: false,
        requiresApproval: false,
        riskScore: undefined,
      };
    }

    // Calculate risk
    const riskScore = this.securityGateway.calculateRiskScore({
      role: context.userRole,
      action: 'execute_tool',
      resource: parsedIntent.toolName,
      toolName: parsedIntent.toolName,
    });

    const requiresApproval = this.securityGateway.requiresApproval(riskScore);

    if (requiresApproval) {
      // Store pending execution
      const approvalId = this.generateApprovalId();
      const turn: ConversationTurn = {
        timestamp: new Date(),
        role: 'user',
        content: userMessage,
        toolName: parsedIntent.toolName,
        agentId,
        parameters: parsedIntent.parameters || {},
        sessionId: context.sessionId,
        riskScore,
        requiresApproval: true,
      };
      this.pendingApprovals.set(approvalId, turn);
      if (this.storage) {
        await this.storage.saveApproval({
          approvalId,
          sessionId: context.sessionId,
          toolName: parsedIntent.toolName,
          agentId,
          parameters: parsedIntent.parameters || {},
          riskScore,
          createdAt: new Date().toISOString(),
        });
      }

      return {
        response: `⚠️ This action has a risk score of ${(riskScore * 100).toFixed(1)}% and requires approval. Do you want to proceed? (yes/no)`,
        toolExecuted: false,
        requiresApproval: true,
        approvalId,
        riskScore,
      };
    }

    // Execute tool
    try {
      const result = await this.orchestrator.orchestrateToolCall({
        agentId,
        toolName: parsedIntent.toolName,
        input: parsedIntent.parameters || {},
        userId: context.userId,
        profile: (context.metadata.profile as 'core' | 'cyber') || 'core',
        metadata: { sessionId: context.sessionId },
      });

      const response = this.generateExecutionResponse(parsedIntent.toolName, result);
      return {
        response,
        result,
        toolExecuted: true,
        requiresApproval: false,
        riskScore,
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      return {
        response: `Failed to execute tool: ${errorMsg}`,
        toolExecuted: false,
        requiresApproval: false,
        riskScore,
      };
    }
  }

  /**
   * Handle query intent - introspection and information requests.
   */
  private async handleQueryIntent(
    context: ConversationContext,
    parsedIntent: ParsedUserIntent
  ): Promise<string> {
    const target = (parsedIntent.parameters?.target as string) || '';

    if (target.includes('agent') || !target) {
      const agents = this.orchestrator.listAgents();
      return (
        `📋 Available agents:\n` +
        agents
          .map(
            (a) =>
              `- ${a.id}: ${a.description} (tools: ${a.tools.join(', ')})`
          )
          .join('\n')
      );
    }

    if (target.includes('tool')) {
      const tools = this.orchestrator.listTools();
      return (
        `🔧 Available tools:\n` +
        tools
          .map(
            (t) =>
              `- ${t.name}: ${t.description || 'No description'}`
          )
          .join('\n')
      );
    }

    if (target.includes('threat')) {
      const threats = this.threatIntelligence.getCriticalThreats();
      if (threats.length === 0) {
        return `✅ No critical threats detected.`;
      }
      return (
        `🚨 Critical threats:\n` +
        threats
          .map((t) => `- [${t.level}] ${t.title}: ${t.description}`)
          .join('\n')
      );
    }

    if (target.includes('incident')) {
      const incidents = this.threatIntelligence.getOpenIncidents();
      if (incidents.length === 0) {
        return `✅ No open incidents.`;
      }
      return (
        `📍 Open incidents:\n` +
        incidents
          .map((i) => `- [${i.status}] Severity: ${i.severity}`)
          .join('\n')
      );
    }

    return `I'm not sure what to query. Try: "show agents", "show tools", "show threats", or "show incidents".`;
  }

  /**
   * Handle help intent - show available commands.
   */
  private handleHelpIntent(
    _context: ConversationContext,
    _parsedIntent: ParsedUserIntent
  ): string {
    return `
📚 Available Commands:

🎯 Execute Tools:
  - "execute echo 'hello'" - Echo a message
  - "calculate 2 + 2" - Evaluate math expressions
  - "fetch https://example.com" - Make HTTP requests

📋 Information:
  - "show agents" - List available agents
  - "show tools" - List available tools
  - "show threats" - Show critical threats
  - "show incidents" - Show open incidents

⚙️ System:
  - "status" - Show conversation status
  - "help" - Show this help message

🔐 Approval:
  - "yes" or "approve" - Approve a pending action
  - "no" or "deny" - Reject a pending action
    `;
  }

  /**
   * Handle status intent - show current session status.
   */
  private handleStatusIntent(context: ConversationContext): string {
    return `
📊 Session Status:

User: ${context.userId}
Role: ${context.userRole}
Session ID: ${context.sessionId}
Conversation Turns: ${context.conversationHistory.length}
Active Agent: ${context.activeAgent || 'None'}
Pending Approvals: ${this.pendingApprovals.size}
    `;
  }

  /**
   * Handle config intent - configuration and settings.
   */
  private async handleConfigIntent(
    _context: ConversationContext,
    _parsedIntent: ParsedUserIntent
  ): Promise<string> {
    // TODO: Implement configuration handling
    return `Configuration management coming soon.`;
  }

  /**
   * Handle approval intent - approve or deny pending actions.
   */
  private async handleApprovalIntent(
    context: ConversationContext,
    _parsedIntent: ParsedUserIntent,
    approved: boolean
  ): Promise<{
    response: string;
    result?: unknown;
    toolExecuted: boolean;
  }> {
    if (this.pendingApprovals.size === 0) {
      await this.loadPendingApprovals();
    }

    if (this.pendingApprovals.size === 0) {
      return {
        response: `No pending approvals to ${approved ? 'approve' : 'deny'}.`,
        toolExecuted: false,
      };
    }

    // Get the most recent pending approval
    const matchingApproval = Array.from(this.pendingApprovals.entries()).find(
      ([, turn]) => turn.sessionId === context.sessionId
    );
    const entry = matchingApproval ?? this.pendingApprovals.entries().next().value;
    const [approvalId, turn] = entry || [undefined, undefined];
    if (!approvalId || !turn) {
      return {
        response: `No pending approvals to ${approved ? 'approve' : 'deny'}.`,
        toolExecuted: false,
      };
    }

    if (!approved) {
      this.pendingApprovals.delete(approvalId);
      if (this.storage) {
        await this.storage.deleteApproval(approvalId);
      }
      return {
        response: `Action denied: Tool execution cancelled.`,
        toolExecuted: false,
      };
    }

    // Execute the approved action
    if (!turn.toolName || !turn.agentId) {
      return {
        response: `Invalid approval state.`,
        toolExecuted: false,
      };
    }

    try {
      const result = await this.orchestrator.orchestrateToolCall({
        agentId: turn.agentId,
        toolName: turn.toolName,
        input: turn.parameters || {},
        userId: context.userId,
        profile: (context.metadata.profile as 'core' | 'cyber') || 'core',
        metadata: { sessionId: context.sessionId },
      });

      this.pendingApprovals.delete(approvalId);
      if (this.storage) {
        await this.storage.deleteApproval(approvalId);
      }

      const response = this.generateExecutionResponse(turn.toolName, result);
      return {
        response: `✅ Action approved and executed.\n${response}`,
        result,
        toolExecuted: true,
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      return {
        response: `Failed to execute approved action: ${errorMsg}`,
        toolExecuted: false,
      };
    }
  }

  /**
   * Find the best agent for a given tool.
   */
  private findBestAgent(context: ConversationContext, toolName: string): string | undefined {
    const agents = this.orchestrator.listAgents();
    for (const agent of agents) {
      if (agent.tools.includes(toolName)) {
        return agent.id;
      }
    }
    return undefined;
  }

  /**
   * Generate natural language response for tool execution.
   */
  private generateExecutionResponse(toolName: string, result: unknown): string {
    const toolResult = (result as { result?: unknown })?.result ?? result;

    if (toolName === 'math_eval') {
      const mathResult = toolResult as any;
      if (mathResult?.ok) {
        return `✅ Calculation result: **${mathResult.data?.result}**`;
      }
    }

    if (toolName === 'echo') {
      return `🔊 Echo: ${JSON.stringify(toolResult)}`;
    }

    if (toolName === 'http_request') {
      const httpResult = toolResult as any;
      if (httpResult?.ok) {
        return `✅ HTTP request successful. Response: ${JSON.stringify(httpResult.data).substring(0, 200)}...`;
      }
    }

    return `✅ Tool executed successfully: ${JSON.stringify(toolResult)}`;
  }

  /**
   * Get conversation history.
   */
  async getConversationHistory(sessionId: string): Promise<ConversationTurn[]> {
    const context = await this.getContext(sessionId);
    return context?.conversationHistory || [];
  }

  /**
   * End a conversation session.
   */
  endConversation(sessionId: string): void {
    this.contexts.delete(sessionId);
    if (this.storage) {
      void this.storage.deleteSession(sessionId);
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  private generateApprovalId(): string {
    return `approval_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  private async getContext(sessionId: string): Promise<ConversationContext | undefined> {
    const existing = this.contexts.get(sessionId);
    if (existing) {
      return existing;
    }

    if (!this.storage) {
      return undefined;
    }

    const stored = await this.storage.getSession(sessionId);
    if (!stored) {
      return undefined;
    }

    const context: ConversationContext = {
      userId: stored.userId,
      sessionId: stored.sessionId,
      userRole: stored.userRole as RoleType,
      conversationHistory: stored.conversationHistory.map((turn) => ({
        ...turn,
        timestamp: new Date(turn.timestamp),
      })),
      agentAssignments: new Map(),
      activeAgent: stored.activeAgent,
      metadata: stored.metadata,
    };

    this.contexts.set(sessionId, context);
    return context;
  }

  private async persistSession(context: ConversationContext): Promise<void> {
    if (!this.storage) {
      return;
    }
    await this.storage.saveSession({
      sessionId: context.sessionId,
      userId: context.userId,
      userRole: context.userRole,
      conversationHistory: context.conversationHistory.map((turn) => ({
        ...turn,
        timestamp: turn.timestamp.toISOString(),
      })),
      activeAgent: context.activeAgent,
      metadata: context.metadata,
      updatedAt: new Date().toISOString(),
    });
  }

  private async loadPendingApprovals(): Promise<void> {
    if (!this.storage) {
      return;
    }
    const approvals = await this.storage.getApprovals();
    for (const approval of approvals) {
      if (!this.pendingApprovals.has(approval.approvalId)) {
        this.pendingApprovals.set(approval.approvalId, {
          timestamp: new Date(approval.createdAt),
          role: 'user',
          content: 'Pending approval',
          toolName: approval.toolName,
          agentId: approval.agentId,
          parameters: approval.parameters,
          sessionId: approval.sessionId,
          riskScore: approval.riskScore,
          requiresApproval: true,
        });
      }
    }
  }
}
