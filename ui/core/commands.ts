import type { SaveDialogFilter, SaveDialogOptions } from '@mircmd/extensions-api';
import { invoke } from '@tauri-apps/api/core';

export const isDesktop = '__TAURI_INTERNALS__' in window;

import { type AppState, DockPosition, Language } from './app_state';
import type { LogMessage, PluginInfo, ProjectNode } from './types';

export type { SaveDialogFilter, SaveDialogOptions };


const defaultAppState: AppState = {
  language: Language.System,
  window: {
    pos: [0, 0],
    size: [1024, 768],
  },
  workspace: {
    docks: {
      left: {
        visible: true,
        size: 200,
      },
      right: {
        visible: true,
        size: 350,
      },
      bottom: {
        visible: true,
        size: 150,
      },
    },
    panels: [
      {
        id: 'builtin:explorer',
        dock_position: DockPosition.Left,
        visible: true,
      },
      {
        id: 'builtin:console-output',
        dock_position: DockPosition.Bottom,
        visible: true,
      }
    ],
  },
};

const defaultRootNode: ProjectNode = {
  id: '00000000-0000-0000-0000-000000000000',
  name: 'Root',
  type: 'root',
  children: [],
};

export const log = {
  info: (message: string) =>
    isDesktop ? invoke('log', { level: 'info', message }) : console.info(message),
  warn: (message: string) =>
    isDesktop ? invoke('log', { level: 'warn', message }) : console.warn(message),
  error: (message: string) =>
    isDesktop ? invoke('log', { level: 'error', message }) : console.error(message),
  debug: (message: string) =>
    isDesktop ? invoke('log', { level: 'debug', message }) : console.debug(message),
  trace: (message: string) =>
    isDesktop ? invoke('log', { level: 'trace', message }) : console.trace(message),
};

export async function getAppState(): Promise<AppState> {
  if (!isDesktop) return defaultAppState;
  try {
    return await invoke<AppState>('get_app_state');
  } catch (e) {
    log.error(`Failed to get app config: ${e}`);
    return defaultAppState;
  }
}

export async function getStartupMessages(): Promise<LogMessage[]> {
  if (!isDesktop) return [];
  try {
    return await invoke<LogMessage[]>('get_startup_messages');
  } catch (e) {
    log.error(`Failed to get startup messages: ${e}`);
    return [];
  }
}

export async function getProjectRootNode(): Promise<ProjectNode> {
  if (!isDesktop) return defaultRootNode;
  try {
    return await invoke<ProjectNode>('get_project_root_node');
  } catch (e) {
    log.error(`Failed to get project root node: ${e}`);
    return defaultRootNode;
  }
}

export async function getProjectNodeById(node_id: string): Promise<ProjectNode | null> {
  if (!isDesktop) return null;
  try {
    return await invoke<ProjectNode | null>('get_project_node_by_id', { nodeId: node_id });
  } catch (e) {
    log.error(`Failed to get node by id: ${e}`);
    return null;
  }
}

export async function getProjectNodeDataById(id: string): Promise<Uint8Array> {
  if (!isDesktop) return new Uint8Array();
  try {
    const data = await invoke<number[]>('get_project_node_data_by_id', { id: id });
    return new Uint8Array(data);
  } catch (e) {
    log.error(`Failed to get node data: ${e}`);
    return new Uint8Array();
  }
}

export async function importFiles(node_id: string | null): Promise<ProjectNode[]> {
  if (!isDesktop) return [];
  try {
    return await invoke<ProjectNode[]>('import_files', { nodeId: node_id ?? null });
  } catch (e) {
    log.error(`Failed to import files: ${e}`);
    return [];
  }
}

export async function getPlugins(): Promise<PluginInfo[]> {
  if (!isDesktop) return [];
  try {
    return await invoke<PluginInfo[]>('get_plugins');
  } catch (e) {
    log.error(`Failed to get plugins: ${e}`);
    return [];
  }
}

export async function saveFileDialog(
  options: SaveDialogOptions = {},
): Promise<string | null> {
  if (!isDesktop) return null;
  try {
    return await invoke<string | null>('save_file_dialog', {
      defaultPath: options.defaultPath ?? null,
      filters: options.filters ?? null,
    });
  } catch (e) {
    log.error(`Failed to open save dialog: ${e}`);
    return null;
  }
}

export async function getCwd(): Promise<string> {
  if (!isDesktop) return '';
  try {
    return await invoke<string>('get_cwd');
  } catch (e) {
    log.error(`Failed to get current working directory: ${e}`);
    return '';
  }
}

export async function writeFile(path: string, data: Uint8Array): Promise<void> {
  if (!isDesktop) {
    throw new Error('File writing is only available in the desktop app');
  }
  await invoke('write_file', { path, data: Array.from(data) });
}

export function appendConsoleLine(level: 'info' | 'error', message: string): void {
  if (!isDesktop) {
    if (level === 'error') console.error(message);
    else console.info(message);
    return;
  }
  void invoke('append_console_line', { level, message });
}
