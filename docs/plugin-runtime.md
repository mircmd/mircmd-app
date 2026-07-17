# Plugin Runtime

## Overview

Mir Commander supports two execution targets:

- **Core plugins** are WebAssembly components executed by the Rust backend with
  Wasmtime and WASI Preview 2.
- **UI plugins** are JavaScript modules loaded by the web frontend and executed
  inside the application webview.

Both targets use the same YAML manifest for discovery. The manifest selects the
execution target and plugin type; the corresponding host subsystem determines
the executable file and runtime contract.

Public API definitions should be maintained in `mircmd-api`. This document
describes the behavior currently implemented by `mircmd-app`.

## Installation layout

The host scans plugins below `~/.config/mircmd/plugins` using a two-level
publisher/plugin hierarchy:

```text
~/.config/mircmd/plugins/
└── <publisher>/
    └── <plugin>/
        ├── manifest.yaml
        ├── plugin.wasm       Core target
        ├── plugin.js         UI target
        └── ...               Additional UI assets
```

The relative path `<publisher>/<plugin>` becomes the runtime path exposed to
the frontend. Directory names and manifest metadata are currently not checked
for consistency.

## Manifest

Every plugin directory must contain `manifest.yaml`:

```yaml
target: Ui
type: Program
protocol: v1
metadata:
  id: molecular-visualizer
  name: Molecular Visualizer
  version: 0.1.0
  publisher: mircmd
  description: Interactive molecular structure visualization
```

Supported fields:

| Field | Values | Purpose |
| --- | --- | --- |
| `target` | `Core`, `Ui` | Selects the execution environment |
| `type` | `FileImporter`, `Icons`, `Program` | Selects the host integration |
| `protocol` | `v1` | Version of plugin protocol |
| `metadata.id` | string | Publisher-local plugin identifier |
| `metadata.name` | string | User-facing name |
| `metadata.version` | string | Plugin version |
| `metadata.publisher` | string | Publisher identifier |
| `metadata.description` | string | User-facing description |

The backend parses manifests with Serde. Unknown enum values or missing
required fields cause that plugin to be rejected during discovery.

The combinations with an implemented execution path are:

| Target | Type | Executed by |
| --- | --- | --- |
| `Core` | `FileImporter` | Rust backend through Wasmtime |
| `Ui` | `Icons` | Frontend plugin manager |
| `Ui` | `Program` | Frontend plugin manager |

Other target/type combinations may be discovered but do not currently have a
complete host integration.

## Discovery

Plugin discovery runs in `AppState::new`:

1. create a Wasmtime engine with Component Model support;
2. create a component linker and add WASI Preview 2;
3. enumerate publisher directories;
4. enumerate plugin directories under each publisher;
5. parse each `manifest.yaml`;
6. add its path and manifest to the list exposed to the frontend;
7. for a Core target, load `plugin.wasm` as a Wasmtime component and register
   it by plugin type and `<metadata.publisher>:<metadata.id>`.

A failure in one publisher or plugin is logged and discovery continues with
other entries. Discovery order follows filesystem iteration order and should
not be treated as stable.

Backend discovery currently happens once at application startup. UI registries
are populated when `App.svelte` calls the frontend plugin manager's `refresh`
method during mounting.

## Core plugins

### Runtime

Core plugins are loaded from `plugin.wasm` using the WebAssembly Component
Model. The host uses a shared Wasmtime engine and linker, then creates a new
store and WASI context for each invocation.

The host-side WIT binding is generated from:

```text
core/wit/file-importer.wit
```

The current file-importer world is:

```wit
package mircmd:api;

world file-importer {
    export load: func(file-path: string) -> result<list<u8>, string>;
}
```

This WIT file is part of the host implementation. Its canonical public version
and compatibility policy should be maintained in `mircmd-api`.

### File importer execution

When the application imports a file:

1. `FileManager` chooses a registered Core `FileImporter`;
2. the host preopens the file's containing directory with read-only directory
   and file permissions;
3. the host instantiates the component with a fresh WASI context;
4. the plugin receives only the file name, relative to the preopened directory;
5. the plugin returns either an error string or a byte array;
6. the host interprets successful bytes as a JSON-encoded raw project node;
7. the host assigns UUID v7 identifiers and adds the resulting tree to the
   current project.

The JSON returned by an importer has this recursive shape:

```json
{
  "name": "example",
  "type": "publisher:domain:data-type",
  "data": [],
  "children": []
}
```

`data` is a byte array whose encoding is defined by the domain API, not by the
core. `children` may be omitted and defaults to an empty array.

The current `FileManager` returns the result of the first importer in its
registry, including an error result. It does not yet continue to subsequent
importers when a plugin declines or fails to load a file. Because the registry
is a hash map, applications must not rely on importer selection order.

## UI plugins

### Asset protocol

The native application registers a custom `plugin://` URI scheme. A URL such
as:

```text
plugin://localhost/<publisher>/<plugin>/plugin.js
```

is served from:

```text
~/.config/mircmd/plugins/<publisher>/<plugin>/plugin.js
```

The handler currently recognizes JavaScript, CSS, HTML, JSON, and WebAssembly
MIME types and adds CORS headers. UI plugins may place additional assets beside
`plugin.js` and resolve them relative to `import.meta.url`.

### Module contract

Every UI plugin must export an `instantiate` function:

```ts
export function instantiate() {
  // Return the interface required by the manifest's plugin type.
}
```

If the module cannot be imported or does not export `instantiate`, the frontend
logs the error and does not register the plugin.

### Icons plugins

For an `Icons` plugin, `instantiate()` returns an object whose:

- keys are project node type identifiers;
- values are asset paths relative to the plugin directory.

Conceptually:

```ts
export function instantiate() {
  return {
    "mircmd:example:data": "icons/example.svg"
  };
}
```

The frontend converts each relative path into a `plugin://` URL and stores it
in the icon registry. The explorer resolves icons by project node type.

### Program plugins

For a `Program` plugin, `instantiate()` returns:

```ts
interface ProgramPluginInstance {
  supportedTypes(): string[];
  run(
    context: ProgramPluginContext,
    nodeType: string,
    nodeData: Uint8Array
  ): unknown;
}
```

`supportedTypes()` is called during registration. The plugin is added to the
program registry for each returned project node type. Its user-facing metadata
comes from the manifest.

When the user selects a program from an explorer node's context menu, the host
retrieves the node payload, opens a managed window, creates a plugin context,
and calls `run`. The current caller ignores the return value and does not await
asynchronous completion, so plugins must handle their own asynchronous errors
and lifecycle.

### Program plugin context

The context supplied to `run` contains:

```ts
interface ProgramPluginContext {
  host: HTMLElement;
  root: ShadowRoot;
  addStyles(cssText: string): void;
  contextMenu: {
    open(params: {
      event: MouseEvent;
      items: MenuItem[];
      data?: unknown;
    }): void;
    close(): void;
  };
}
```

The host attaches an open Shadow DOM root to the program window. Plugins should
render inside `context.root` and use `addStyles` for styles that belong inside
that root. The shared context-menu service lets a plugin use host menus without
reimplementing menu placement and interaction.

There is currently no explicit dispose callback. A program that creates event
listeners, observers, timers, animation loops, or GPU resources must therefore
manage cleanup carefully when its host element is disconnected.

## Current lifecycle and compatibility constraints

- Native plugins are discovered only during application startup.
- The host does not currently install, update, disable, unload, or hot-reload
  plugin packages.
- There is no manifest schema version, API version, dependency declaration, or
  capability declaration.
- UI plugin modules run in the application webview rather than an isolated
  process.
- Core plugins receive a fresh WASI store for each file-import invocation.
- Project node payload compatibility is defined by node type and the relevant
  domain API.

Changes to the manifest schema, WIT worlds, JavaScript module exports,
`ProgramPluginContext`, or project node serialization are compatibility changes
and should be coordinated through `mircmd-api`.
