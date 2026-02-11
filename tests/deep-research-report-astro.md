# Forensic Code Audit and Security Intelligence Report: Senpai-Sama7/Astro

## Connector scope and repository context

**Enabled connectors (as requested):** GitHub.

**Repository scope (strict):** This audit is limited to the single GitHub repository **Senpai-Sama7/Astro** (no other repos, forks, gists, or organizations were reviewed).

**High-level context inferred from the codebase:** The repository appears to combine multiple “Astro” sub-systems under one roof: a TypeScript/Node.js service (Express + Socket.IO + JWT auth, tool orchestration), a Python FastAPI service (API + WebSocket broadcasting + agent engine integration), and Python CLI/TUI utilities (e.g., an “Astro OS” agent shell) that can execute OS commands. This multi-runtime design expands the attack surface and creates configuration drift risk (controls implemented in one runtime are not automatically present in the others).

**Core security posture takeaway:** The repo contains **agent/tooling features that are inherently high-risk** (filesystem access, HTTP fetchers, shell execution, plugin loading). In an “AI agent” architecture, these are not automatically “bad,” but they demand strong and consistent guardrails (authn/z, allowlists, sandboxing, auditability, and safe defaults). OWASP explicitly calls out categories like SSRF, injection, and unsafe resource access when untrusted input influences network, filesystem, or command execution flows. citeturn0search2turn2search7turn1search8

## Audit methodology and tooling blueprint

This report is based primarily on **manual static review** of security-relevant modules and configuration, supplemented by a **recommended** reproducible toolchain you can run in CI/CD to validate and maintain findings.

**What was performed (static-focused):**
- Architectural inventory and trust-boundary mapping (what accepts input, what performs privileged actions, and where enforcement happens).
- Manual review of high-risk primitives:
  - URL fetchers (SSRF class risk).
  - File I/O and path validation (path traversal / symlink escape class risk).
  - Process spawning and shell execution (command injection class risk).
  - Authentication/authorization middleware and route controls.
  - WebSocket handshake/auth patterns and token handling.
  - Dependency pinning and workflow checks.

**What is recommended for a full “forensic-grade” verification run (static + dynamic):**
- **SAST (TypeScript/Node):** Semgrep (OWASP rules), ESLint security plugins, CodeQL (if enabled), npm audit.
- **SAST (Python):** Bandit for code anti-patterns (e.g., shell execution), Ruff, mypy-type checks.
- **Dependency & vuln scanning:**
  - Python: pip-audit (PyPA advisory database / OSV backends). citeturn0search0turn7search4
  - Node: npm audit; optionally OSV-Scanner for cross-ecosystem.
- **DAST / API security testing:** OWASP ZAP baseline for HTTP endpoints; WebSocket testing extensions (OWASP ZAP supports WebSocket testing per OWASP guidance). citeturn6search0
- **Fuzzing / robustness:** schema fuzzing for JSON endpoints; property-based tests for path validators; WebSocket message mutation.
- **CI integrity:** require lockfiles, SBOM output (CycloneDX), and signed build artifacts.

**Notes on “dynamic analysis” constraints:** I did not execute the services, connect to a running instance, or validate runtime network behavior. Any “reproduction steps” below are designed to be safe, local, and ethical (run only in your own environment).

## Architectural inventory and attack surface mapping

The codebase partitions into several **high-risk capability zones**:

**Node/TypeScript zone (Express + tool orchestration + Socket.IO):**
- JWT-based auth and role permissions are present (good baseline), and there is a dedicated “security gateway” for risk scoring / approvals.
- Tooling provides filesystem, HTTP, lint/test execution, and other operations. This is a classic “agent tools” pattern; the main question is whether *every* privileged tool is strongly gated and whether defaults are safe.

**Python FastAPI zone (HTTP + WebSocket + agent engine):**
- FastAPI service exposes endpoints for workflows, file operations, telemetry, chat, and WebSocket broadcasting.
- Middleware implements authentication, rate limiting, CSRF handling, security headers; correctness of exempt paths and matching rules is critical.

**Python CLI/TUI zone (Astro OS / shells):**
- Contains utilities that can execute commands via a shell. Bandit explicitly flags “shell execution” patterns as dangerous because they are vulnerable to injection if untrusted input ever reaches them. citeturn1search0turn1search4
- Even if “local-only,” these tools can still be exploited via prompt injection and unsafe defaults in an LLM-command loop (a real operational risk in agent architectures).

**Cross-cutting risks:**
- **SSRF:** Any “fetch URL and process response” path is SSRF-prone without robust validation, normalization, DNS/IP checks, and redirect policy. OWASP explains why SSRF defenses based on regex/blacklists are brittle and recommends safe-by-construction validation and allowlisting. citeturn0search1turn0search2
- **WebSockets:** OWASP highlights WebSockets as easy to ship insecurely (auth bypass, CSWSH, origin validation failures, logging gaps, DoS vectors). citeturn6search0
- **Tokens in URLs:** Passing tokens in query strings is a known weakness (CWE-598) because URLs leak via logs/history/referers. citeturn5search0turn5search2

## Findings with code-level evidence

### Critical findings

**Authentication and throttling bypass risk in Python middleware due to overly-broad exemption logic**
- **What it means:** If an auth/rate-limit middleware uses prefix matching (`startswith`) and includes the root path (`"/"`) in its exempt list, then *every request* matches and bypasses enforcement.
- **Why this matters:** This can silently turn “protected” endpoints into unauthenticated endpoints, including file read/write and command/workflow execution routes.
- **Impact:** Remote unauthorized access if the service is reachable (container binds to `0.0.0.0`, reverse proxy, or developer runs it exposed).
- **Severity rationale:** This is a “single-line misconfiguration class” that collapses the security model (CWE-306 / CWE-287 style failure mode).

Safe reproduction (local-only):
1. Start the FastAPI service locally (Docker or direct).
2. Attempt to access an endpoint that should require auth (e.g., a workflow or file endpoint) **without any API key / auth header**.
3. If response is 200/OK (or provides data) rather than 401/403, exemption enforcement is broken.

Remediation preview (patch shown later): remove `"/"` from exempt prefixes and implement exact-match or safe-prefix matching.

**Unauthenticated WebSocket exposure risk in Python FastAPI**
- **What it means:** A WebSocket endpoint that accepts connections without authentication and then broadcasts internal events can leak sensitive operational data (telemetry, filenames, user prompts, system messages).
- **Why this matters:** OWASP warns that WebSockets often ship without authentication because typical HTTP middleware does not automatically apply after upgrade, and monitoring often misses in-band WebSocket traffic. citeturn6search0
- **Impact:** Passive data exfiltration; in some designs, could lead to active command/control if message handlers trigger privileged actions.
- **Severity rationale:** If broadcast content includes secrets, file paths, command results, or user content, this becomes a serious confidentiality breach.

Safe reproduction (local-only):
1. Run the service locally.
2. Connect to the WebSocket endpoint from a separate client (no credentials).
3. Observe whether you receive telemetry or events without auth.

Remediation: enforce token-based authentication for the WebSocket handshake and validate `Origin` allowlists as per OWASP. citeturn6search0

### High findings

**SSRF-capable URL fetch and HTML extraction tool without a strong allowlist**
- **What it means:** A tool that fetches arbitrary URLs and processes responses can be abused to probe internal services (loopback, RFC1918, cloud metadata) if attacker-controlled input reaches it.
- **Why this matters:** OWASP describes SSRF as the ability to make the server perform unintended requests, including metadata endpoints like `169.254.169.254` and internal REST interfaces. citeturn0search2turn0search1
- **Exploitability factors:** Whether untrusted users can call the tool; whether the tool follows redirects; whether it blocks private IPs and DNS rebinding; whether there is a strict allowlist.
- **Impact:** Internal network enumeration and potentially credential theft in cloud environments.

Safe reproduction (local-only):
1. In a test environment only, attempt to use the tool to fetch a local service on `127.0.0.1:<port>` that is not externally accessible.
2. If it returns content, SSRF is viable.

Remediation: implement a **default-deny** URL policy (scheme allowlist + domain allowlist + IP range deny + redirect controls). OWASP emphasizes that blacklists/regex checks are insufficient. citeturn0search1turn0search2

**Shell execution primitives in Python agent tools and CLI shells**
- **What it means:** The repo contains utilities that execute OS commands using a shell (e.g., “subprocess shell mode” patterns). This is a known hazardous pattern.
- **Why this matters:** Bandit’s security rules flag shell execution because it is vulnerable to injection if variable/untrusted input can influence the command string. citeturn1search0turn1search4
- **In an LLM-agent context:** Even if the user does not type a command directly, prompt injection can cause the model to propose unsafe commands; relying on the model to self-label “dangerous” commands is not a robust control.

Safe reproduction (local-only):
- Demonstrate that the shell tool can execute benign commands like `echo` or `whoami` in a sandboxed directory.
- Do **not** test destructive commands.

Remediation: eliminate shell execution where possible; use `subprocess.run([...], shell=False)` equivalents; enforce allowlisted commands; run in a locked-down sandbox (container, seccomp, AppArmor). OWASP’s injection guidance emphasizes preventing untrusted input from reaching command execution sinks. citeturn2search7

### Medium findings

**File write path validation vulnerable to symlink-escape edge cases**
- **What it means:** A common pitfall: validating a path with `realpath` fails open when the *target file doesn’t exist yet*, allowing a symlinked parent directory to redirect writes outside the intended workspace.
- **Why this matters:** OWASP ASVS requires protection against path traversal for untrusted file paths and calls out realpath-style defenses (“keep it real with realpath”)—but correctness matters in edge cases. citeturn1search8turn2search9
- **Impact:** Potential to overwrite files outside workspace if the process has permissions (persistence, sabotage, secret overwrite).

Safe reproduction (local-only, non-destructive):
1. Create a temp directory outside the workspace (e.g., `/tmp/outside_safe`).
2. Inside the workspace, create a symlink directory `link -> /tmp/outside_safe`.
3. Call the “write file” tool with path `link/test.txt`.
4. If `/tmp/outside_safe/test.txt` is created, the validator is symlink-bypassable.

Remediation: validate the **realpath of the parent directory**; reject symlinked parents; consider `O_NOFOLLOW` where available; avoid TOCTOU by opening files safely.

**Security risk scoring / approval logic under-classifies tool sensitivity**
- **What it means:** If only a narrow subset of tools are marked “sensitive,” other high-impact tools (filesystem writes, git operations, test runners that execute scripts) may run without explicit approval.
- **Why this matters:** In agent systems, “tool gating” is one of the last lines of defense. Incomplete classification creates surprising escalation paths.
- **Impact:** Accidental destructive actions or abuse by compromised tokens/users.

Remediation: expand sensitivity classification to include filesystem mutation, code execution/test runners, content extraction, and any plugin/module loading.

**Helmet / CSP disabled to permit inline scripts**
- **What it means:** Disabling CSP removes a major mitigation against XSS and script injection.
- **Why this matters:** Helmet’s documentation emphasizes that CSP mitigates a large class of attacks, including XSS; disabling it is sometimes necessary but should be narrowly scoped. citeturn2search2turn2search4turn2search5
- **Impact:** Increased blast radius if any reflected/stored XSS exists elsewhere.

Remediation: re-enable CSP with a dashboard-specific policy; move inline scripts to static files or use nonces/hashes.

### Supply chain, dependency, and configuration findings

**Lockfile uncertainty and “npm ci” expectation**
- **What it means:** CI and Docker builds that use `npm ci` require a lockfile (`package-lock.json` or shrinkwrap). npm’s own documentation states `npm ci` requires an existing lockfile. citeturn3search1turn3search2
- **Security impact:** Without lockfiles, dependency resolution is non-deterministic, increasing the risk of supply-chain surprises and complicating incident response (“what actually shipped?”).

**Protobuf CVE handling appears incomplete**
- **What it means:** The repo references protobuf constraints intended to avoid a security issue; **CVE-2026-0994** is a protobuf DoS vulnerability fixed in newer versions (e.g., 6.33.5+ per advisories). citeturn7search1turn7search3
- **Risk:** Version ranges that “avoid one bad version” can still include other vulnerable versions. Best practice is to pin to a known fixed version range and validate with pip-audit. citeturn0search0turn7search4

**Tokens and secrets in dev configs**
- **What it means:** docker-compose and dev routes may include default secrets or “dev token issuance” patterns. Even if intended for development, they are frequently deployed accidentally.
- **Why this matters:** Secret scanning exists because accidental commits and mis-deployments happen; GitHub secret scanning is designed to detect leaked credential formats and warn quickly. citeturn3search8turn3search0

## Risk assessment and exploitability analysis

### Severity model used

I used a pragmatic model aligned with “real exploitability” for agent systems:
- **Critical:** collapses auth/z boundary or enables remote unauth command/file execution.
- **High:** enables SSRF, meaningful data exfiltration, or reliable sandbox escape within typical deployments.
- **Medium:** requires additional preconditions (symlink setup, misconfig), or increases blast radius of other bugs.
- **Low:** best-practice gaps with limited standalone exploitability.

### Exploit chains that matter most

**Chain: auth bypass → file access / workflow execution**
- If middleware exemption logic bypasses auth/rate-limit, an attacker can directly call privileged endpoints (file read/write, workflow execution).
- This is the most dangerous class because it turns the service into a remotely reachable “agent runner.”

**Chain: SSRF → internal pivot**
- SSRF can map internal services or metadata endpoints if allowlists are absent/weak. OWASP specifically notes metadata endpoints and internal databases as common SSRF targets. citeturn0search2

**Chain: WebSocket unauth → passive intel → targeted follow-on**
- OWASP warns WebSocket monitoring gaps and auth oversights can enable silent data leakage. citeturn6search0

**Chain: symlink escape → persistence**
- A symlink escape on write can become persistence if the process can overwrite startup scripts, cron entries, or plugin modules.

## Remediation guidance with patches and hardening

Below are targeted patches/diffs designed to eliminate the highest-risk failure modes. These are illustrative and may require minor adaptation to match exact filenames and structures.

### Fix exemption matching so auth and rate limiting cannot be bypassed by “/”

```diff
diff --git a/src/api/middleware.py b/src/api/middleware.py
@@
-class SecurityConfig:
-    exempt_paths = {"/", "/health", "/ready", "/metrics", "/docs", "/openapi.json"}
+class SecurityConfig:
+    # Exact-path exemptions only (never include "/")
+    exempt_paths = {"/health", "/ready", "/metrics", "/docs", "/openapi.json"}
+    exempt_prefixes = {"/static/", "/assets/"}  # if you truly need prefix exemptions
@@
-def is_exempt(path: str) -> bool:
-    return any(path.startswith(exempt) for exempt in security_config.exempt_paths)
+def is_exempt(path: str) -> bool:
+    if path in security_config.exempt_paths:
+        return True
+    return any(path.startswith(prefix) for prefix in security_config.exempt_prefixes)
```

**Why:** Prefix-matching exemptions are easy to get catastrophically wrong. This patch makes exemptions explicit and safe.

### Enforce WebSocket authentication and origin allowlisting

OWASP recommends explicit authentication and origin validation for WebSocket handshakes. citeturn6search0

```diff
diff --git a/src/api/server.py b/src/api/server.py
@@
-@app.websocket("/ws")
-async def ws_endpoint(websocket: WebSocket):
-    await websocket.accept()
+@app.websocket("/ws")
+async def ws_endpoint(websocket: WebSocket):
+    # Example: require a short-lived token as a query param or via a subprotocol header.
+    # Prefer NOT putting long-lived tokens in URLs (CWE-598); if unavoidable, redact logs. citeturn5search0turn6search0
+    token = websocket.query_params.get("token")
+    origin = websocket.headers.get("origin")
+    if origin not in {"https://your-ui.example.com"}:
+        await websocket.close(code=1008)
+        return
+    if not token or not await authenticate_websocket_token(token):
+        await websocket.close(code=1008)
+        return
+    await websocket.accept()
```

### Harden “write file” path safety against symlink-parent escapes

```diff
diff --git a/src/astro/tools.ts b/src/astro/tools.ts
@@
-function isPathSafe(filePath: string): boolean {
-  const fullPath = path.resolve(WORKSPACE_DIR, filePath);
-  try {
-    const resolvedFullPath = fs.realpathSync(fullPath);
-    const workspaceReal = fs.realpathSync(WORKSPACE_DIR);
-    return resolvedFullPath.startsWith(workspaceReal);
-  } catch {
-    // File doesn't exist yet; fallback check
-    const workspaceResolved = path.resolve(WORKSPACE_DIR);
-    return fullPath.startsWith(workspaceResolved);
-  }
-}
+function isPathSafeForWrite(filePath: string): boolean {
+  const fullPath = path.resolve(WORKSPACE_DIR, filePath);
+  const workspaceReal = fs.realpathSync(WORKSPACE_DIR);
+
+  // Validate the real path of the parent directory (prevents symlink-parent escapes)
+  const parent = path.dirname(fullPath);
+  const parentReal = fs.realpathSync(parent);
+  if (!parentReal.startsWith(workspaceReal + path.sep)) return false;
+
+  // Reject if the final path segment is a symlink (if it already exists)
+  if (fs.existsSync(fullPath)) {
+    const st = fs.lstatSync(fullPath);
+    if (st.isSymbolicLink()) return false;
+  }
+  return true;
+}
@@
-  if (!isPathSafe(filePath)) {
+  if (!isPathSafeForWrite(filePath)) {
     return { success: false, error: 'Invalid file path: must be within workspace directory' };
   }
```

### Expand the security gateway’s sensitivity model

```diff
diff --git a/src/otis/security-gateway.ts b/src/otis/security-gateway.ts
@@
-const SENSITIVE_TOOLS = new Set(['http_request', 'math_eval']);
+const SENSITIVE_TOOLS = new Set([
+  'http_request',
+  'content_extract',
+  'read_file',
+  'write_file',
+  'list_dir',
+  'git_status',
+  'git_diff',
+  'run_tests',
+  'lint_code',
+  'math_eval'
+]);
```

### SSRF defenses for URL fetch tools

OWASP’s SSRF guidance emphasizes robust URL parsing, allowlists, and defenses against DNS rebinding and IP literal tricks. citeturn0search1turn0search2

Minimum viable remediation:
- Allow only `https:` (and maybe `http:` in dev).
- Domain allowlist required for production.
- Resolve DNS and block private/loopback/link-local ranges.
- Disable redirects or re-validate each redirect hop.

### Dependency hardening

**Python:**
- Run `pip-audit -r requirements.txt` in CI. citeturn0search0  
- Pin protobuf to a fixed, non-vulnerable range given CVE-2026-0994 advisories (e.g., `protobuf>=5.29.6,<6.0.0` or `protobuf>=6.33.5`). citeturn7search1turn7search3

**Node:**
- Ensure a lockfile exists and is committed. `npm ci` requires it. citeturn3search1  
- Add `npm audit --audit-level=high` gate in CI.

## Prioritized action plan and effort estimate

### Immediate containment

**Disable or strictly bind all agent services to localhost by default** (especially the Python FastAPI service), and require explicit opt-in to listen on external interfaces. This reduces the probability that a dev-only misconfiguration becomes remotely exploitable.

**Remove or fix any middleware exemption pattern that can bypass auth/rate limits** (Critical). This is the highest ROI fix because it restores the trust boundary.

Estimated effort: 0.5–1.5 engineering days (including tests).

### Short-term hardening

**WebSocket authentication + origin allowlisting** guided by OWASP WebSocket recommendations. citeturn6search0  
Estimated effort: 1–3 days.

**SSRF defenses**: convert all URL fetchers to default-deny allowlists and safe resolution; add regression tests. citeturn0search1turn0search2  
Estimated effort: 2–5 days.

**Filesystem tool symlink-escape protections** with parent-realpath enforcement and dedicated tests (symlink + non-existent target). citeturn1search8  
Estimated effort: 2–4 days.

### Medium-term posture improvements

**Command execution containment:** tighten or remove shell-based execution in Python utilities; if kept, require containerized sandboxing and strict allowlists; follow the spirit of Bandit’s shell execution warnings. citeturn1search0turn1search4  
Estimated effort: 3–8 days depending on refactor depth.

**Restore CSP with scoped exceptions** (dashboard-specific handling) using Helmet guidance. citeturn2search2turn2search5  
Estimated effort: 1–3 days.

**Supply chain determinism:** lockfiles + pip hashes + SBOM + CI gating (pip-audit). citeturn0search0turn3search1  
Estimated effort: 2–6 days.

## Sources

OWASP, MITRE, and primary tool documentation were used to ground the risk analysis and recommended remediations, including SSRF prevention, injection/command execution guidance, path traversal requirements, WebSocket security practices, token leakage concerns, and dependency auditing tooling. citeturn0search1turn0search2turn2search7turn1search8turn6search0turn5search0turn0search0turn3search1turn7search3turn7search1turn2search2