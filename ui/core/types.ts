export interface Window {
  pos: [number, number];
  size: [number, number];
}

export interface AppConfig {
  language: 'system' | 'english' | 'russian';
  window: Window;
}

export interface LogMessage {
  message: string;
  level: "debug" | "info" | "warning" | "error";
}

export interface ProjectNode {
  id: string;
  name: string;
  type: string;
  children: ProjectNode[];
}

export enum PluginTarget {
  Core = 'Core',
  Ui = 'Ui',
}

export enum PluginType {
  Icons = 'Icons',
  FileImporter = 'FileImporter',
  Program = 'Program',
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

export interface PluginInfo {
  path: string;
  manifest: PluginManifest;
}
