# Architecture

## Purpose and boundaries

`mircmd-app` is the host application for the Mir Commander plugin ecosystem.
It owns infrastructure that is common to all scientific domains:

- desktop application lifecycle and persistent configuration;
- the in-memory project tree and opaque node payloads;
- discovery and execution of installed plugins;
- file import orchestration;
- the application workspace, explorer, menus, windows, and console;
- communication between the native core and the web frontend.

The core does not interpret domain-specific project data. A project node has a
type identifier and an opaque byte payload; plugins define the meaning and
encoding of that payload. Public contracts belong to `mircmd-api`, while
domain-specific implementations belong to plugin repositories.

## High-level structure

```text
┌──────────────────────────────────────────────────────────────┐
│ Svelte frontend (`ui/`)                                      │
│                                                              │
│ App / Workspace / Explorer / Windows                         │
│              │                                               │
│              ├── frontend plugin manager                     │
│              └── typed wrappers around Tauri commands        │
└───────────────────────────┬──────────────────────────────────┘
                            │ Tauri invoke and events
┌───────────────────────────▼──────────────────────────────────┐
│ Rust core (`core/src/`)                                      │
│                                                              │
│ commands ── AppState ── Project                              │
│                    ├── PluginManager ── Wasmtime/WASI        │
│                    ├── FileManager                           │
│                    └── Config                                │
└───────────────────────────┬──────────────────────────────────┘
                            │
             ┌──────────────┴──────────────┐
             │                             │
     Core WASM components          UI JavaScript modules
```

## Native core

### Application entry point

`core/src/main.rs` is responsible for:

1. parsing file paths supplied on the command line;
2. initializing logging;
3. registering the `plugin://` URI scheme;
4. creating a mutex-protected `AppState`;
5. registering Tauri commands;
6. importing command-line files into the temporary project;
7. creating the main window and tracking its position and size;
8. saving the configuration when the application exits.

The application currently creates one temporary in-memory project per process.
Project persistence is not implemented in this repository.

### Shared application state

The native state is stored as `Mutex<AppState>` and contains:

```text
AppState
├── Config
├── Project
├── PluginManager
├── FileManager
└── startup messages
```

`AppState::new` establishes an important initialization order:

1. initialize the Wasmtime-based plugin manager;
2. discover plugins under the user plugin directory;
3. extract Core `FileImporter` plugins into the file manager;
4. load the application configuration;
5. create an empty temporary project.

Plugins are therefore discovered once during native state initialization. The
current backend does not expose installation, unloading, or rediscovery
commands.

### Project model

A project is a recursive tree of `ProjectNode` values:

```text
ProjectNode
├── id: UUID v7
├── name: string
├── type: string
├── data: bytes
└── children: ProjectNode[]
```

The node `type` is the routing key used by UI program and icon plugins. The
`data` field is deliberately opaque to the core and is not included when a
node is serialized for the frontend tree. The frontend requests the payload
separately when it launches a program for a node.

Importer plugins return a serialized raw node tree without IDs. The host
assigns a new UUID v7 to every imported node while converting it into the
native project model.

### Frontend-backend interface

The native core exposes Tauri commands for:

- reading application configuration and startup messages;
- listing discovered plugins;
- reading the project root or a node by ID;
- reading a node payload by ID;
- opening the native file picker and importing files;
- forwarding frontend log messages to the native logger.

The TypeScript wrappers in `ui/core/commands.ts` are the frontend boundary for
these calls. When the UI is running outside Tauri, the wrappers return fallback
configuration and empty project/plugin data instead of invoking native
commands.

The backend also emits events:

- `explorer_add_node` after a file has been imported successfully;
- `console_output_append_line` when an import error should be shown.

This keeps the explorer and console synchronized with asynchronous native file
picker callbacks.

## Frontend

`ui/main.ts` mounts the Svelte application. `ui/App.svelte` initializes the
frontend plugin registry and composes the main workspace.

The user interface is organized around:

- an explorer backed by the native project tree;
- a dockable workspace;
- managed program windows;
- context menus shared by the host and UI plugins;
- a console for startup and runtime messages.

When a user launches a program from an explorer node, the frontend:

1. retrieves the node payload from the Rust core;
2. creates a managed window;
3. attaches an isolated Shadow DOM root to the window host;
4. creates a `ProgramPluginContext`;
5. calls the selected UI plugin with the context, node type, and payload.

## Configuration and runtime directories

`Dirs` resolves runtime paths below `~/.config/mircmd`:

- `config.yaml` — language and main-window geometry;
- `logs/` — application logs;
- `plugins/` — installed plugin packages.

Window geometry is updated from native window events and saved on application
exit. If the configuration file contains invalid YAML, defaults are used in
memory and the invalid file is preserved rather than overwritten.

## Dependency direction

The intended dependency direction is:

```text
domain plugins ──► public mircmd-api contracts ◄── mircmd-app host
```

Plugin code must not import internal modules from `mircmd-app`. Likewise, the
host should route opaque domain data without embedding domain-specific schemas.

Changes to WIT worlds, plugin manifests, JavaScript plugin exports, project node
serialization, or `ProgramPluginContext` affect the public integration surface
and must be coordinated with `mircmd-api` and existing plugins.

For loading and execution details, see [Plugin runtime](plugin-runtime.md).
