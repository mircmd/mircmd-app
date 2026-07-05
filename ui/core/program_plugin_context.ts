import { getContextMenu } from "./context_menu.svelte";
import type { MenuItem } from "../lib/Menu.svelte";

export interface ProgramPluginContext {
  host: HTMLElement;
  root: ShadowRoot;
  addStyles: (cssText: string) => void;
  contextMenu: {
    open: (params: { event: MouseEvent; items: MenuItem[]; data?: unknown }) => void;
    close: () => void;
  };
}

const contextMenu = getContextMenu();

export function createProgramPluginContext(host: HTMLElement): ProgramPluginContext {
  const shadowRoot = host.attachShadow({ mode: 'open' });
  shadowRoot.innerHTML = "";

  return {
    host,
    root: shadowRoot,
    addStyles: (cssText) => {
      const style = document.createElement('style');
      style.textContent = cssText;
      shadowRoot.appendChild(style);
    },
    contextMenu: {
      open: (params) => contextMenu.open(params),
      close: () => contextMenu.close()
    }
  };
}
