import axios, { AxiosError } from 'axios';
import { execSync, spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
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
    return WHITELISTED_DOMAINS.some(
      (domain) => parsed.hostname === domain || parsed.hostname?.endsWith(`.${domain}`)
    );
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
 * Only supports +, -, *, /, parentheses, and numbers
 */
function isSafeExpression(expr: string): boolean {
  // Only allow digits, operators, parentheses, and decimal points
  return /^[0-9+\-*/.()\s]+$/.test(expr);
}

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

    if (!isSafeExpression(expression)) {
      return {
        ok: false,
        error: 'Expression contains invalid characters. Only numbers, operators (+, -, *, /), parentheses, and decimal points are allowed.',
        elapsedMs: Date.now() - start,
      };
    }

    // Use Function constructor with strict input validation
    // This is safer than eval() because it doesn't have access to scope
    const result = new Function('return ' + expression)();

    if (typeof result !== 'number') {
      return {
        ok: false,
        error: 'Expression did not evaluate to a number',
        elapsedMs: Date.now() - start,
      };
    }

    if (!isFinite(result)) {
      return {
        ok: false,
        error: 'Expression resulted in infinity or NaN',
        elapsedMs: Date.now() - start,
      };
    }

    return {
      ok: true,
      data: {
        expression,
        result,
      },
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
    const maxResults = (input.maxResults as number) || 5;

    if (!query) {
      return { ok: false, error: 'query is required', elapsedMs: Date.now() - start };
    }

    // Use DuckDuckGo HTML endpoint (no API key needed)
    const response = await axios.get('https://html.duckduckgo.com/html/', {
      params: { q: query },
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ASTRO/1.0)' },
      timeout: 10000,
    });

    // Parse results from HTML (simplified)
    const results: { title: string; url: string; snippet: string }[] = [];
    const regex = /<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/gi;
    let match;
    while ((match = regex.exec(response.data)) !== null && results.length < maxResults) {
      results.push({ title: match[2], url: match[1], snippet: '' });
    }

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
  const resolved = path.resolve(WORKSPACE_DIR, filePath);
  return resolved.startsWith(path.resolve(WORKSPACE_DIR));
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
    const output = execSync('git status --porcelain', { cwd, encoding: 'utf-8', timeout: 5000 });
    const branch = execSync('git branch --show-current', { cwd, encoding: 'utf-8', timeout: 5000 }).trim();
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
    const cmd = file ? `git diff -- ${file}` : 'git diff';
    const output = execSync(cmd, { cwd, encoding: 'utf-8', timeout: 10000 });
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
    let command = input.command as string;

    // Auto-detect test command if not provided
    if (!command) {
      if (fs.existsSync(path.join(cwd, 'package.json'))) {
        command = 'npm test';
      } else if (fs.existsSync(path.join(cwd, 'pytest.ini')) || fs.existsSync(path.join(cwd, 'pyproject.toml'))) {
        command = 'pytest';
      } else {
        return { ok: false, error: 'Could not detect test framework', elapsedMs: Date.now() - start };
      }
    }

    const output = execSync(command, { cwd, encoding: 'utf-8', timeout: 120000 });
    return {
      ok: true,
      data: { command, output: output.slice(0, 10000) },
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
    let command: string;

    if (linter === 'eslint' || (!linter && fs.existsSync('package.json'))) {
      command = `npx eslint ${targetPath} --format json`;
    } else if (linter === 'pylint' || (!linter && fs.existsSync('pyproject.toml'))) {
      command = `pylint ${targetPath} --output-format=json`;
    } else {
      return { ok: false, error: 'No linter detected or specified', elapsedMs: Date.now() - start };
    }

    const output = execSync(command, { encoding: 'utf-8', timeout: 60000 });
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
