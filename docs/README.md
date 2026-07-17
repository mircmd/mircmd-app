# Mir Commander Core

`mircmd-app` is the desktop core of Mir Commander, an extensible environment for
scientific and engineering applications. The repository provides the
application shell, project data model, plugin discovery and execution, and the
user interface in which plugins operate.

## Documentation

- [Architecture](architecture.md) describes the application layers, state,
  startup sequence, project model, and frontend-backend communication.
- [Plugin runtime](plugin-runtime.md) describes plugin discovery, manifests,
  Core and UI plugin execution, and the contracts currently supported by the
  host.

The public plugin API is a separate concern from the host implementation. API
definitions and compatibility guarantees should be documented and versioned in
the `mircmd-api` repository. This documentation explains how `mircmd-app`
consumes and implements those contracts.

## Technology stack

- **Rust 2024** for the native core
- **Tauri 2** for the desktop application and frontend-backend bridge
- **Svelte 5** and **TypeScript** for the user interface
- **Vite 7** for frontend development and bundling
- **WebAssembly Component Model**, **Wasmtime**, and **WASI Preview 2** for Core
  plugins
- **JavaScript modules** for UI plugins

## Repository map

```text
mircmd-app/
├── ui/                  Svelte user interface and frontend services
├── core/
│   ├── src/             Rust application core
│   ├── wit/             WIT contracts consumed by the host
│   ├── capabilities/    Tauri permission configuration
│   └── tauri.conf.json  Desktop application configuration
├── docs/                Technical documentation for the core
├── package.json         Frontend dependencies and scripts
└── vite.config.ts       Frontend build configuration
```

The main Rust modules are:

- `app_state` — process-wide application state and file-import workflow
- `project` — in-memory project tree and node data
- `file_manager` — dispatch of files to importer plugins
- `plugins` — manifests, discovery, Wasmtime bindings, execution, and asset serving
- `commands` — Tauri commands exposed to the frontend
- `config` and `consts` — persisted settings and user data paths
- `logging` and `menu` — desktop infrastructure

The main frontend areas are:

- `ui/core` — Tauri command wrappers, shared types, plugin management, and program-plugin context
- `ui/lib` — reusable layout, tree, menu, tab, panel, and window components
- `ui/Explorer.svelte` — project navigation and program-plugin launching
- `ui/ConsoleOutput.svelte` — application messages
- `ui/App.svelte` — top-level UI composition and initialization

## Runtime data

The current implementation stores user data under:

```text
~/.config/mircmd/
├── config.yaml
├── logs/
└── plugins/
```

Plugins are discovered from the `plugins` directory when the native application
state is created. See [Plugin runtime](plugin-runtime.md) for the expected
layout.
