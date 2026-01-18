import { writable } from "svelte/store";
import type { WindowItem } from "../lib/components/window_manager.svelte";

export interface PluginWindowData {
  plugin_path: string;
  html_content: string;
}

export interface DynamicWindow extends WindowItem {
  plugin_data?: PluginWindowData;
}

interface WindowStore {
  windows: DynamicWindow[];
  next_z_index: number;
}

const initial_state: WindowStore = {
  windows: [],
  next_z_index: 1,
};

function create_window_store() {
  const { subscribe, update } = writable<WindowStore>(initial_state);

  return {
    subscribe,
    add_window: (
      title: string,
      plugin_path: string,
      html_content: string,
      icon?: string
    ) => {
      update((state) => {
        const id = `window-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        const new_window: DynamicWindow = {
          id,
          title,
          icon,
          x: 50 + (state.windows.length % 5) * 30,
          y: 30 + (state.windows.length % 5) * 30,
          width: 400,
          height: 300,
          zIndex: state.next_z_index,
          plugin_data: {
            plugin_path,
            html_content,
          },
        };
        return {
          windows: [...state.windows, new_window],
          next_z_index: state.next_z_index + 1,
        };
      });
    },
    remove_window: (id: string) => {
      update((state) => ({
        ...state,
        windows: state.windows.filter((w) => w.id !== id),
      }));
    },
    update_windows: (windows: DynamicWindow[]) => {
      update((state) => ({
        ...state,
        windows,
      }));
    },
  };
}

export const window_store = create_window_store();
