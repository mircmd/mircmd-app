import { invoke } from '@tauri-apps/api/core';
import { isDesktop } from '../app';

export enum PluginType {
  Icons = 'Icons',
  FileImporter = 'FileImporter',
  Program = 'Program',
}

export enum PluginTarget {
  Core = 'Core',
  Ui = 'Ui',
}

export interface PluginMetadata {
  id: string;
  name: string;
  version: string;
  publisher: string;
  description: string;
}

export interface PluginManifest {
  target: PluginTarget;
  type: PluginType;
  metadata: PluginMetadata;
}

export interface Plugin {
  manifest: PluginManifest;
}

export interface PluginInfo {
  path: string;
  manifest: PluginManifest;
}

export const getPlugins = async (): Promise<PluginInfo[]> => {
  if (!isDesktop) {
    return [];
  }
  return await invoke('get_plugins');
};
