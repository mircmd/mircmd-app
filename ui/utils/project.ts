import { invoke } from '@tauri-apps/api/core';
import log from './logging';
import { isDesktop } from '../app';

export async function getNodeData(node_id: string): Promise<Uint8Array> {
  if (!isDesktop) {
    return new Uint8Array();
  }
  try {
    const data = await invoke<number[]>('get_node_data', { nodeId: node_id });
    return new Uint8Array(data);
  } catch (e) {
    log.error(`Failed to get node data: ${e}`);
    return new Uint8Array();
  }
}

export async function importFiles(node_id: string | null): Promise<void> {
  if (!isDesktop) {
    return;
  }
  try {
    await invoke('import_files', { nodeId: node_id ?? null });
  } catch (e) {
    log.error(`Failed to import files: ${e}`);
  }
}
