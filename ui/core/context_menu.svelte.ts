import type { MenuItem } from "../lib/Menu.svelte";

export type ContextMenuState = {
  id: number;
  items: MenuItem[];
  posX: number;
  posY: number;
  data: unknown;
} | null;

let state = $state<ContextMenuState>(null);
let open_id = 0;

function isInsideMenu(target: EventTarget | null): boolean {
  if (!(target instanceof Node)) return false;
  return Array.from(document.querySelectorAll(".context-menu")).some((menu) => menu.contains(target));
}

document.addEventListener(
  "contextmenu",
  (event) => {
    if (state && !isInsideMenu(event.target)) {
      state = null;
    }
  },
  true,
);

export function getContextMenu() {
  return {
    get current() {
      return state;
    },
    open(params: { event: MouseEvent; items: MenuItem[]; data?: unknown }) {
      open_id += 1;
      state = { id: open_id, 
        posX: params.event.clientX, 
        posY: params.event.clientY, 
        ...params, 
        data: params.data ?? null 
      };
    },
    close() {
      state = null;
    },
  };
}
