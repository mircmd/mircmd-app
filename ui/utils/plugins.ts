// Utility for loading browser-side WASM Component Model plugins
// Uses jco-transpiled modules with instantiation mode

import { getPlugins, log } from "../core/commands";
import type { PluginMetadata } from "../core/types";
import type { ProgramPluginContext } from "./program_plugin_context";

export interface ProgramPlugin {
  run: (ctx: ProgramPluginContext, data: Uint8Array) => string;
  supportedTypes: () => string[];
  metadata: () => PluginMetadata;
}

const PLUGIN_BASE_URL = 'plugin://localhost';

// Minimal WASI preview2 shim implementations
function createWasiShims() {
  return {
    'wasi:cli/environment': {
      getEnvironment: () => [],
    },
    'wasi:cli/exit': {
      exit: (status: { tag: string; val?: number }) => {
        if (status.tag === 'err') {
          throw new Error(`WASI exit with code: ${status.val}`);
        }
      },
    },
    'wasi:cli/stderr': {
      getStderr: () => ({
        write: () => ({ tag: 'ok', val: 0n }),
        blockingFlush: () => ({ tag: 'ok' }),
      }),
    },
    'wasi:io/error': {
      Error: class WasiError {
        toDebugString() {
          return 'WASI Error';
        }
      },
    },
    'wasi:io/streams': {
      OutputStream: class OutputStream {
        write() {
          return { tag: 'ok', val: 0n };
        }
        blockingFlush() {
          return { tag: 'ok' };
        }
      },
    },
  };
}

class PluginManager {
  icons = new Map<string, string>();
  programs = new Map<string, ProgramPlugin[]>();

  constructor() { }

  private async loadPlugin(pluginPath: string): Promise<any> {
    const moduleUrl = `${PLUGIN_BASE_URL}/${pluginPath}/plugin.js`;
    const module = await import(moduleUrl);
    if (typeof module.instantiate !== 'function') {
      throw new Error(`Plugin ${pluginPath} does not export instantiate function`);
    }
    return module;
  }

  private async loadIconsPlugin(pluginPath: string) {
    try {
      const pluginInstance = (await this.loadPlugin(pluginPath)).instantiate();
      Object.entries(pluginInstance).forEach(([key, value]) => {
        this.icons.set(key, `${PLUGIN_BASE_URL}/${pluginPath}/${value as string}`);
      });
    } catch (error) {
      log.error(`Failed to load icons plugin ${pluginPath}: ${error}`);
    }
  }

  private async loadProgramPlugin(pluginPath: string, metadata: PluginMetadata) {
    const getCoreModule = async (name: string): Promise<WebAssembly.Module> => {
      const url = `${PLUGIN_BASE_URL}/${pluginPath}/${name}`;
      const response = await fetch(url);
      const bytes = await response.arrayBuffer();
      return WebAssembly.compile(bytes);
    };

    try {
      const pluginModule = await this.loadPlugin(pluginPath);
      const pluginInstance = await pluginModule.instantiate(
        getCoreModule,
        createWasiShims()
      );
      const programPlugin: ProgramPlugin = {
        run: pluginInstance.run,
        supportedTypes: pluginInstance.supportedTypes,
        metadata: () => metadata,
      };
      for (const t of pluginInstance.supportedTypes()) {
        const existing = this.programs.get(t);
        if (existing) {
          existing.push(programPlugin);
        } else {
          this.programs.set(t, [programPlugin]);
        }
      }
    } catch (error) {
      log.error(`Failed to load program plugin ${pluginPath}: ${error}`);
    }
  }

  async refresh() {
    try {
      const plugins = await getPlugins();

      this.icons.clear();
      this.programs.clear();
      for (const plugin of plugins) {
        if (plugin.manifest.target === "Ui" && plugin.manifest.type === "Icons") {
          await this.loadIconsPlugin(plugin.path);
        } else if (plugin.manifest.target === "Ui" && plugin.manifest.type === "Program") {
          await this.loadProgramPlugin(plugin.path, plugin.manifest.metadata);
        }
      }
    } catch (error) {
      log.error(`Failed to get plugins: ${error}`);
    }
  }
}

export const pluginManager = new PluginManager();
