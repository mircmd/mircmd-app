import { getPlugins, log } from "./commands";
import type { PluginMetadata } from "./types";
import { PluginProtocol } from "./types";
import {
  wrapProgramPlugin,
  type ProgramPluginDescriptor,
} from "./program_plugin_runtime";

const PLUGIN_BASE_URL = "plugin://localhost";

class PluginManager {
  icons = new Map<string, string>();
  programs = new Map<string, ProgramPluginDescriptor[]>();

  constructor() {}

  private async loadPlugin(pluginPath: string): Promise<any> {
    const moduleUrl = `${PLUGIN_BASE_URL}/${pluginPath}/plugin.js`;
    const module = await import(moduleUrl);
    if (typeof module.instantiate !== "function") {
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

  private async loadProgramPlugin(
    pluginPath: string,
    metadata: PluginMetadata,
    protocol: PluginProtocol,
  ) {
    try {
      const pluginModule = await this.loadPlugin(pluginPath);
      const pluginInstance = await pluginModule.instantiate();
      const descriptor = wrapProgramPlugin(pluginInstance, metadata, pluginPath, protocol);

      for (const t of descriptor.supportedTypes) {
        const existing = this.programs.get(t);
        if (existing) {
          existing.push(descriptor);
        } else {
          this.programs.set(t, [descriptor]);
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
        if (plugin.manifest.target === "ui" && plugin.manifest.type === "icons") {
          await this.loadIconsPlugin(plugin.path);
        } else if (plugin.manifest.target === "ui" && plugin.manifest.type === "program") {
          await this.loadProgramPlugin(
            plugin.path,
            plugin.manifest.metadata,
            plugin.manifest.protocol ?? PluginProtocol.V1,
          );
        }
      }
    } catch (error) {
      log.error(`Failed to get plugins: ${error}`);
    }
  }
}

export const pluginManager = new PluginManager();
