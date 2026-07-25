/**
 * Reactive workspace preferences for host panels and layout.
 *
 * Panel visibility is a shared state/API stub until App/Workspace fully
 * connect `visible` to LayoutItemHandle. Native View menu is out of scope.
 * `expandedBlocks` is runtime-only for the current app run — never loaded
 * from or written to config.
 */

import { getAppState, log } from "./commands";
import type { DockArea } from "../lib/Workspace.svelte";

export type { DockArea };

export type WorkspaceState = {
  panelVisibility: Record<string, boolean>;
  dockSizes: Record<DockArea, number>;
  expandedBlocks: Record<string, boolean>;
};

const DEFAULT_PANEL_VISIBILITY: Record<string, boolean> = {
  "builtin:explorer": true,
  "builtin:console-output": true,
};

const DEFAULT_DOCK_SIZES: Record<DockArea, number> = {
  left: 200,
  right: 350,
  bottom: 150,
};

const DOCK_SIZE_MIN = 150;
const DOCK_SIZE_MAX = 800;

export function programControlPanelId(pluginKey: string): string {
  return `program-control-panel:${pluginKey}`;
}

function blockKey(pluginKey: string, blockId: string): string {
  return `${pluginKey}/${blockId}`;
}

function clampDockSize(size: number): number {
  return Math.max(DOCK_SIZE_MIN, Math.min(DOCK_SIZE_MAX, Math.round(size)));
}

export class WorkspacePreferences {
  /** `visible` per panelId — no availability / effectiveVisible triad. */
  panelVisibility = $state<Record<string, boolean>>({
    ...DEFAULT_PANEL_VISIBILITY,
  });
  dockSizes = $state<Record<DockArea, number>>({ ...DEFAULT_DOCK_SIZES });
  /** In-memory only; not persisted across reloads. */
  expandedBlocks = $state<Record<string, boolean>>({});

  async load(): Promise<void> {
    try {
      const config = await getAppState();
      const workspace = config.workspace;
      if (!workspace) return;

      const fromConfig: Record<string, boolean> = {};
      for (const panel of workspace.panels) {
        fromConfig[panel.id] = panel.visible;
      }

      this.panelVisibility = {
        ...DEFAULT_PANEL_VISIBILITY,
        ...fromConfig,
      };
      this.dockSizes = {
        left: workspace.docks.left.size,
        right: workspace.docks.right.size,
        bottom: workspace.docks.bottom.size,
      };
    } catch (error) {
      log.error(`Failed to load workspace preferences: ${error}`);
    }
  }

  isPanelVisible(panelId: string): boolean {
    return this.panelVisibility[panelId] ?? true;
  }

  setPanelVisible(panelId: string, value: boolean): void {
    this.panelVisibility = {
      ...this.panelVisibility,
      [panelId]: value,
    };
  }

  togglePanelVisible(panelId: string): void {
    this.setPanelVisible(panelId, !this.isPanelVisible(panelId));
  }

  getDockSize(area: DockArea): number {
    return this.dockSizes[area];
  }

  setDockSize(area: DockArea, size: number): void {
    this.dockSizes = {
      ...this.dockSizes,
      [area]: clampDockSize(size),
    };
  }

  setBlockExpanded(pluginKey: string, blockId: string, expanded: boolean): void {
    const key = blockKey(pluginKey, blockId);
    this.expandedBlocks = { ...this.expandedBlocks, [key]: expanded };
  }

  isBlockExpanded(pluginKey: string, blockId: string, defaultExpanded: boolean): boolean {
    const key = blockKey(pluginKey, blockId);
    if (Object.prototype.hasOwnProperty.call(this.expandedBlocks, key)) {
      return this.expandedBlocks[key]!;
    }
    return defaultExpanded;
  }
}
