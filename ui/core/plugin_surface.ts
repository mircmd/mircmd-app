/**
 * Shared helper for program window and control-panel block surfaces.
 * Creates an isolated Shadow DOM mount point with stylesheet injection.
 */

import type { PluginSurface } from "./program_plugin_api";

export type PluginSurfaceHandle = PluginSurface & {
  dispose(): void;
};

type SurfaceState = {
  ownedHost: boolean;
  disposed: boolean;
};

const surfaceState = new WeakMap<PluginSurfaceHandle, SurfaceState>();

/**
 * Attach or reuse an open ShadowRoot on `host`.
 * Never calls attachShadow twice on the same element.
 */
function ensureOpenShadow(host: HTMLElement): ShadowRoot {
  if (host.shadowRoot) {
    host.shadowRoot.innerHTML = "";
    return host.shadowRoot;
  }
  return host.attachShadow({ mode: "open" });
}

function buildSurface(host: HTMLElement, ownedHost: boolean): PluginSurfaceHandle {
  const root = ensureOpenShadow(host);

  const surface: PluginSurfaceHandle = {
    host,
    root,
    addStyles(cssText: string) {
      const state = surfaceState.get(surface);
      if (!state || state.disposed) return;

      const style = document.createElement("style");
      style.textContent = cssText;
      root.appendChild(style);
    },
    dispose() {
      disposePluginSurface(surface);
    },
  };

  surfaceState.set(surface, { ownedHost, disposed: false });
  return surface;
}

/**
 * Create a dedicated host element inside `parent` and open a ShadowRoot on it.
 * Use for Control Panel blocks and any nested plugin UI.
 */
export function createPluginSurface(parent: HTMLElement): PluginSurfaceHandle {
  const host = document.createElement("div");
  host.className = "mircmd-plugin-surface";
  host.style.cssText =
    "display:block;width:100%;height:100%;min-width:0;min-height:0;box-sizing:border-box;";
  parent.appendChild(host);
  return buildSurface(host, true);
}

/**
 * Open a ShadowRoot on an existing host element (program window content).
 * Does not create or remove the host; only clears the shadow on dispose.
 */
export function adoptPluginSurface(host: HTMLElement): PluginSurfaceHandle {
  return buildSurface(host, false);
}

/**
 * Clear shadow content and, when the host was created by createPluginSurface,
 * remove it from the DOM. Idempotent.
 */
export function disposePluginSurface(surface: PluginSurfaceHandle): void {
  const state = surfaceState.get(surface);
  if (!state || state.disposed) return;

  state.disposed = true;
  surface.root.innerHTML = "";

  if (state.ownedHost) {
    surface.host.remove();
  }
}
