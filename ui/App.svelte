<script lang="ts">
  import { onDestroy, onMount } from "svelte";

  import ConsoleOutput from "./ConsoleOutput.svelte";
  import Menu from "./lib/Menu.svelte";
  import AppWorkspace from "./AppWorkspace.svelte";
  import Explorer from "./Explorer.svelte";
  import ProgramControlPanel from "./ProgramControlPanel.svelte";
  import WindowManager from "./lib/WindowManager.svelte";
  import type { LayoutItemHandle } from "./lib/Layout.svelte";
  import { pluginManager } from "./core/plugins";
  import { getContextMenu } from "./core/context_menu.svelte";
  import { ProgramManager } from "./core/program_manager.svelte";
  import {
    programControlPanelId,
    WorkspacePreferences,
  } from "./core/workspace_state.svelte";

  const contextMenu = getContextMenu();

  let workspaceRef: ReturnType<typeof AppWorkspace>;
  let windowManagerRef: ReturnType<typeof WindowManager>;
  let explorerRef: ReturnType<typeof Explorer>;
  let programManager = $state<ProgramManager | null>(null);
  let workspacePreferences = $state(new WorkspacePreferences());

  /** Right-dock handles for program control panels, keyed by plugin key. */
  const controlPanelHandles = new Map<string, LayoutItemHandle>();

  onMount(async () => {
    await pluginManager.refresh();
    await workspacePreferences.load();
    programManager = new ProgramManager(windowManagerRef);
    workspaceRef?.addWidgetToDock("left", explorerSnippet);
    workspaceRef?.addWidgetToDock("bottom", consoleOutputSnippet);
  });

  // Lazily create/destroy one right-dock control panel per open plugin key.
  $effect(() => {
    const manager = programManager;
    const workspace = workspaceRef;
    if (!manager || !workspace) return;

    const keys = new Set(manager.openPanelPluginKeys);

    for (const pluginKey of keys) {
      if (controlPanelHandles.has(pluginKey)) continue;

      const panelId = programControlPanelId(pluginKey);
      const handle = workspace.addWidgetToDock("right", {
        component: ProgramControlPanel,
        props: {
          pluginKey,
          programManager: manager,
          workspacePreferences,
        },
      });
      handle.setVisible(workspacePreferences.isPanelVisible(panelId));
      controlPanelHandles.set(pluginKey, handle);
    }

    for (const pluginKey of [...controlPanelHandles.keys()]) {
      if (keys.has(pluginKey)) continue;
      controlPanelHandles.get(pluginKey)?.remove();
      controlPanelHandles.delete(pluginKey);
    }
  });

  onDestroy(() => {
    for (const handle of controlPanelHandles.values()) {
      handle.remove();
    }
    controlPanelHandles.clear();
    void programManager?.disposeAll();
  });
</script>

{#snippet consoleOutputSnippet()}
  <ConsoleOutput />
{/snippet}

{#snippet explorerSnippet()}
  {#if programManager}
    <Explorer bind:this={explorerRef} {programManager} />
  {/if}
{/snippet}

{#snippet windowManagerSnippet()}
  <WindowManager bind:this={windowManagerRef} />
{/snippet}

<div class="app-container disable-selection">
  <AppWorkspace
    bind:this={workspaceRef}
    {workspacePreferences}
    centralContent={windowManagerSnippet}
  />

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
    pointer-events: auto;
  }
</style>
