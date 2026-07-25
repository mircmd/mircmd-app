import { getContextMenu } from "./context_menu.svelte";
import type { ContextMenuParams } from "./context_menu_types";
import type { ProgramNodeIdentity, ProgramPluginContext } from "./program_plugin_api";
import { adoptPluginSurface, type PluginSurfaceHandle } from "./plugin_surface";

export type { ProgramPluginContext };

const contextMenu = getContextMenu();

export type CreateProgramPluginContextOptions = {
  signal?: AbortSignal;
  node?: ProgramNodeIdentity;
};

export type ProgramPluginContextHandle = ProgramPluginContext & {
  /** Dispose the underlying plugin surface (clears Shadow DOM). */
  disposeSurface(): void;
};

/**
 * Builds a program context on top of a PluginSurface adopted from the window host.
 */
export function createProgramPluginContext(
  host: HTMLElement,
  options: CreateProgramPluginContextOptions = {},
): ProgramPluginContextHandle {
  const surface: PluginSurfaceHandle = adoptPluginSurface(host);

  const signal = options.signal ?? new AbortController().signal;
  const node: ProgramNodeIdentity = options.node ?? {
    id: "",
    name: "",
    type: "",
  };

  return {
    host: surface.host,
    root: surface.root,
    signal,
    node,
    addStyles: (cssText) => surface.addStyles(cssText),
    contextMenu: {
      open: (params: ContextMenuParams) => contextMenu.open(params),
      close: () => contextMenu.close(),
    },
    disposeSurface: () => surface.dispose(),
  };
}
