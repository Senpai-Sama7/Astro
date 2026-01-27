export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMResponse {
  content: string;
  model: string;
  usage?: { prompt: number; completion: number; total: number };
}

export interface LLMProvider {
  name: string;
  chat(messages: LLMMessage[], options?: LLMOptions): Promise<LLMResponse>;
  stream?(messages: LLMMessage[], options?: LLMOptions): AsyncIterable<string>;
}

export interface LLMOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

const DEFAULT_TIMEOUT_MS = Number(process.env.LLM_TIMEOUT_MS || 15000);

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

interface OpenAIResponse {
  choices: { message: { content: string }; delta?: { content?: string } }[];
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  error?: { message: string };
}

interface AnthropicResponse {
  content: { text: string }[];
  usage?: { input_tokens: number; output_tokens: number };
  error?: { message: string };
}

interface OllamaResponse {
  message: { content: string };
  error?: string;
}

// OpenAI Provider
export class OpenAIProvider implements LLMProvider {
  name = 'openai';
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey?: string, baseUrl?: string) {
    this.apiKey = apiKey || process.env.OPENAI_API_KEY || '';
    this.baseUrl = baseUrl || 'https://api.openai.com/v1';
  }

  async chat(messages: LLMMessage[], options?: LLMOptions): Promise<LLMResponse> {
    const model = options?.model || 'gpt-4o-mini';
    const res = await fetchWithTimeout(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({
        model,
        messages,
        temperature: options?.temperature ?? 0.7,
        max_tokens: options?.maxTokens,
      }),
    });
    const data = (await res.json()) as OpenAIResponse;
    if (!res.ok) throw new Error(data.error?.message || 'OpenAI API error');
    return {
      content: data.choices[0].message.content,
      model,
      usage: data.usage ? { prompt: data.usage.prompt_tokens, completion: data.usage.completion_tokens, total: data.usage.total_tokens } : undefined,
    };
  }

  async *stream(messages: LLMMessage[], options?: LLMOptions): AsyncIterable<string> {
    const model = options?.model || 'gpt-4o-mini';
    const res = await fetchWithTimeout(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${this.apiKey}` },
      body: JSON.stringify({ model, messages, temperature: options?.temperature ?? 0.7, max_tokens: options?.maxTokens, stream: true }),
    });
    if (!res.ok || !res.body) throw new Error('OpenAI stream error');
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ') && !line.includes('[DONE]')) {
          try {
            const json = JSON.parse(line.slice(6)) as OpenAIResponse;
            const content = json.choices?.[0]?.delta?.content;
            if (content) yield content;
          } catch { /* skip */ }
        }
      }
    }
  }
}

// Anthropic Provider
export class AnthropicProvider implements LLMProvider {
  name = 'anthropic';
  private apiKey: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.ANTHROPIC_API_KEY || '';
  }

  async chat(messages: LLMMessage[], options?: LLMOptions): Promise<LLMResponse> {
    const model = options?.model || 'claude-3-5-sonnet-20241022';
    const systemMsg = messages.find((m) => m.role === 'system')?.content;
    const chatMsgs = messages.filter((m) => m.role !== 'system').map((m) => ({ role: m.role, content: m.content }));
    const res = await fetchWithTimeout('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': this.apiKey, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify({ model, max_tokens: options?.maxTokens || 4096, system: systemMsg, messages: chatMsgs }),
    });
    const data = (await res.json()) as AnthropicResponse;
    if (!res.ok) throw new Error(data.error?.message || 'Anthropic API error');
    return {
      content: data.content[0].text,
      model,
      usage: data.usage ? { prompt: data.usage.input_tokens, completion: data.usage.output_tokens, total: data.usage.input_tokens + data.usage.output_tokens } : undefined,
    };
  }
}

// Local/Ollama Provider
export class OllamaProvider implements LLMProvider {
  name = 'ollama';
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.OLLAMA_URL || 'http://localhost:11434';
  }

  async chat(messages: LLMMessage[], options?: LLMOptions): Promise<LLMResponse> {
    const model = options?.model || 'llama3.2';
    const res = await fetchWithTimeout(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages, stream: false }),
    });
    const data = (await res.json()) as OllamaResponse;
    if (!res.ok) throw new Error(data.error || 'Ollama API error');
    return { content: data.message.content, model };
  }
}

// Multi-model Manager
export class LLMManager {
  private providers: Map<string, LLMProvider> = new Map();
  private defaultProvider: string = 'openai';

  constructor() {
    // Auto-register based on available API keys
    if (process.env.OPENAI_API_KEY) this.register(new OpenAIProvider());
    if (process.env.ANTHROPIC_API_KEY) this.register(new AnthropicProvider());
    this.register(new OllamaProvider()); // Always available locally
  }

  register(provider: LLMProvider): void {
    this.providers.set(provider.name, provider);
  }

  setDefault(name: string): void {
    if (!this.providers.has(name)) throw new Error(`Provider '${name}' not registered`);
    this.defaultProvider = name;
  }

  get(name?: string): LLMProvider {
    const provider = this.providers.get(name || this.defaultProvider);
    if (!provider) throw new Error(`Provider '${name || this.defaultProvider}' not found`);
    return provider;
  }

  list(): string[] {
    return Array.from(this.providers.keys());
  }

  async chat(messages: LLMMessage[], options?: LLMOptions & { provider?: string }): Promise<LLMResponse> {
    return this.get(options?.provider).chat(messages, options);
  }
}

export const llmManager = new LLMManager();
