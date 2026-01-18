<script lang="ts">
  import { onMount } from "svelte";

  import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

  import { getStartupMessages, isDesktop } from "./app";
  import ConsoleOutput from "./docks/console_output.svelte";
  import Explorer from "./docks/explorer.svelte";
  import WindowManager from "./lib/window_manager/window_manager.svelte";
  import Workspace from "./lib/workspace.svelte";
  import type { WorkspaceState } from "./lib/workspace.svelte";

  let consoleOutput: ConsoleOutput;
  let explorer: Explorer;

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
    <WindowManager />

    <svelte:fragment slot="dockContent" let:dock>
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
</style>
