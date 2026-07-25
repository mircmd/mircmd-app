/**
 * Framework-neutral context menu item types.
 * Host-local contract; do not import Menu.svelte from plugin code.
 *
 * TODO: move MenuItem definition out of Menu.svelte and re-export from here.
 */

export interface MenuItem {
  label: string;
  icon?: string;
  disabled?: boolean;
  shortcut?: string;
  action?: (data: unknown) => void;
  children?: MenuItem[];
  checkable?: boolean;
  checked?: boolean;
  separator?: boolean;
}

export interface ContextMenuParams {
  event: MouseEvent;
  items: MenuItem[];
  data?: unknown;
}
