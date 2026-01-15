// Utility for loading browser-side WASM Component Model plugins
// Uses jco-transpiled modules with instantiation mode

export interface ProgramPlugin {
  render: () => string;
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

export async function loadMoleculeVisualizer(): Promise<ProgramPlugin> {
  const pluginPath = 'mircmd-dev/chemistry-molecular-visualizer';
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
