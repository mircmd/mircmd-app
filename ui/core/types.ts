import type { PluginMetadata } from "@mircmd/extensions-api";

export type { PluginMetadata };

export interface LogMessage {
  message: string;
  level: 'debug' | 'info' | 'warning' | 'error';
}

export interface ProjectNode {
  id: string;
  name: string;
  type: string;
  children: ProjectNode[];
}

export enum PluginTarget {
  Core = 'core',
  Ui = 'ui',
}

export enum PluginType {
  Icons = 'icons',
  FileImporter = 'file_importer',
  Program = 'program',
}

export enum PluginProtocol {
  V1 = 'v1',
}

export interface PluginManifest {
  target: PluginTarget;
  type: PluginType;
  protocol: PluginProtocol;
  metadata: PluginMetadata;
}

export interface PluginInfo {
  path: string;
  manifest: PluginManifest;
}
