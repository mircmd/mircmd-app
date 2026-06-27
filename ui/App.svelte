<script lang="ts">
  import { onMount } from "svelte";

  import ConsoleOutput from "./ConsoleOutput.svelte";
  import Panel from "./lib/Panel.svelte";
  import Menu from "./lib/Menu.svelte";
  import Workspace from "./lib/Workspace.svelte";
  import Explorer from "./Explorer.svelte";
  import WindowManager from "./lib/WindowManager.svelte";
  import { pluginManager } from "./core/plugins";
  import { getContextMenu } from "./core/context_menu.svelte";

  const contextMenu = getContextMenu();

  let workspaceRef: ReturnType<typeof Workspace>;
  let windowManagerRef: ReturnType<typeof WindowManager>;
  let explorerRef: ReturnType<typeof Explorer>;

  onMount(async () => {
    await pluginManager.refresh();
    workspaceRef?.addWidgetToDock("left", explorerSnippet);
    workspaceRef?.addWidgetToDock("bottom", consoleOutputSnippet);
  });
</script>

{#snippet consoleOutputSnippet()}
  <ConsoleOutput />
{/snippet}

{#snippet explorerSnippet()}
  <Explorer bind:this={explorerRef} windowManager={windowManagerRef} />
{/snippet}

{#snippet windowManagerSnippet()}
  <WindowManager bind:this={windowManagerRef} />
{/snippet}

<div class="app-container disable-selection">
  <Workspace bind:this={workspaceRef} centralContent={windowManagerSnippet} />

  {#if contextMenu.current}
    {#key contextMenu.current.id}
      <div class="global-overlay">
        <Menu
          items={contextMenu.current.items}
          posX={contextMenu.current.posX}
          posY={contextMenu.current.posY}
          data={contextMenu.current.data}
          close={() => contextMenu.close()}
        />
      </div>
    {/key}
  {/if}
</div>

<style>
  .app-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .global-overlay {
    position: fixed;
    inset: 0;
    z-index: 10000;
    pointer-events: none; /* clicks pass through the overlay */
  }
  .global-overlay :global(.context-menu) {
    pointer-events: auto; /* но меню кликабельно */
  }
</style>
