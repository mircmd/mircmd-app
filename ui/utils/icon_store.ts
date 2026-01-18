import { get, writable } from 'svelte/store';

import iconUnknown from '../assets/icons/unknown.svg';

export interface IconEntry {
  kind: string;
  icon: string;
}

export interface IconPlugin {
  icons: () => IconEntry[];
}

interface IconStoreState {
  icons: Map<string, string>;
  loaded: boolean;
}

const initial_state: IconStoreState = {
  icons: new Map(),
  loaded: false,
};

function create_icon_store() {
  const { subscribe, update } = writable<IconStoreState>(initial_state);

  return {
    subscribe,
    add_icons: (entries: IconEntry[]) => {
      update((state) => {
        const new_icons = new Map(state.icons);
        for (const entry of entries) {
          new_icons.set(entry.kind, entry.icon);
        }
        return {
          ...state,
          icons: new_icons,
        };
      });
    },
    set_loaded: (loaded: boolean) => {
      update((state) => ({
        ...state,
        loaded,
      }));
    },
    get_icon: (kind: string): string => {
      const state = get({ subscribe });
      return state.icons.get(kind) ?? iconUnknown;
    },
  };
}

export const icon_store = create_icon_store();
