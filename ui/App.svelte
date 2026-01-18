<script lang="ts">
  import { onMount } from "svelte";

  import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

  import { getStartupMessages, isDesktop } from "./app";
  import ConsoleOutput from "./docks/console_output.svelte";
  import Explorer from "./docks/explorer.svelte";
  import type { ExpandedState, TreeNode } from "./lib/tree.svelte";
  import WindowManager from "./lib/window_manager/window_manager.svelte";
  import Workspace from "./lib/workspace/workspace.svelte";
  import type { WorkspaceState } from "./lib/workspace/workspace.svelte";

  let consoleOutput: ConsoleOutput | undefined = $state();
  let explorer: Explorer | undefined = $state();

  // Lifted state for docks to persist across panel moves
  let consoleValue = $state("");
  let explorerNodes: TreeNode[] = $state([]);
  let explorerSelectedId: string | null = $state(null);
  let explorerExpandedState: ExpandedState = $state({});

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

  let workspaceState = $state<WorkspaceState>({
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
  });
</script>

<div class="app-container">
  <Workspace bind:data={workspaceState}>
    <WindowManager />

    {#snippet dockContent(dock, _position)}
      {#if dock.id === "console"}
        <ConsoleOutput
          bind:this={consoleOutput}
          bind:value={consoleValue}
          onappend={(text) =>
            (consoleValue += (consoleValue ? "\n" : "") + text)}
          onclear={() => (consoleValue = "")}
        />
      {:else if dock.id === "explorer"}
        <Explorer
          bind:this={explorer}
          bind:nodes={explorerNodes}
          bind:selectedId={explorerSelectedId}
          bind:expandedState={explorerExpandedState}
        />
      {:else}
        <div class="default-dock-content">
          <p>{dock.content}</p>
        </div>
      {/if}
    {/snippet}
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
