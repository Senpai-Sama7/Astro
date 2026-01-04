# ARIA - Advanced Reasoning Interface for Agents
## Turn-by-Turn Natural Language Control System

---

## Quick Start: Talk to ASTRO

### 1. Start a Conversation

```bash
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "you",
    "userRole": "analyst",
    "message": "help"
  }'
```

**Response:**
```json
{
  "sessionId": "session_1704307000000_abc123",
  "message": "help",
  "response": "📚 Available Commands:\n\n🧠 Execute Tools:\n  - \"execute echo 'hello'\" - Echo a message\n  - \"calculate 2 + 2\" - Evaluate math expressions\n  - \"fetch https://example.com\" - Make HTTP requests\n...",
  "toolExecuted": false,
  "conversationHistory": [
    { "role": "user", "content": "help" },
    { "role": "system", "content": "📚 Available Commands:..." }
  ]
}
```

**Keep the `sessionId` for all follow-up messages.**

---

## Example Conversations

### Example 1: Simple Calculation

```bash
# First message (creates session)
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "you",
    "userRole": "analyst",
    "message": "calculate 5 * 4"
  }'
```

**Response:**
```json
{
  "sessionId": "session_1704307000000_abc123",
  "response": "✅ Calculation result: **20**",
  "toolExecuted": true,
  "result": { "ok": true, "data": { "expression": "5 * 4", "result": 20 } }
}
```

---

### Example 2: Multi-Turn Conversation

```bash
# Turn 1: See available agents
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "you",
    "userRole": "analyst",
    "sessionId": "session_1704307000000_abc123",
    "message": "show agents"
  }'

# Response shows all agents and their available tools

# Turn 2: Query threats
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "you",
    "userRole": "analyst",
    "sessionId": "session_1704307000000_abc123",
    "message": "show threats"
  }'

# Response shows critical threats

# Turn 3: Execute a tool
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "you",
    "userRole": "analyst",
    "sessionId": "session_1704307000000_abc123",
    "message": "calculate 10 + 5"
  }'

# Response: Tool executes, returns result
```

---

### Example 3: Security-Aware Execution

```bash
# Red team user attempting high-risk action
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "attacker",
    "userRole": "red-team",
    "message": "calculate 2 + 2"
  }'
```

**Response (if risk threshold exceeded):**
```json
{
  "response": "⚠️ This action has a risk score of 45.5% and requires approval. Do you want to proceed? (yes/no)",
  "requiresApproval": true,
  "approvalId": "approval_1704307000000_xyz789"
}
```

**Follow up with approval:**
```bash
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "attacker",
    "userRole": "red-team",
    "sessionId": "session_1704307000000_abc123",
    "message": "yes"
  }'
```

**Response:**
```json
{
  "response": "✅ Action approved and executed.\n✅ Calculation result: **4**",
  "toolExecuted": true
}
```

---

## Complete Command Reference

### Tool Execution

| Command | Example | Result |
|---------|---------|--------|
| Echo | "echo hello world" | Returns the input |
| Calculate | "calculate 5 + 3 * 2" | Returns 11 |
| Fetch | "fetch https://httpbin.org/get" | Returns HTTP response |

### Information Queries

| Command | Example | Result |
|---------|---------|--------|
| Show Agents | "show agents" | Lists all agents and their tools |
| Show Tools | "show tools" | Lists all available tools |
| Show Threats | "show threats" | Lists critical threats |
| Show Incidents | "show incidents" | Lists open incidents |

### System Commands

| Command | Example | Result |
|---------|---------|--------|
| Help | "help" | Shows all available commands |
| Status | "status" | Shows current session status |

### Approval Commands

| Command | Purpose |
|---------|----------|
| "yes" or "approve" | Approve a pending action |
| "no" or "deny" | Reject a pending action |

---

## API Endpoints

### Main Conversation Endpoint

**POST /api/v1/aria/chat**

Request body:
```typescript
{
  userId: string;              // Who is using the system
  userRole: RoleType;          // 'admin' | 'analyst' | 'red-team' | 'blue-team' | 'read-only' | 'guest'
  message: string;             // Your natural language message
  sessionId?: string;          // Optional, created if not provided
}
```

Response:
```typescript
{
  sessionId: string;           // Use for follow-up messages
  message: string;             // Your message echoed back
  response: string;            // ARIA's response
  toolExecuted?: boolean;      // Whether a tool was executed
  result?: unknown;            // Tool result (if executed)
  requiresApproval?: boolean;  // Whether action needs approval
  approvalId?: string;         // ID for approval workflow
  conversationHistory?: Turn[]; // Last 10 turns
}
```

### Session Management

**POST /api/v1/aria/sessions**
Create a new conversation session.

**GET /api/v1/aria/sessions/:sessionId**
Retrieve full conversation history.

**DELETE /api/v1/aria/sessions/:sessionId**
End a conversation session.

**GET /api/v1/aria/examples**
Get example commands.

---

## Understanding Security Layers

### RBAC (Role-Based Access Control)

**6 Roles with Different Permissions:**

- **admin**: Full access to everything
- **analyst**: Can execute tools, view audit logs
- **red-team**: Can register new tools, higher risk tolerance
- **blue-team**: Can execute, register tools, view audit, modify risk
- **read-only**: Can only view audit logs
- **guest**: No permissions

### Risk Scoring (CVaR Algorithm)

Each action gets a risk score (0.0-1.0):

- **0.0-0.3**: Low risk (immediate execution)
- **0.3-0.6**: Medium risk (may require approval)
- **0.6-1.0**: High risk (requires approval)

Risk factors:
- User role (red-team = higher risk)
- Action type (tool registration = higher risk)
- Tool sensitivity (HTTP, math = higher risk)

### Audit Logging

Every action is logged:
- Immutable append-only log
- HMAC-SHA256 signatures (tamper-proof)
- Filterable by user, action, date
- Role-based access control on logs

---

## Real-World Scenarios

### Scenario 1: Security Analyst Investigating Threats

```
User: "show threats"
ARIA: "🚨 Critical threats:\n- [CRITICAL] SQL Injection: ..."

User: "show incidents"
ARIA: "📋 Open incidents:\n- [INVESTIGATING] Severity: HIGH"

User: "status"
ARIA: "📊 Session Status:\n..."
```

### Scenario 2: Red Team Pentester

```
User: "show agents"
ARIA: "📋 Available agents:\n- general-assistant: Can use echo, http_request, math_eval"

User: "fetch https://target.local/admin"
ARIA: "⚠️ This action has a risk score of 62.5% and requires approval."

User: "yes"
ARIA: "✅ Action approved and executed.\nHTTP request successful..."
```

### Scenario 3: Development/Testing

```
User: "help"
ARIA: "📚 Available Commands:..." 

User: "show tools"
ARIA: "🔧 Available tools:\n- echo\n- http_request\n- math_eval"

User: "echo 'test message'"
ARIA: "🔊 Echo: \"test message\""
```

---

## Error Handling

If something goes wrong, ARIA provides clear error messages:

```
User: "invalid command xyz"
ARIA: "I'm not sure what you're asking. Try 'help' for available commands."

User: "calculate 5 +"
ARIA: "Error: Invalid mathematical expression"

User: "fetch http://disallowed.com"
ARIA: "Error: Domain not whitelisted for HTTP requests"
```

---

## Advanced Features

### Context Awareness

ARIA maintains conversation context:
- Remembers which agent you're working with
- Tracks your role and permissions
- Maintains execution history
- Tracks risk assessments per action

### Intent Parsing

Natural language parsing handles:
- Variations: "show tools" vs "list tools" vs "what tools?"
- Tool parameter extraction: "calculate 2 + 2" → parses expression
- URL extraction: "fetch https://..." → extracts domain
- Approval phrases: "yes", "approve", "ok", "confirm"

### Approval Workflows

For high-risk actions:
1. User requests action
2. ARIA calculates risk score
3. If >= threshold, asks for approval
4. User responds "yes" or "no"
5. Action approved/denied
6. Logged to audit trail

---

## Tips & Tricks

1. **Save your session ID**: Keep the `sessionId` from your first message to use in follow-ups
2. **Use natural language**: "calculate 5 + 3" works better than formal JSON
3. **Ask for help**: "help" shows all available commands
4. **Check status**: "status" shows your current session info
5. **View history**: Use the `/sessions/:sessionId` endpoint to see full conversation

---

## What ARIA Does Behind the Scenes

1. **Parse Intent** - Understands what you're asking
2. **Check Permissions** - Verifies your role can do this action
3. **Calculate Risk** - Uses CVaR algorithm to score risk
4. **Request Approval** - If risk is high, asks for confirmation
5. **Find Agent** - Selects best agent for the job
6. **Execute Tool** - Runs the tool with your input
7. **Log Action** - Records to immutable audit log
8. **Generate Response** - Creates natural language response
9. **Return Result** - Sends back result + conversation history

---

**You're now using a production-ready conversational AI system with security, threat intelligence, and full auditability. Enjoy.** 🚀
