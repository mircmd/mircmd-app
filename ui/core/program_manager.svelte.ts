/**
 * App-owned lifecycle manager for program windows and sessions.
 * Registry must not be exported to external plugins.
 *
 * Control panels bind to focusedSessionByPluginKey (last activated ready
 * session per plugin key), not the globally active workspace window.
 */

import type { ProgramCommand, ProgramSession } from "@mircmd/extensions-api";
import type WindowManager from "../lib/WindowManager.svelte";
import type { WindowHandle } from "../lib/WindowManager.svelte";
import { getProjectNodeDataById, log } from "./commands";
import { createProgramPluginContext } from "./program_plugin_context";
import {
  runProgramPlugin,
  type ProgramPluginDescriptor,
} from "./program_plugin_runtime";

export type ProgramLifecycleState =
  | "loading"
  | "starting"
  | "ready"
  | "closing"
  | "failed";

export type ProgramRecord = {
  windowId: string;
  nodeId: string;
  nodeName: string;
  nodeType: string;
  pluginKey: string;
  descriptor: ProgramPluginDescriptor;
  lifecycleState: ProgramLifecycleState;
  abortController: AbortController;
  session: ProgramSession | null;
  disposed: boolean;
  windowHandle: WindowHandle;
};

export type OpenProgramRequest = {
  nodeId: string;
  nodeName: string;
  nodeType: string;
  icon: string;
  descriptor: ProgramPluginDescriptor;
};

export type DispatchRequest = {
  sourceWindowId: string;
  command: ProgramCommand;
  applyToAll: boolean;
};

export class ProgramManager {
  /** Last activated ready session per canonical plugin key. */
  focusedSessionByPluginKey = $state<Record<string, ProgramRecord>>({});

  /**
   * Plugin keys that currently need a control panel host widget
   * (≥1 ready session with controlPanel contribution).
   */
  openPanelPluginKeys = $state<string[]>([]);

  private readonly records = new Map<string, ProgramRecord>();
  private readonly unsubscribers: Array<() => void> = [];

  constructor(private readonly windowManager: WindowManager) {
    this.unsubscribers.push(
      this.windowManager.onActiveWindowChange(({ windowId }) => {
        if (!windowId) return;
        const record = this.records.get(windowId);
        if (!record || record.lifecycleState !== "ready" || !record.session) {
          return;
        }
        this.setFocusedRecord(record);
      }),
    );

    this.unsubscribers.push(
      this.windowManager.onWindowCloseRequest(async (windowId) => {
        await this.handleWindowClosing(windowId);
      }),
    );
  }

  async openProgram(request: OpenProgramRequest): Promise<void> {
    const existing = this.findByNodeAndPlugin(request.nodeId, request.descriptor.key);
    if (existing) {
      existing.windowHandle.focus();
      if (existing.lifecycleState === "ready" && existing.session) {
        this.setFocusedRecord(existing);
      }
      return;
    }

    const abortController = new AbortController();
    let windowHandle: WindowHandle | null = null;

    try {
      const nodeData = await getProjectNodeDataById(request.nodeId);
      if (abortController.signal.aborted) return;

      const handle = this.windowManager.addWindow({
        icon: request.icon,
        title: request.nodeName,
        pos: [0, 0],
        onmount: (host) => {
          void this.startSession(handle.id, host, request, nodeData);
        },
      });
      windowHandle = handle;

      const record: ProgramRecord = {
        windowId: handle.id,
        nodeId: request.nodeId,
        nodeName: request.nodeName,
        nodeType: request.nodeType,
        pluginKey: request.descriptor.key,
        descriptor: request.descriptor,
        lifecycleState: "loading",
        abortController,
        session: null,
        disposed: false,
        windowHandle: handle,
      };

      this.records.set(handle.id, record);
      log.debug(
        `ProgramManager: opened window ${handle.id} for ${request.descriptor.key}`,
      );
    } catch (error) {
      log.error(
        `ProgramManager: failed to open ${request.descriptor.key} for node ${request.nodeId}: ${error}`,
      );
      abortController.abort();
      windowHandle?.close();
      if (windowHandle) {
        this.records.delete(windowHandle.id);
      }
    }
  }

  getFocusedSession(pluginKey: string): ProgramSession | null {
    return this.focusedSessionByPluginKey[pluginKey]?.session ?? null;
  }

  getFocusedRecord(pluginKey: string): ProgramRecord | null {
    return this.focusedSessionByPluginKey[pluginKey] ?? null;
  }

  getRecord(windowId: string): ProgramRecord | null {
    return this.records.get(windowId) ?? null;
  }

  getReadyRecords(): ProgramRecord[] {
    return [...this.records.values()].filter(
      (record) => record.lifecycleState === "ready" && record.session,
    );
  }

  async dispatch(request: DispatchRequest): Promise<void> {
    const source = this.records.get(request.sourceWindowId);
    if (!source || source.lifecycleState !== "ready" || !source.session) {
      log.warn(
        `ProgramManager: dispatch ignored; source ${request.sourceWindowId} is not ready`,
      );
      return;
    }

    const focused = this.focusedSessionByPluginKey[source.pluginKey];
    if (!focused || focused.windowId !== source.windowId) {
      log.warn(
        `ProgramManager: dispatch ignored; source ${request.sourceWindowId} is not focused for ${source.pluginKey}`,
      );
      return;
    }

    const targets = request.applyToAll
      ? this.collectBroadcastTargets(source)
      : [source];

    const instanceCount = targets.length;
    for (let instanceIndex = 0; instanceIndex < targets.length; instanceIndex++) {
      const target = targets[instanceIndex];
      if (target.lifecycleState !== "ready" || !target.session) continue;

      try {
        await target.session.execute(request.command, {
          instanceIndex,
          instanceCount,
        });
      } catch (error) {
        log.error(
          `ProgramManager: execute failed for ${target.pluginKey} window ${target.windowId}: ${error}`,
        );
      }
    }
  }

  async closeWindow(windowId: string): Promise<void> {
    const record = this.records.get(windowId);
    if (!record) return;
    record.windowHandle.close();
  }

  async disposeAll(): Promise<void> {
    const handles = [...this.records.values()].map((record) => record.windowHandle);
    for (const handle of handles) {
      handle.close();
    }
    for (const unsubscribe of this.unsubscribers) {
      unsubscribe();
    }
    this.unsubscribers.length = 0;
  }

  private setFocusedRecord(record: ProgramRecord): void {
    this.focusedSessionByPluginKey = {
      ...this.focusedSessionByPluginKey,
      [record.pluginKey]: record,
    };
  }

  private clearFocusedRecord(pluginKey: string): void {
    if (!(pluginKey in this.focusedSessionByPluginKey)) return;
    const next = { ...this.focusedSessionByPluginKey };
    delete next[pluginKey];
    this.focusedSessionByPluginKey = next;
  }

  private refreshOpenPanelKeys(): void {
    const keys = new Set<string>();
    for (const record of this.records.values()) {
      if (record.lifecycleState === "ready" && record.session?.controlPanel) {
        keys.add(record.pluginKey);
      }
    }
    this.openPanelPluginKeys = [...keys].sort();
  }

  private rebindFocusedAfterClose(closed: ProgramRecord): void {
    const pluginKey = closed.pluginKey;
    const wasFocused =
      this.focusedSessionByPluginKey[pluginKey]?.windowId === closed.windowId;

    if (!wasFocused) {
      return;
    }

    const history = this.windowManager.getActivationHistory();
    for (const windowId of history) {
      if (windowId === closed.windowId) continue;
      const candidate = this.records.get(windowId);
      if (
        candidate &&
        candidate.pluginKey === pluginKey &&
        candidate.lifecycleState === "ready" &&
        candidate.session
      ) {
        this.setFocusedRecord(candidate);
        return;
      }
    }

    this.clearFocusedRecord(pluginKey);
  }

  private findByNodeAndPlugin(nodeId: string, pluginKey: string): ProgramRecord | null {
    for (const record of this.records.values()) {
      if (
        record.nodeId === nodeId &&
        record.pluginKey === pluginKey &&
        record.lifecycleState !== "closing" &&
        record.lifecycleState !== "failed"
      ) {
        return record;
      }
    }
    return null;
  }

  private collectBroadcastTargets(source: ProgramRecord): ProgramRecord[] {
    const sourceKey = source.session?.controlPanel?.broadcastKey;
    const history = this.windowManager.getActivationHistory();
    const byId = new Map(this.getReadyRecords().map((record) => [record.windowId, record]));

    const targets: ProgramRecord[] = [];
    for (const windowId of history) {
      const record = byId.get(windowId);
      if (!record) continue;
      if (record.pluginKey !== source.pluginKey) continue;

      const targetKey = record.session?.controlPanel?.broadcastKey;
      if (sourceKey !== targetKey) continue;

      targets.push(record);
    }
    return targets;
  }

  private async startSession(
    windowId: string,
    host: HTMLElement,
    request: OpenProgramRequest,
    nodeData: Uint8Array,
  ): Promise<void> {
    const record = this.records.get(windowId);
    if (!record) return;

    record.lifecycleState = "starting";

    try {
      if (!this.isRecordCurrent(windowId)) return;

      const context = createProgramPluginContext(host, {
        signal: record.abortController.signal,
        node: {
          id: request.nodeId,
          name: request.nodeName,
          type: request.nodeType,
        },
      });

      const session = await runProgramPlugin(
        request.descriptor,
        context,
        request.nodeType,
        nodeData,
      );

      if (!this.isRecordCurrent(windowId)) {
        await this.disposeSessionOnce({
          ...record,
          session,
          disposed: false,
        });
        return;
      }

      record.session = session;
      record.lifecycleState = "ready";

      // First ready window of this key, or currently globally active window,
      // becomes the focused session for the control panel of this plugin.
      const existingFocused = this.focusedSessionByPluginKey[record.pluginKey];
      if (
        !existingFocused ||
        this.windowManager.getActiveWindowId() === windowId
      ) {
        this.setFocusedRecord(record);
      }
      this.refreshOpenPanelKeys();

      log.debug(`ProgramManager: session ready for ${request.descriptor.key} (${windowId})`);
    } catch (error) {
      log.error(
        `ProgramManager: run failed for ${request.descriptor.key} (${windowId}): ${error}`,
      );

      const current = this.records.get(windowId);
      if (!current) return;

      current.lifecycleState = "failed";
      current.windowHandle.close();
    }
  }

  private isRecordCurrent(windowId: string): boolean {
    const record = this.records.get(windowId);
    if (!record) return false;
    if (record.abortController.signal.aborted) return false;
    if (record.lifecycleState === "closing" || record.lifecycleState === "failed") {
      return false;
    }
    return true;
  }

  private async handleWindowClosing(windowId: string): Promise<void> {
    const record = this.records.get(windowId);
    if (!record) return;

    record.lifecycleState = "closing";
    record.abortController.abort();

    try {
      await this.disposeSessionOnce(record);
    } finally {
      this.records.delete(windowId);
      this.rebindFocusedAfterClose(record);
      this.refreshOpenPanelKeys();
      log.debug(`ProgramManager: closed ${record.pluginKey} (${windowId})`);
    }
  }

  private async disposeSessionOnce(record: ProgramRecord): Promise<void> {
    if (record.disposed) return;

    record.disposed = true;
    if (!record.session) return;

    try {
      await record.session.dispose();
    } catch (error) {
      log.error(
        `ProgramManager: dispose failed for ${record.pluginKey} (${record.windowId}): ${error}`,
      );
    }
  }
}
