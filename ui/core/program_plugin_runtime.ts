/**
 * Runtime boundary for dynamically loaded program plugin modules.
 */

import { PluginProtocol, type PluginMetadata } from "./types";
import type {
  ControlPanelContribution,
  ProgramPlugin,
  ProgramPluginContext,
  ProgramSession,
} from "./program_plugin_api";

export type ProgramPluginDescriptor = {
  key: string;
  path: string;
  protocol: PluginProtocol;
  metadata: PluginMetadata;
  supportedTypes: string[];
  plugin: ProgramPlugin;
};

export function canonicalPluginKey(metadata: PluginMetadata): string {
  return `${metadata.publisher}:${metadata.id}`;
}

export function assertProgramSession(value: unknown, pluginKey: string): ProgramSession {
  if (value == null) {
    throw new Error(
      `Plugin ${pluginKey} run() returned void/null; protocol v1 requires a ProgramSession`,
    );
  }

  if (typeof value !== "object") {
    throw new Error(`Plugin ${pluginKey} returned a non-object session`);
  }

  const session = value as ProgramSession;
  if (typeof session.execute !== "function") {
    throw new Error(`Plugin ${pluginKey} session is missing execute()`);
  }
  if (typeof session.dispose !== "function") {
    throw new Error(`Plugin ${pluginKey} session is missing dispose()`);
  }

  if (session.controlPanel !== undefined) {
    assertControlPanelContribution(session.controlPanel, pluginKey);
  }

  return session;
}

function assertControlPanelContribution(
  contribution: ControlPanelContribution,
  pluginKey: string,
): void {
  if (!contribution || typeof contribution !== "object") {
    throw new Error(`Plugin ${pluginKey} controlPanel must be an object`);
  }
  if (!Array.isArray(contribution.blocks)) {
    throw new Error(`Plugin ${pluginKey} controlPanel.blocks must be an array`);
  }
  for (const [index, block] of contribution.blocks.entries()) {
    if (!block || typeof block !== "object") {
      throw new Error(`Plugin ${pluginKey} controlPanel.blocks[${index}] is invalid`);
    }
    if (typeof block.id !== "string" || block.id.length === 0) {
      throw new Error(`Plugin ${pluginKey} controlPanel.blocks[${index}] needs a non-empty id`);
    }
    if (typeof block.title !== "string") {
      throw new Error(`Plugin ${pluginKey} controlPanel.blocks[${index}] needs a title`);
    }
    if (typeof block.mount !== "function") {
      throw new Error(`Plugin ${pluginKey} controlPanel.blocks[${index}] needs mount()`);
    }
  }
}

export function wrapProgramPlugin(
  raw: unknown,
  metadata: PluginMetadata,
  path: string,
  protocol: PluginProtocol = PluginProtocol.V1,
): ProgramPluginDescriptor {
  if (protocol !== PluginProtocol.V1) {
    throw new Error(`Plugin ${path} uses unsupported protocol ${protocol}`);
  }
  if (!raw || typeof raw !== "object") {
    throw new Error(`Plugin ${path} instantiate() did not return an object`);
  }

  const instance = raw as Record<string, unknown>;
  if (typeof instance.run !== "function") {
    throw new Error(`Plugin ${path} does not export run()`);
  }
  if (typeof instance.supportedTypes !== "function") {
    throw new Error(`Plugin ${path} does not export supportedTypes()`);
  }

  const supportedTypes = (instance.supportedTypes as () => string[]).call(instance);
  if (!Array.isArray(supportedTypes)) {
    throw new Error(`Plugin ${path} supportedTypes() must return an array`);
  }

  const plugin: ProgramPlugin = {
    run: (instance.run as ProgramPlugin["run"]).bind(instance),
    supportedTypes: () => supportedTypes,
    metadata: () => metadata,
  };

  return {
    key: canonicalPluginKey(metadata),
    path,
    protocol,
    metadata,
    supportedTypes,
    plugin,
  };
}

export async function runProgramPlugin(
  descriptor: ProgramPluginDescriptor,
  context: ProgramPluginContext,
  nodeType: string,
  nodeData: Uint8Array,
): Promise<ProgramSession> {
  const result = await descriptor.plugin.run(context, nodeType, nodeData);
  return assertProgramSession(result, descriptor.key);
}
