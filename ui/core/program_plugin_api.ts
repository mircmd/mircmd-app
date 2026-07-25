/**
 * Experimental program plugin contract (protocol v1).
 * Canonical description lives in mircmd-app until API stabilizes.
 */

import type { ContextMenuParams } from "./context_menu_types";
import type { PluginMetadata } from "./types";

export type MaybePromise<T> = T | Promise<T>;
export type Cleanup = () => MaybePromise<void>;

export interface PluginSurface {
  host: HTMLElement;
  root: ShadowRoot;
  addStyles(cssText: string): void;
}

export interface ProgramNodeIdentity {
  readonly id: string;
  readonly name: string;
  readonly type: string;
}

export interface ProgramPluginContext extends PluginSurface {
  signal: AbortSignal;
  node: ProgramNodeIdentity;
  contextMenu: {
    open(params: ContextMenuParams): void;
    close(): void;
  };
}

export interface ProgramCommand {
  type: string;
  payload?: unknown;
}

export interface ProgramCommandContext {
  instanceIndex: number;
  instanceCount: number;
}

export interface ControlPanelBlockMountContext {
  signal: AbortSignal;
  dispatch(command: ProgramCommand): Promise<void>;
}

export interface ControlPanelBlock {
  id: string;
  title: string;
  initiallyExpanded?: boolean;
  mount(
    surface: PluginSurface,
    context: ControlPanelBlockMountContext,
  ): MaybePromise<void | Cleanup>;
}

export interface ControlPanelContribution {
  title?: string;
  allowApplyToAll?: boolean;
  broadcastKey?: string;
  blocks: readonly ControlPanelBlock[];
}

export interface ProgramSession {
  controlPanel?: ControlPanelContribution;
  execute(command: ProgramCommand, context: ProgramCommandContext): MaybePromise<void>;
  /** Must be idempotent; called exactly once by the host. */
  dispose(): MaybePromise<void>;
}

export interface ProgramPlugin {
  supportedTypes(): string[];
  metadata(): PluginMetadata;
  /** Always returns a ProgramSession (sync or async). void is rejected by the host runtime. */
  run(
    context: ProgramPluginContext,
    nodeType: string,
    nodeData: Uint8Array,
  ): MaybePromise<ProgramSession>;
}
