import * as fs from 'fs';
import * as path from 'path';
import { ToolDefinition, ToolInput, ToolContext, ToolResult } from '../astro/orchestrator';
import { logger } from '../services/logger';

export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  tools: PluginToolDef[];
}

export interface PluginToolDef {
  name: string;
  description: string;
  schema?: Record<string, unknown>;
  handler: string; // function name in module
}

export interface LoadedPlugin {
  manifest: PluginManifest;
  tools: ToolDefinition[];
  path: string;
}

export class PluginLoader {
  private plugins: Map<string, LoadedPlugin> = new Map();
  private pluginDir: string;

  constructor(pluginDir?: string) {
    this.pluginDir = pluginDir || path.join(process.cwd(), 'plugins');
  }

  async loadPlugin(pluginPath: string): Promise<LoadedPlugin> {
    const manifestPath = path.join(pluginPath, 'manifest.json');
    if (!fs.existsSync(manifestPath)) {
      throw new Error(`No manifest.json found in ${pluginPath}`);
    }

    const manifest: PluginManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
    if (!manifest.name || !manifest.tools?.length) {
      throw new Error('Invalid manifest: name and tools required');
    }

    const modulePath = path.join(pluginPath, 'index.js');
    if (!fs.existsSync(modulePath)) {
      throw new Error(`No index.js found in ${pluginPath}`);
    }

    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pluginModule = require(modulePath);
    const tools: ToolDefinition[] = manifest.tools.map((t) => {
      const handler = pluginModule[t.handler];
      if (typeof handler !== 'function') {
        throw new Error(`Handler '${t.handler}' not found in plugin ${manifest.name}`);
      }
      return {
        name: `${manifest.name}:${t.name}`,
        description: t.description,
        schema: t.schema,
        handler: async (input: ToolInput, ctx: ToolContext): Promise<ToolResult> => {
          const start = Date.now();
          try {
            const data = await handler(input, ctx);
            return { ok: true, data, elapsedMs: Date.now() - start };
          } catch (e) {
            return { ok: false, error: String(e), elapsedMs: Date.now() - start };
          }
        },
      };
    });

    const loaded: LoadedPlugin = { manifest, tools, path: pluginPath };
    this.plugins.set(manifest.name, loaded);
    logger.info(`Loaded plugin: ${manifest.name} v${manifest.version} (${tools.length} tools)`);
    return loaded;
  }

  async loadAllPlugins(): Promise<LoadedPlugin[]> {
    if (!fs.existsSync(this.pluginDir)) {
      fs.mkdirSync(this.pluginDir, { recursive: true });
      return [];
    }

    const entries = fs.readdirSync(this.pluginDir, { withFileTypes: true });
    const loaded: LoadedPlugin[] = [];

    for (const entry of entries) {
      if (entry.isDirectory()) {
        try {
          const plugin = await this.loadPlugin(path.join(this.pluginDir, entry.name));
          loaded.push(plugin);
        } catch (e) {
          logger.error(`Failed to load plugin ${entry.name}: ${e}`);
        }
      }
    }
    return loaded;
  }

  unloadPlugin(name: string): boolean {
    return this.plugins.delete(name);
  }

  getPlugin(name: string): LoadedPlugin | undefined {
    return this.plugins.get(name);
  }

  listPlugins(): LoadedPlugin[] {
    return Array.from(this.plugins.values());
  }

  getAllTools(): ToolDefinition[] {
    return this.listPlugins().flatMap((p) => p.tools);
  }
}
