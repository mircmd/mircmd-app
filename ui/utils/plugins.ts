import { getPlugins, log } from "../core/commands";
import type { PluginMetadata } from "../core/types";
import type { ProgramPluginContext } from "./program_plugin_context";

export interface ProgramPlugin {
  run: (ctx: ProgramPluginContext, data: Uint8Array) => string;
  supportedTypes: () => string[];
  metadata: () => PluginMetadata;
}

const PLUGIN_BASE_URL = 'plugin://localhost';

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
    try {
      const pluginModule = await this.loadPlugin(pluginPath);
      const pluginInstance = await pluginModule.instantiate();
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
