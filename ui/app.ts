import { invoke } from '@tauri-apps/api/core';
import log from './utils/logging';

export const isDesktop = '__TAURI_INTERNALS__' in window;

export interface Window {
  pos: [number, number];
  size: [number, number];
}

export interface Config {
  language: 'system' | 'english' | 'russian';
  window: Window;
}

export interface ProjectNode {
  id: string;
  name: string;
  kind: string;
  children: ProjectNode[];
}

const defaultRootNode: ProjectNode = {
  id: '00000000-0000-0000-0000-000000000000',
  name: 'Root',
  kind: 'root',
  children: [],
};

export async function getProjectRootNode(): Promise<ProjectNode> {
  if (!isDesktop) {
    return defaultRootNode;
  }
  try {
    return await invoke<ProjectNode>('get_project_root_node');
  } catch (e) {
    log.error(`Failed to get project root node: ${e}`);
    return defaultRootNode;
  }
}

const defaultConfig: Config = {
  language: 'system',
  window: {
    pos: [0, 0],
    size: [1024, 768],
  },
};

export async function getAppConfig(): Promise<Config> {
  if (!isDesktop) {
    return defaultConfig;
  }
  try {
    return await invoke<Config>('get_app_config');
  } catch (e) {
    log.error(`Failed to get app config: ${e}`);
    return defaultConfig;
  }
}

export async function getStartupMessages(): Promise<string[]> {
  if (!isDesktop) {
    return [];
  }
  try {
    return await invoke<string[]>('get_startup_messages');
  } catch (e) {
    log.error(`Failed to get startup messages: ${e}`);
    return [];
  }
}

