// Utility for loading browser-side WASM Component Model plugins
// Uses jco-transpiled modules with instantiation mode

import type { IconEntry, IconPlugin } from './icon_store';

export interface ProgramPlugin {
  render: (data: Uint8Array) => string;
}

const PLUGIN_BASE_URL = 'plugin://localhost';

// Minimal WASI preview2 shim implementations
function createWasiShims() {
  return {
    'wasi:cli/environment': {
      getEnvironment: () => [],
    },
    'wasi:cli/exit': {
      exit: (status: { tag: string; val?: number }) => {
        if (status.tag === 'err') {
          throw new Error(`WASI exit with code: ${status.val}`);
        }
      },
    },
    'wasi:cli/stderr': {
      getStderr: () => ({
        write: () => ({ tag: 'ok', val: 0n }),
        blockingFlush: () => ({ tag: 'ok' }),
      }),
    },
    'wasi:io/error': {
      Error: class WasiError {
        toDebugString() {
          return 'WASI Error';
        }
      },
    },
    'wasi:io/streams': {
      OutputStream: class OutputStream {
        write() {
          return { tag: 'ok', val: 0n };
        }
        blockingFlush() {
          return { tag: 'ok' };
        }
      },
    },
  };
}

export async function loadBrowserPlugin(pluginPath: string): Promise<ProgramPlugin> {
  const moduleUrl = `${PLUGIN_BASE_URL}/${pluginPath}/plugin.js`;

  // Load the instantiation module
  const pluginModule = await import(moduleUrl);

  // getCoreModule: fetch and compile WASM by name
  const getCoreModule = async (name: string): Promise<WebAssembly.Module> => {
    const url = `${PLUGIN_BASE_URL}/${pluginPath}/${name}`;
    const response = await fetch(url);
    const bytes = await response.arrayBuffer();
    return WebAssembly.compile(bytes);
  };

  // Instantiate with getCoreModule and shims
  const instance = await pluginModule.instantiate(
    getCoreModule,
    createWasiShims()
  );

  return {
    render: instance.render,
  };
}

export async function loadIconPlugin(pluginPath: string): Promise<IconPlugin> {
  const pluginBaseUrl = `${PLUGIN_BASE_URL}/${pluginPath}`;
  const moduleUrl = `${pluginBaseUrl}/plugin.js`;

  const pluginModule = await import(moduleUrl);

  // Icon plugins return a map of kind -> relative icon path
  const iconsMap = pluginModule.instantiate() as Record<string, string>;

  return {
    icons: (): IconEntry[] => {
      return Object.entries(iconsMap).map(([kind, relativePath]) => ({
        kind,
        icon: `${pluginBaseUrl}/${relativePath}`,
      }));
    },
  };
}
