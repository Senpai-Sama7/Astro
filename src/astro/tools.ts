import axios, { AxiosError } from 'axios';
import { execSync, execFileSync, spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { parse as parseHtml } from 'node-html-parser';
import { evaluate as mathEvaluate } from 'mathjs';
import { ToolInput, ToolResult, ToolContext } from './orchestrator';

// Workspace directory for file operations
const WORKSPACE_DIR = process.env.WORKSPACE_DIR || path.join(process.cwd(), 'workspace');

/**
 * Echo tool - returns input as-is (useful for testing and debugging)
 */
export async function echoTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const result: ToolResult = {
      ok: true,
      data: {
        echo: input,
        context: {
          requestId: context.requestId,
          profile: context.profile,
        },
      },
      elapsedMs: Date.now() - start,
    };
    return result;
  } catch (error) {
    return {
      ok: false,
      error: `Echo tool failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * HTTP Request tool - makes authenticated HTTP calls to whitelisted domains
 * Input: { url: string, method?: 'GET'|'POST'|'PUT'|'DELETE', headers?: object, data?: object }
 */
const WHITELISTED_DOMAINS = [
  'api.example.com',
  'api.github.com',
  'api.coindesk.com',
  'jsonplaceholder.typicode.com',
  'httpbin.org',
];

function isWhitelisted(url: string): boolean {
  try {
    const parsed = new URL(url);
    return WHITELISTED_DOMAINS.some((domain) => {
      // Exact match
      if (parsed.hostname === domain) return true;
      // Subdomain match: hostname must end with ".domain" and have exactly one more segment
      if (parsed.hostname?.endsWith(`.${domain}`)) {
        const hostParts = parsed.hostname.split('.');
        const domainParts = domain.split('.');
        return hostParts.length === domainParts.length + 1;
      }
      return false;
    });
  } catch {
    return false;
  }
}

export async function httpRequestTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();

  try {
    const url = input.url as string | undefined;
    const method = (input.method as string | undefined) || 'GET';
    const headers = (input.headers as Record<string, string> | undefined) || {};
    const data = input.data;

    if (!url) {
      return {
        ok: false,
        error: 'url is required',
        elapsedMs: Date.now() - start,
      };
    }

    if (!isWhitelisted(url)) {
      return {
        ok: false,
        error: `URL ${url} is not whitelisted. Allowed domains: ${WHITELISTED_DOMAINS.join(', ')}`,
        elapsedMs: Date.now() - start,
      };
    }

    if (!['GET', 'POST', 'PUT', 'DELETE'].includes(method.toUpperCase())) {
      return {
        ok: false,
        error: `Method ${method} is not allowed`,
        elapsedMs: Date.now() - start,
      };
    }

    const response = await axios({
      url,
      method: method.toUpperCase() as any,
      headers: { ...headers, 'User-Agent': 'Ultimate-System/1.0' },
      data,
      timeout: 10000,
    });

    return {
      ok: true,
      data: {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data,
      },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      ok: false,
      error: `HTTP request failed: ${axiosError.message}`,
      data: {
        status: axiosError.response?.status,
        statusText: axiosError.response?.statusText,
        message: axiosError.message,
      },
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * Math evaluation tool - safely evaluates mathematical expressions
 * Input: { expression: string }
 * Uses mathjs for safe evaluation without code injection risks
 */
export async function mathEvalTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();

  try {
    const expression = input.expression as string | undefined;

    if (!expression) {
      return {
        ok: false,
        error: 'expression is required',
        elapsedMs: Date.now() - start,
      };
    }

    if (expression.length > 200) {
      return {
        ok: false,
        error: 'Expression too long (max 200 characters)',
        elapsedMs: Date.now() - start,
      };
    }

    // Use mathjs for safe evaluation (no code injection possible)
    const result = mathEvaluate(expression);

    if (typeof result !== 'number' || !Number.isFinite(result)) {
      return {
        ok: false,
        error: 'Expression did not evaluate to a finite number',
        elapsedMs: Date.now() - start,
      };
    }

    return {
      ok: true,
      data: { expression, result },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Math evaluation failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}


// ============================================
// RESEARCH AGENT TOOLS
// ============================================

/**
 * Web search tool using DuckDuckGo
 * Input: { query: string, maxResults?: number }
 */
export async function webSearchTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const query = input.query as string;
    const maxResults = Math.min((input.maxResults as number) || 5, 20);

    if (!query) {
      return { ok: false, error: 'query is required', elapsedMs: Date.now() - start };
    }

    // Use DuckDuckGo HTML endpoint (no API key needed)
    const response = await axios.get('https://html.duckduckgo.com/html/', {
      params: { q: query },
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ASTRO/1.0)' },
      timeout: 10000,
      maxContentLength: 1024 * 1024, // 1MB limit
    });

    // Parse results using proper HTML parser (prevents ReDoS)
    const root = parseHtml(response.data);
    const links = root.querySelectorAll('a.result__a');
    const results = links.slice(0, maxResults).map((link) => ({
      title: link.innerText.trim(),
      url: link.getAttribute('href') || '',
      snippet: '',
    }));

    return {
      ok: true,
      data: { query, results, count: results.length },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Web search failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * Content extraction tool - fetches and extracts text from URL
 * Input: { url: string }
 */
export async function contentExtractTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const url = input.url as string;
    if (!url) {
      return { ok: false, error: 'url is required', elapsedMs: Date.now() - start };
    }

    const response = await axios.get(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ASTRO/1.0)' },
      timeout: 15000,
      maxContentLength: 1024 * 1024, // 1MB limit
    });

    // Strip HTML tags for plain text
    const text = response.data
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 5000); // Limit output

    return {
      ok: true,
      data: { url, content: text, length: text.length },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Content extraction failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

// ============================================
// FILESYSTEM AGENT TOOLS
// ============================================

function isPathSafe(filePath: string): boolean {
  try {
    const fullPath = path.resolve(WORKSPACE_DIR, filePath);
    // Use realpathSync to resolve symlinks and get actual filesystem location
    const resolved = fs.realpathSync(fullPath);
    const workspaceReal = fs.realpathSync(WORKSPACE_DIR);
    return resolved === workspaceReal || resolved.startsWith(workspaceReal + path.sep);
  } catch {
    // Path doesn't exist or isn't readable - check without symlink resolution
    const resolved = path.resolve(WORKSPACE_DIR, filePath);
    const workspaceResolved = path.resolve(WORKSPACE_DIR);
    return resolved === workspaceResolved || resolved.startsWith(workspaceResolved + path.sep);
  }
}

/**
 * Read file tool
 * Input: { path: string }
 */
export async function readFileTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const filePath = input.path as string;
    if (!filePath) {
      return { ok: false, error: 'path is required', elapsedMs: Date.now() - start };
    }
    if (!isPathSafe(filePath)) {
      return { ok: false, error: 'Path outside workspace not allowed', elapsedMs: Date.now() - start };
    }

    const fullPath = path.join(WORKSPACE_DIR, filePath);
    const content = fs.readFileSync(fullPath, 'utf-8');
    return {
      ok: true,
      data: { path: filePath, content, size: content.length },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Read file failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * Write file tool
 * Input: { path: string, content: string }
 */
export async function writeFileTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const filePath = input.path as string;
    const content = input.content as string;
    if (!filePath || content === undefined) {
      return { ok: false, error: 'path and content are required', elapsedMs: Date.now() - start };
    }
    if (!isPathSafe(filePath)) {
      return { ok: false, error: 'Path outside workspace not allowed', elapsedMs: Date.now() - start };
    }

    const fullPath = path.join(WORKSPACE_DIR, filePath);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, content, 'utf-8');
    return {
      ok: true,
      data: { path: filePath, written: content.length },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Write file failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * List directory tool
 * Input: { path?: string }
 */
export async function listDirTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const dirPath = (input.path as string) || '.';
    if (!isPathSafe(dirPath)) {
      return { ok: false, error: 'Path outside workspace not allowed', elapsedMs: Date.now() - start };
    }

    const fullPath = path.join(WORKSPACE_DIR, dirPath);
    const entries = fs.readdirSync(fullPath, { withFileTypes: true });
    const files = entries.map(e => ({ name: e.name, type: e.isDirectory() ? 'dir' : 'file' }));
    return {
      ok: true,
      data: { path: dirPath, entries: files },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `List dir failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

// ============================================
// GIT AGENT TOOLS
// ============================================

/**
 * Git status tool
 * Input: { cwd?: string }
 */
export async function gitStatusTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const cwd = (input.cwd as string) || process.cwd();
    const output = execFileSync('git', ['status', '--porcelain'], { cwd, encoding: 'utf-8', timeout: 5000 });
    const branch = execFileSync('git', ['branch', '--show-current'], { cwd, encoding: 'utf-8', timeout: 5000 }).trim();
    return {
      ok: true,
      data: { branch, status: output.trim().split('\n').filter(Boolean) },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Git status failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * Git diff tool
 * Input: { cwd?: string, file?: string }
 */
export async function gitDiffTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const cwd = (input.cwd as string) || process.cwd();
    const file = input.file as string;
    const args = file ? ['diff', '--', file] : ['diff'];
    const output = execFileSync('git', args, { cwd, encoding: 'utf-8', timeout: 10000 });
    return {
      ok: true,
      data: { diff: output.slice(0, 10000) }, // Limit output
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Git diff failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

// ============================================
// TEST AGENT TOOLS
// ============================================

/**
 * Run tests tool
 * Input: { command?: string, cwd?: string }
 */
export async function runTestsTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const cwd = (input.cwd as string) || process.cwd();
    let cmd: string;
    let args: string[];

    // Auto-detect test command if not provided
    if (input.command) {
      // Only allow known safe test commands
      const allowedCommands: Record<string, string[]> = {
        'npm test': ['npm', ['test']],
        'npm run test': ['npm', ['run', 'test']],
        'pytest': ['pytest', []],
        'jest': ['npx', ['jest']],
        'mocha': ['npx', ['mocha']],
      } as any;
      const normalized = (input.command as string).trim().toLowerCase();
      const match = Object.entries(allowedCommands).find(([k]) => k === normalized);
      if (!match) {
        return { ok: false, error: 'Only npm test, pytest, jest, or mocha allowed', elapsedMs: Date.now() - start };
      }
      [cmd, args] = match[1] as [string, string[]];
    } else if (fs.existsSync(path.join(cwd, 'package.json'))) {
      cmd = 'npm';
      args = ['test'];
    } else if (fs.existsSync(path.join(cwd, 'pytest.ini')) || fs.existsSync(path.join(cwd, 'pyproject.toml'))) {
      cmd = 'pytest';
      args = [];
    } else {
      return { ok: false, error: 'Could not detect test framework', elapsedMs: Date.now() - start };
    }

    const output = execFileSync(cmd, args, { cwd, encoding: 'utf-8', timeout: 120000 });
    return {
      ok: true,
      data: { command: `${cmd} ${args.join(' ')}`.trim(), output: output.slice(0, 10000) },
      elapsedMs: Date.now() - start,
    };
  } catch (error: any) {
    return {
      ok: false,
      error: `Tests failed`,
      data: { output: error.stdout?.slice(0, 5000) || error.message },
      elapsedMs: Date.now() - start,
    };
  }
}

// ============================================
// ANALYSIS AGENT TOOLS
// ============================================

/**
 * Lint code tool
 * Input: { path?: string, linter?: string }
 */
export async function lintCodeTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const targetPath = (input.path as string) || '.';
    const linter = input.linter as string;
    let cmd: string;
    let args: string[];

    // Validate path doesn't contain shell metacharacters
    if (!/^[\w./-]+$/.test(targetPath)) {
      return { ok: false, error: 'Invalid path characters', elapsedMs: Date.now() - start };
    }

    if (linter === 'eslint' || (!linter && fs.existsSync('package.json'))) {
      cmd = 'npx';
      args = ['eslint', targetPath, '--format', 'json'];
    } else if (linter === 'pylint' || (!linter && fs.existsSync('pyproject.toml'))) {
      cmd = 'pylint';
      args = [targetPath, '--output-format=json'];
    } else {
      return { ok: false, error: 'No linter detected or specified', elapsedMs: Date.now() - start };
    }

    const output = execFileSync(cmd, args, { encoding: 'utf-8', timeout: 60000 });
    return {
      ok: true,
      data: { linter: linter || 'auto', output: output.slice(0, 10000) },
      elapsedMs: Date.now() - start,
    };
  } catch (error: any) {
    // Linters often exit non-zero when issues found
    return {
      ok: true,
      data: { output: error.stdout?.slice(0, 10000) || 'Lint completed with issues' },
      elapsedMs: Date.now() - start,
    };
  }
}

// ============================================
// KNOWLEDGE AGENT TOOLS
// ============================================

const KNOWLEDGE_FILE = path.join(process.cwd(), 'data', 'knowledge.json');

/**
 * Save knowledge tool
 * Input: { key: string, value: any }
 */
export async function saveKnowledgeTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const key = input.key as string;
    const value = input.value;
    if (!key) {
      return { ok: false, error: 'key is required', elapsedMs: Date.now() - start };
    }

    let knowledge: Record<string, any> = {};
    if (fs.existsSync(KNOWLEDGE_FILE)) {
      knowledge = JSON.parse(fs.readFileSync(KNOWLEDGE_FILE, 'utf-8'));
    }
    knowledge[key] = { value, timestamp: new Date().toISOString() };
    fs.mkdirSync(path.dirname(KNOWLEDGE_FILE), { recursive: true });
    fs.writeFileSync(KNOWLEDGE_FILE, JSON.stringify(knowledge, null, 2));

    return {
      ok: true,
      data: { key, saved: true },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Save knowledge failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}

/**
 * Retrieve knowledge tool
 * Input: { key?: string }
 */
export async function retrieveKnowledgeTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const key = input.key as string;

    if (!fs.existsSync(KNOWLEDGE_FILE)) {
      return { ok: true, data: { knowledge: {} }, elapsedMs: Date.now() - start };
    }

    const knowledge = JSON.parse(fs.readFileSync(KNOWLEDGE_FILE, 'utf-8'));
    if (key) {
      return {
        ok: true,
        data: { key, value: knowledge[key] || null },
        elapsedMs: Date.now() - start,
      };
    }
    return {
      ok: true,
      data: { keys: Object.keys(knowledge), count: Object.keys(knowledge).length },
      elapsedMs: Date.now() - start,
    };
  } catch (error) {
    return {
      ok: false,
      error: `Retrieve knowledge failed: ${error instanceof Error ? error.message : 'unknown'}`,
      elapsedMs: Date.now() - start,
    };
  }
}


// ============================================
// ADDITIONAL TOOL INTEGRATIONS
// ============================================

/**
 * JSON Query tool - query JSON data with JSONPath-like syntax
 * Input: { data: object, query: string }
 */
export async function jsonQueryTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const data = input.data as Record<string, unknown>;
    const query = input.query as string;
    if (!data || !query) {
      return { ok: false, error: 'data and query are required', elapsedMs: Date.now() - start };
    }

    // Simple dot-notation query
    const parts = query.split('.');
    let result: unknown = data;
    for (const part of parts) {
      if (result && typeof result === 'object') {
        result = (result as Record<string, unknown>)[part];
      } else {
        result = undefined;
        break;
      }
    }

    return { ok: true, data: { query, result }, elapsedMs: Date.now() - start };
  } catch (error) {
    return { ok: false, error: `JSON query failed: ${error instanceof Error ? error.message : 'unknown'}`, elapsedMs: Date.now() - start };
  }
}

/**
 * Text transform tool - various text transformations
 * Input: { text: string, operation: 'upper'|'lower'|'reverse'|'count'|'base64_encode'|'base64_decode' }
 */
export async function textTransformTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const text = input.text as string;
    const operation = input.operation as string;
    if (!text || !operation) {
      return { ok: false, error: 'text and operation are required', elapsedMs: Date.now() - start };
    }

    let result: string | number;
    switch (operation) {
      case 'upper': result = text.toUpperCase(); break;
      case 'lower': result = text.toLowerCase(); break;
      case 'reverse': result = text.split('').reverse().join(''); break;
      case 'count': result = text.length; break;
      case 'base64_encode': result = Buffer.from(text).toString('base64'); break;
      case 'base64_decode': result = Buffer.from(text, 'base64').toString('utf-8'); break;
      default: return { ok: false, error: `Unknown operation: ${operation}`, elapsedMs: Date.now() - start };
    }

    return { ok: true, data: { operation, result }, elapsedMs: Date.now() - start };
  } catch (error) {
    return { ok: false, error: `Text transform failed: ${error instanceof Error ? error.message : 'unknown'}`, elapsedMs: Date.now() - start };
  }
}

/**
 * System info tool - get system information
 * Input: { type: 'os'|'memory'|'cpu'|'disk'|'env' }
 */
export async function systemInfoTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const type = (input.type as string) || 'os';
    let data: Record<string, unknown>;

    switch (type) {
      case 'os':
        data = {
          platform: process.platform,
          arch: process.arch,
          nodeVersion: process.version,
          uptime: process.uptime(),
        };
        break;
      case 'memory':
        const mem = process.memoryUsage();
        data = {
          heapUsed: Math.round(mem.heapUsed / 1024 / 1024) + 'MB',
          heapTotal: Math.round(mem.heapTotal / 1024 / 1024) + 'MB',
          rss: Math.round(mem.rss / 1024 / 1024) + 'MB',
        };
        break;
      case 'cpu':
        data = { cpus: require('os').cpus().length };
        break;
      case 'disk':
        const diskOutput = execSync('df -h / 2>/dev/null || echo "N/A"', { encoding: 'utf-8' });
        data = { disk: diskOutput.trim() };
        break;
      case 'env':
        data = {
          NODE_ENV: process.env.NODE_ENV,
          PROFILE: process.env.PROFILE,
          cwd: process.cwd(),
        };
        break;
      default:
        return { ok: false, error: `Unknown type: ${type}`, elapsedMs: Date.now() - start };
    }

    return { ok: true, data, elapsedMs: Date.now() - start };
  } catch (error) {
    return { ok: false, error: `System info failed: ${error instanceof Error ? error.message : 'unknown'}`, elapsedMs: Date.now() - start };
  }
}

/**
 * Timestamp tool - date/time operations
 * Input: { operation: 'now'|'parse'|'format', value?: string, format?: string }
 */
export async function timestampTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const operation = (input.operation as string) || 'now';
    let result: Record<string, unknown>;

    switch (operation) {
      case 'now':
        const now = new Date();
        result = {
          iso: now.toISOString(),
          unix: Math.floor(now.getTime() / 1000),
          utc: now.toUTCString(),
          local: now.toLocaleString(),
        };
        break;
      case 'parse':
        const value = input.value as string;
        if (!value) return { ok: false, error: 'value required for parse', elapsedMs: Date.now() - start };
        const parsed = new Date(value);
        result = {
          iso: parsed.toISOString(),
          unix: Math.floor(parsed.getTime() / 1000),
          valid: !isNaN(parsed.getTime()),
        };
        break;
      case 'format':
        const ts = input.value ? new Date(input.value as string) : new Date();
        result = {
          date: ts.toDateString(),
          time: ts.toTimeString(),
          iso: ts.toISOString(),
        };
        break;
      default:
        return { ok: false, error: `Unknown operation: ${operation}`, elapsedMs: Date.now() - start };
    }

    return { ok: true, data: result, elapsedMs: Date.now() - start };
  } catch (error) {
    return { ok: false, error: `Timestamp failed: ${error instanceof Error ? error.message : 'unknown'}`, elapsedMs: Date.now() - start };
  }
}

/**
 * Hash tool - compute hashes
 * Input: { text: string, algorithm?: 'md5'|'sha1'|'sha256'|'sha512' }
 */
export async function hashTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const text = input.text as string;
    const algorithm = (input.algorithm as string) || 'sha256';
    if (!text) {
      return { ok: false, error: 'text is required', elapsedMs: Date.now() - start };
    }

    const crypto = require('crypto');
    const hash = crypto.createHash(algorithm).update(text).digest('hex');

    return { ok: true, data: { algorithm, hash }, elapsedMs: Date.now() - start };
  } catch (error) {
    return { ok: false, error: `Hash failed: ${error instanceof Error ? error.message : 'unknown'}`, elapsedMs: Date.now() - start };
  }
}

/**
 * UUID tool - generate UUIDs
 * Input: { count?: number }
 */
export async function uuidTool(
  input: ToolInput,
  context: ToolContext
): Promise<ToolResult> {
  const start = Date.now();
  try {
    const count = Math.min((input.count as number) || 1, 10);
    const crypto = require('crypto');
    const uuids = Array.from({ length: count }, () => crypto.randomUUID());

    return { ok: true, data: { uuids, count }, elapsedMs: Date.now() - start };
  } catch (error) {
    return { ok: false, error: `UUID failed: ${error instanceof Error ? error.message : 'unknown'}`, elapsedMs: Date.now() - start };
  }
}
