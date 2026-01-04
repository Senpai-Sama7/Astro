import axios, { AxiosError } from 'axios';
import { ToolInput, ToolResult, ToolContext } from '../orchestrator';

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
