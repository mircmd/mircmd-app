<script lang="ts">
  import { onMount } from "svelte";

  import ConsoleOutput from "./ConsoleOutput.svelte";
  import Panel from "./lib/Panel.svelte";
  import Workspace from "./lib/Workspace.svelte";
  import Explorer from "./Explorer.svelte";
  import WindowManager from "./lib/WindowManager.svelte";
  import { pluginManager } from "./core/plugins";

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
</div>

<style>
  .app-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
</style>
