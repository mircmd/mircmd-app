<script lang="ts">
  import { onMount, tick } from "svelte";
  import { getAppConfig, getStartupMessages } from "./app";
  import ConsoleOutput from "./docks/console_output.svelte";
  import Explorer from "./docks/explorer.svelte";
  import WindowManager from "./lib/components/window_manager.svelte";
  import type { WindowItem } from "./lib/components/window_manager.svelte";
  import Workspace from "./lib/components/workspace.svelte";
  import type { WorkspaceState } from "./lib/components/workspace.svelte";
  import { open } from "./utils/dialog";
  import { getPlugins } from "./utils/plugins";
  import {
    loadMoleculeVisualizer,
    type ProgramPlugin,
  } from "./utils/browser_plugins";

  import iconMolecule from "./assets/icons/molecule.png";
  import iconAtomicCoordinates from "./assets/icons/atomic_coordinates.png";
  import iconVolumeCube from "./assets/icons/volume_cube.png";

  let consoleOutput: ConsoleOutput;
  let visualizerPlugin: ProgramPlugin | null = null;
  let visualizerHtml = "";

  onMount(async () => {
    const config = await getAppConfig();
    consoleOutput?.appendLine(`Config loaded: ${JSON.stringify(config)}`);

    const startupMessages = await getStartupMessages();
    for (const message of startupMessages) {
      consoleOutput?.appendLine(message);
    }
  });

  async function handleGetPlugins() {
    try {
      const plugins = await getPlugins();
      consoleOutput?.appendLine("Loaded Plugins:");
      consoleOutput?.appendLine(JSON.stringify(plugins, null, 2));
    } catch (e) {
      consoleOutput?.appendLine(`Error loading plugins: ${e}`);
    }
  }

  async function handleLoadVisualizer() {
    try {
      consoleOutput?.appendLine("Loading WASM plugin...");
      visualizerPlugin = await loadMoleculeVisualizer();
      consoleOutput?.appendLine(`Plugin loaded`);
      visualizerHtml = visualizerPlugin.render();

      // Wait for DOM update, then execute scripts
      await tick();
      const container = document.querySelector(".plugin-output");
      if (container) {
        const scripts = container.querySelectorAll("script");
        scripts.forEach((oldScript) => {
          const newScript = document.createElement("script");
          newScript.textContent = oldScript.textContent;
          oldScript.parentNode?.replaceChild(newScript, oldScript);
        });
      }
    } catch (e) {
      consoleOutput?.appendLine(`Error loading WASM plugin: ${e}`);
    }
  }

  let windowsState: WindowItem[] = [
    {
      id: "window-1",
      title: "Document 1",
      icon: iconMolecule,
      x: 50,
      y: 30,
      width: 300,
      height: 200,
      zIndex: 1,
    },
    {
      id: "window-2",
      title: "Properties Editor",
      icon: iconAtomicCoordinates,
      x: 200,
      y: 120,
      width: 350,
      height: 250,
      zIndex: 2,
    },
    {
      id: "window-3",
      title: "WASM Plugin Demo",
      icon: iconVolumeCube,
      x: 400,
      y: 50,
      width: 400,
      height: 300,
      zIndex: 3,
    },
    {
      id: "window-4",
      title: "Material Editor",
      icon: iconMolecule,
      x: 100,
      y: 200,
      width: 320,
      height: 220,
      zIndex: 4,
    },
    {
      id: "window-5",
      title: "Timeline",
      icon: iconAtomicCoordinates,
      x: 300,
      y: 280,
      width: 450,
      height: 180,
      zIndex: 5,
    },
  ];

  let workspaceState: WorkspaceState = {
    left: [
      {
        id: "left-group-1",
        items: [
          {
            id: "explorer",
            title: "Explorer",
            content: "File explorer content",
          },
        ],
        activeTabId: "explorer",
        size: 1,
      },
    ],
    right: [
      {
        id: "right-group-1",
        items: [
          {
            id: "properties",
            title: "Properties",
            content: "Properties panel content",
          },
        ],
        activeTabId: "properties",
        size: 1,
      },
    ],
    bottom: [
      {
        id: "bottom-group-1",
        items: [
          {
            id: "console",
            title: "Console output",
            content: "Console output content",
          },
        ],
        activeTabId: "console",
        size: 1,
      },
    ],
  };
</script>

<div class="app-container">
  <Workspace bind:state={workspaceState}>
    <WindowManager bind:windows={windowsState}>
      <svelte:fragment slot="windowContent" let:window>
        {#if window.id === "window-1"}
          <div class="window-example-content">
            <h3>Document 1</h3>
            <p>This is a floating window with some example content.</p>
            <div class="actions">
              <button on:click={() => open.about()}>About</button>
              <button on:click={handleGetPlugins}>List Plugins</button>
            </div>
          </div>
        {:else if window.id === "window-2"}
          <div class="window-example-content">
            <h3>Properties Editor</h3>
            <p>Edit properties of selected objects here.</p>
            <ul>
              <li>Position: 0, 0, 0</li>
              <li>Rotation: 0°</li>
              <li>Scale: 1.0</li>
            </ul>
          </div>
        {:else if window.id === "window-3"}
          <div class="window-example-content">
            <h3>WASM Plugin Demo</h3>
            <button on:click={handleLoadVisualizer}>Load WASM Plugin</button>
            {#if visualizerHtml}
              <div class="plugin-output">
                {@html visualizerHtml}
              </div>
            {:else}
              <p>Click button to load the plugin</p>
            {/if}
          </div>
        {:else if window.id === "window-4"}
          <div class="window-example-content">
            <h3>Material Editor</h3>
            <p>Configure material properties:</p>
            <ul>
              <li>Diffuse: #FFFFFF</li>
              <li>Specular: 0.5</li>
              <li>Roughness: 0.3</li>
            </ul>
          </div>
        {:else if window.id === "window-5"}
          <div class="window-example-content">
            <h3>Timeline</h3>
            <p>Animation timeline with keyframes.</p>
            <p>Duration: 0:00 - 5:00</p>
          </div>
        {:else}
          <div class="window-example-content">
            <p>Window: {window.title}</p>
          </div>
        {/if}
      </svelte:fragment>
    </WindowManager>

    <svelte:fragment slot="dockContent" let:dock let:position>
      {#if dock.id === "console"}
        <ConsoleOutput bind:this={consoleOutput} />
      {:else if dock.id === "explorer"}
        <Explorer />
      {:else}
        <div class="default-dock-content">
          <p>{dock.content}</p>
        </div>
      {/if}
    </svelte:fragment>
  </Workspace>
</div>

<style>
  .app-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .default-dock-content {
    padding: 10px;
  }

  .window-example-content {
    padding: 12px;
  }

  .window-example-content h3 {
    margin: 0 0 8px 0;
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }

  .window-example-content p {
    margin: 0 0 8px 0;
    font-size: 12px;
    color: #555;
  }

  .window-example-content ul {
    margin: 8px 0 0 0;
    padding-left: 20px;
  }

  .window-example-content li {
    font-size: 12px;
    color: #555;
    margin-bottom: 4px;
  }

  .actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }

  button {
    padding: 4px 8px;
    font-size: 12px;
    cursor: pointer;
  }

  .plugin-output {
    margin-top: 12px;
    padding: 8px;
    background: #f5f5f5;
    border-radius: 4px;
    border: 1px solid #ddd;
  }

  .plugin-output :global(h2) {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #333;
  }

  .plugin-output :global(p) {
    margin: 4px 0;
    font-size: 12px;
    color: #666;
  }

  .plugin-output :global(ul) {
    margin: 8px 0 0 0;
    padding-left: 20px;
  }

  .plugin-output :global(li) {
    font-size: 12px;
    color: #555;
  }
</style>
