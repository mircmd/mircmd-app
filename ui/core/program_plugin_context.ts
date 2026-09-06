import type {
  ContextMenuParams,
  ProgramFs,
  ProgramLog,
  ProgramNodeIdentity,
  ProgramPluginContext,
} from "@mircmd/extensions-api";
import { appendConsoleLine, getCwd, saveFileDialog, writeFile } from "./commands";
import { getContextMenu } from "./context_menu.svelte";
import { adoptPluginSurface, type PluginSurfaceHandle } from "./plugin_surface";

export type { ProgramPluginContext };

const contextMenu = getContextMenu();

export function createProgramFs(): ProgramFs {
  return {
    getCwd,
    showSaveDialog: (options) => saveFileDialog(options),
    writeFile,
  };
}

function createProgramLog(): ProgramLog {
  return {
    info: (message) => appendConsoleLine("info", message),
    error: (message) => appendConsoleLine("error", message),
  };
}

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
    fs: createProgramFs(),
    log: createProgramLog(),
    addStyles: (cssText) => surface.addStyles(cssText),
    contextMenu: {
      open: (params: ContextMenuParams) => contextMenu.open(params),
      close: () => contextMenu.close(),
    },
    disposeSurface: () => surface.dispose(),
  };
}
