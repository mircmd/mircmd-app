<script lang="ts">
  import { onMount, tick } from "svelte";
  import { getAppConfig, getStartupMessages, isDesktop } from "./app";
  import ConsoleOutput from "./docks/console_output.svelte";
  import Explorer from "./docks/explorer.svelte";
  import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
  import WindowManager from "./lib/components/window_manager.svelte";
  import Workspace from "./lib/components/workspace.svelte";
  import type { WorkspaceState } from "./lib/components/workspace.svelte";
  import { window_store, type DynamicWindow } from "./utils/window_store";

  let consoleOutput: ConsoleOutput;
  let explorer: Explorer;
  let windows_state: DynamicWindow[] = [];

  // Subscribe to window store
  window_store.subscribe((state) => {
    windows_state = state.windows;
  });

  onMount(async () => {
    const startupMessages = await getStartupMessages();
    for (const message of startupMessages) {
      consoleOutput?.appendLine(message);
    }

    if (isDesktop) {
      const appWebview = getCurrentWebviewWindow();
      appWebview.listen<boolean>("explorer_refresh", () => {
        explorer?.refresh();
      });
      appWebview.listen<string>("console_output_append_line", (event) => {
        consoleOutput?.appendLine(event.payload);
      });
    }
  });

  function execute_scripts_in_container_action(
    node: HTMLElement,
    _window_id: string
  ) {
    // Execute scripts after the HTML is rendered
    tick().then(() => {
      const scripts = node.querySelectorAll("script");
      scripts.forEach((old_script) => {
        const new_script = document.createElement("script");
        new_script.textContent = old_script.textContent;
        old_script.parentNode?.replaceChild(new_script, old_script);
      });
    });
    return {};
  }

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
    <WindowManager
      bind:windows={windows_state}
      on:close={(e) => window_store.remove_window(e.detail.id)}
    >
      <svelte:fragment slot="windowContent" let:window>
        {@const win = window as DynamicWindow}
        {#if win.plugin_data}
          <div
            class="plugin-output"
            id="plugin-container-{win.id}"
            use:execute_scripts_in_container_action={win.id}
          >
            {@html win.plugin_data.html_content}
          </div>
        {:else}
          <div class="window-example-content">
            <p>Window: {win.title}</p>
          </div>
        {/if}
      </svelte:fragment>
    </WindowManager>

    <svelte:fragment slot="dockContent" let:dock let:position>
      {#if dock.id === "console"}
        <ConsoleOutput bind:this={consoleOutput} />
      {:else if dock.id === "explorer"}
        <Explorer bind:this={explorer} />
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

  .window-example-content p {
    margin: 0;
    font-size: 12px;
    color: #555;
  }

  .plugin-output {
    width: 100%;
    height: 100%;
    padding: 0px;
    box-sizing: border-box;
    background: #f5f5f5;
    overflow: hidden;
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
