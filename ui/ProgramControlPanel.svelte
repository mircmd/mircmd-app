<!--
  @component ProgramControlPanel

  Host chrome for one program plugin key: accordion blocks and Apply to all.
  Binds to the focused session of this pluginKey (last activated among its windows).
-->
<script lang="ts">
  import { onDestroy } from "svelte";
  import type {
    Cleanup,
    ControlPanelBlock,
    ControlPanelContribution,
    ProgramCommand,
  } from "@mircmd/extensions-api";

  import CollapsibleSection from "./lib/CollapsibleSection.svelte";
  import Panel from "./lib/Panel.svelte";
  import { log } from "./core/commands";
  import type { ProgramManager, ProgramRecord } from "./core/program_manager.svelte";
  import { createPluginSurface, type PluginSurfaceHandle } from "./core/plugin_surface";
  import { createProgramFs } from "./core/program_plugin_context";
  import type { WorkspacePreferences } from "./core/workspace_state.svelte";

  interface Props {
    pluginKey: string;
    programManager?: ProgramManager;
    workspacePreferences?: WorkspacePreferences;
  }

  let { pluginKey, programManager, workspacePreferences }: Props = $props();

  type MountedBlock = {
    abort: AbortController;
    surface: PluginSurfaceHandle | null;
    cleanup: Cleanup | null;
    cleaned: boolean;
  };

  let presentationGeneration = 0;
  let mountedBlocks = new Map<string, MountedBlock>();
  let blockErrors = $state<Record<string, string>>({});
  /** Apply-to-all remembered per pluginKey::broadcastKey for the current app run. */
  let applyToAllByScope = $state<Record<string, boolean>>({});
  let localExpanded = $state<Record<string, boolean>>({});

  let focusedRecord = $derived(
    programManager?.focusedSessionByPluginKey[pluginKey] ?? null,
  );
  let readyRecord = $derived(
    focusedRecord?.lifecycleState === "ready" ? focusedRecord : null,
  );
  let contribution = $derived<ControlPanelContribution | undefined>(
    readyRecord?.session?.controlPanel,
  );
  let blocks = $derived(contribution?.blocks ?? []);
  let panelTitle = $derived(
    contribution?.title ?? readyRecord?.descriptor.metadata.name ?? pluginKey,
  );
  let allowApplyToAll = $derived(contribution?.allowApplyToAll === true);
  let applyScope = $derived(
    readyRecord ? `${readyRecord.pluginKey}::${contribution?.broadcastKey ?? ""}` : "",
  );
  let applyToAll = $derived(allowApplyToAll && !!applyToAllByScope[applyScope]);
  let focusedWindowId = $derived(readyRecord?.windowId ?? null);
  let emptyMessage = $derived(
    !readyRecord
      ? "Waiting for program session"
      : !contribution
        ? "This program has no control panel"
        : blocks.length === 0
          ? "No controls available"
          : "",
  );

  $effect(() => {
    void focusedWindowId;
    blockErrors = {};
  });

  export function remountActive(): void {
    bumpGeneration();
    void teardownAllMounted();
    blockErrors = {};
  }

  function bumpGeneration(): void {
    presentationGeneration += 1;
  }

  function scopeApplyToAll(value: boolean): void {
    if (!applyScope) return;
    applyToAllByScope = { ...applyToAllByScope, [applyScope]: value };
  }

  function onApplyToAllChange(event: Event): void {
    scopeApplyToAll((event.currentTarget as HTMLInputElement).checked);
  }

  function isBlockExpanded(block: ControlPanelBlock): boolean {
    const defaultExpanded = block.initiallyExpanded ?? false;
    if (workspacePreferences) {
      return workspacePreferences.isBlockExpanded(pluginKey, block.id, defaultExpanded);
    }
    const key = `${pluginKey}/${block.id}`;
    if (Object.prototype.hasOwnProperty.call(localExpanded, key)) {
      return localExpanded[key]!;
    }
    return defaultExpanded;
  }

  function setBlockExpanded(blockId: string, expanded: boolean): void {
    if (workspacePreferences) {
      workspacePreferences.setBlockExpanded(pluginKey, blockId, expanded);
      return;
    }
    const key = `${pluginKey}/${blockId}`;
    localExpanded = { ...localExpanded, [key]: expanded };
  }

  async function dispatchCommand(
    source: ProgramRecord,
    command: ProgramCommand,
    signal: AbortSignal,
  ): Promise<void> {
    if (signal.aborted) return;
    if (!programManager) return;

    const focused = programManager.focusedSessionByPluginKey[pluginKey];
    if (!focused || focused.windowId !== source.windowId) return;

    const broadcastKey = source.session?.controlPanel?.broadcastKey ?? "";
    const scope = `${source.pluginKey}::${broadcastKey}`;

    await programManager.dispatch({
      sourceWindowId: source.windowId,
      command,
      applyToAll:
        source.session?.controlPanel?.allowApplyToAll === true &&
        !!applyToAllByScope[scope],
    });
  }

  async function teardownMounted(entry: MountedBlock): Promise<void> {
    if (entry.cleaned) return;
    entry.cleaned = true;
    entry.abort.abort();

    try {
      await entry.cleanup?.();
    } catch (error) {
      log.error(`Control Panel block cleanup failed: ${error}`);
    }

    entry.surface?.dispose();
    entry.surface = null;
    entry.cleanup = null;
  }

  async function teardownAllMounted(): Promise<void> {
    const entries = [...mountedBlocks.values()];
    mountedBlocks.clear();
    await Promise.all(entries.map((entry) => teardownMounted(entry)));
  }

  function mountBlockAction(node: HTMLElement, block: ControlPanelBlock) {
    const record = readyRecord;
    if (!record || !contribution) {
      return {};
    }

    const generation = presentationGeneration;
    const abort = new AbortController();
    const entry: MountedBlock = {
      abort,
      surface: null,
      cleanup: null,
      cleaned: false,
    };
    mountedBlocks.set(block.id, entry);

    const surface = createPluginSurface(node);
    entry.surface = surface;

    Promise.resolve(
      block.mount(surface, {
        signal: abort.signal,
        dispatch: (command) => dispatchCommand(record, command, abort.signal),
        fs: createProgramFs(),
      }),
    )
      .then(async (cleanup) => {
        const stale =
          entry.cleaned || abort.signal.aborted || generation !== presentationGeneration;
        if (stale) {
          try {
            await cleanup?.();
          } catch (error) {
            log.error(`Control Panel late cleanup failed: ${error}`);
          }
          if (!entry.cleaned) {
            surface.dispose();
          }
          return;
        }
        entry.cleanup = cleanup ?? null;
      })
      .catch((error) => {
        if (entry.cleaned || abort.signal.aborted || generation !== presentationGeneration) {
          return;
        }
        const message = error instanceof Error ? error.message : String(error);
        blockErrors = { ...blockErrors, [block.id]: message };
        log.error(`Control Panel block "${block.id}" mount failed: ${message}`);
      });

    return {
      destroy() {
        mountedBlocks.delete(block.id);
        void teardownMounted(entry);
      },
    };
  }

  onDestroy(() => {
    bumpGeneration();
    void teardownAllMounted();
  });
</script>

<Panel title={panelTitle}>
  {#snippet content()}
    <div class="control-panel">
      <div class="control-panel-scroll">
        {#if emptyMessage}
          <p class="empty-state">{emptyMessage}</p>
        {:else if readyRecord && contribution}
          {#key focusedWindowId}
            {#each blocks as block (block.id)}
              <CollapsibleSection
                id={block.id}
                title={block.title}
                expanded={isBlockExpanded(block)}
                onExpandedChange={(expanded) => setBlockExpanded(block.id, expanded)}
              >
                {#snippet children()}
                  <div class="block-host" use:mountBlockAction={block}></div>
                  {#if blockErrors[block.id]}
                    <p class="block-error">Failed to load controls: {blockErrors[block.id]}</p>
                  {/if}
                {/snippet}
              </CollapsibleSection>
            {/each}
          {/key}
        {/if}
      </div>

      {#if allowApplyToAll}
        <footer class="control-panel-footer">
          <label class="apply-all">
            <input type="checkbox" checked={applyToAll} onchange={onApplyToAllChange} />
            Apply to all
          </label>
        </footer>
      {/if}
    </div>
  {/snippet}
</Panel>

<style>
  .control-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-width: 0;
  }

  .control-panel-scroll {
    flex: 1;
    overflow-x: hidden;
    overflow-y: auto;
    min-height: 0;
  }

  .empty-state {
    margin: 12px;
    font-size: 12px;
    color: #666;
  }

  .block-host {
    min-width: 0;
    min-height: 0;
  }

  .block-error {
    margin: 6px 0 0;
    font-size: 11px;
    color: #a40000;
  }

  .control-panel-footer {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
    padding: 8px;
    border-top: 1px solid #dadada;
    flex-shrink: 0;
  }

  .apply-all {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    user-select: none;
  }
</style>
