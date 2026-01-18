<!--
  @component DockArea

  Internal component for rendering a dock area (left, right, or bottom) within Workspace.
  Handles groups of dockable panels with resize functionality.

  ## Features
  - Renders multiple dock groups
  - Resizable groups within the area
  - Single panel mode: shows Panel with title bar instead of Tabs
  - Multi panel mode: shows Tabs with tab bar
  - Tab reordering and dragging support
  - Drop zone indicators during drag operations
-->
<script lang="ts">
  import type { Snippet } from "svelte";
  import type { DockGroup, DockItem, DockPosition, DropZone } from "./types";
  import Panel from "./panel.svelte";
  import Tabs from "../tabs.svelte";

  interface DragState {
    active: boolean;
    highlightedGroupId: string | null;
    highlightedDropZone: DropZone | null;
  }

  interface Props {
    position: DockPosition;
    groups: DockGroup[];
    dragState: DragState;
    groupElements: Map<string, HTMLElement>;
    onactiveTabChange: (groupId: string, tabId: string) => void;
    onTabReorder: (groupId: string, newItems: DockItem[]) => void;
    onTabDragStart: (groupId: string, dockId: string, x: number, y: number) => void;
    onDockUndock: (groupId: string, dockId: string, x: number, y: number) => void;
    onGroupResize: (groupIndex: number, event: MouseEvent) => void;
    dockContent?: Snippet<[DockItem, DockPosition]>;
  }

  let {
    position,
    groups,
    dragState,
    groupElements,
    onactiveTabChange,
    onTabReorder,
    onTabDragStart,
    onDockUndock,
    onGroupResize,
    dockContent,
  }: Props = $props();

  let isHorizontal = $derived(position === "bottom");
  let tabPosition = $derived(
    position === "left" ? "left" : position === "right" ? "right" : "top"
  );

  function getDropZoneClass(groupId: string): string {
    if (!dragState.active || dragState.highlightedGroupId !== groupId) return "";
    return `drop-highlight drop-${dragState.highlightedDropZone}`;
  }

  function registerGroupRef(
    element: HTMLElement,
    groupId: string
  ): { update: (newGroupId: string) => void; destroy: () => void } {
    groupElements.set(groupId, element);

    return {
      update(newGroupId: string) {
        groupElements.delete(groupId);
        groupId = newGroupId;
        groupElements.set(groupId, element);
      },
      destroy() {
        groupElements.delete(groupId);
      },
    };
  }
</script>

{#each groups as group, index (group.id)}
  <div
    class="group-wrapper {getDropZoneClass(group.id)}"
    style="flex-grow: {group.size};"
    use:registerGroupRef={group.id}
  >
    {#if group.items.length === 1}
      {@const dock = group.items[0]}
      <Panel
        title={dock.title}
        showTitle={true}
        onundock={(pos) => onDockUndock(group.id, dock.id, pos.x, pos.y)}
      >
        <div class="panel-content-wrapper">
          {#if dockContent}
            {@render dockContent(dock, position)}
          {:else}
            <p>{dock.content}</p>
          {/if}
        </div>
      </Panel>
    {:else}
      <Tabs
        tabs={group.items.map((d) => ({ id: d.id, title: d.title }))}
        activeTabId={group.activeTabId}
        hideSingleTab={false}
        draggable={true}
        reorderable={true}
        tabPosition={tabPosition}
        onchange={(tabId) => onactiveTabChange(group.id, tabId)}
        onreorder={(tabs) =>
          onTabReorder(
            group.id,
            tabs.map((t) => group.items.find((d) => d.id === t.id)!)
          )}
        ontabdragstart={(e) => onTabDragStart(group.id, e.tabId, e.x, e.y)}
      >
        {#snippet children(activeTabId)}
          {#each group.items as dock (dock.id)}
            {#if dock.id === activeTabId}
              <Panel title={dock.title} showTitle={false}>
                <div class="panel-content-wrapper">
                  {#if dockContent}
                    {@render dockContent(dock, position)}
                  {:else}
                    <p>{dock.content}</p>
                  {/if}
                </div>
              </Panel>
            {/if}
          {/each}
        {/snippet}
      </Tabs>
    {/if}

    {#if dragState.active && dragState.highlightedGroupId === group.id}
      <div
        class="drop-indicator drop-indicator-{dragState.highlightedDropZone}"
        class:drop-indicator-vertical={!isHorizontal}
        class:drop-indicator-horizontal={isHorizontal}
      ></div>
    {/if}
  </div>

  {#if index < groups.length - 1}
    <div
      class="group-resizer"
      class:group-resizer-horizontal={!isHorizontal}
      class:group-resizer-vertical={isHorizontal}
      role="separator"
      tabindex="0"
      aria-label="Resize dock group"
      onmousedown={(e) => onGroupResize(index, e)}
      onkeydown={(e) => e.key === "Enter" && e.preventDefault()}
    ></div>
  {/if}
{/each}

<style>
  .group-wrapper {
    position: relative;
    flex: 1 1 0;
    min-height: 0;
    min-width: 0;
    display: flex;
    flex-direction: column;
    overflow: visible;
  }

  .group-wrapper > :global(.panel-widget),
  .group-wrapper > :global(.tabs-widget) {
    flex: 1;
    min-height: 0;
    min-width: 0;
  }

  .panel-content-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    box-sizing: border-box;
  }

  .panel-content-wrapper > :global(*) {
    flex: 1;
    min-height: 0;
  }

  /* Group resizers */
  .group-resizer {
    --resizer-hover-color: #317ae7;
    --border-color: #dadada;

    flex-shrink: 0;
    background-color: var(--border-color);
    background-clip: content-box;
    transition:
      background-color 0.1s ease,
      background-clip 0.1s ease;
    z-index: 500;
  }

  .group-resizer:hover,
  .group-resizer:active {
    background-color: var(--resizer-hover-color);
    background-clip: border-box;
    z-index: 2000;
  }

  .group-resizer-horizontal {
    height: 1px;
    width: 100%;
    padding: 1.5px 0;
    margin: -1.5px 0;
    cursor: ns-resize;
  }

  .group-resizer-vertical {
    width: 1px;
    height: 100%;
    padding: 0 1.5px;
    margin: 0 -1.5px;
    cursor: ew-resize;
  }

  /* Drop indicators */
  .drop-indicator {
    --drop-zone-bg: rgba(49, 122, 231, 0.15);
    --drop-zone-border: rgba(49, 122, 231, 0.5);

    position: absolute;
    background-color: var(--drop-zone-bg);
    border: 2px solid var(--drop-zone-border);
    pointer-events: none;
    z-index: 100;
    animation: fade-in 0.1s ease;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  /* Vertical split (left/right areas): top/bottom zones */
  .drop-indicator-vertical.drop-indicator-before {
    inset: 0 0 auto 0;
    height: 25%;
  }

  .drop-indicator-vertical.drop-indicator-after {
    inset: auto 0 0 0;
    height: 25%;
  }

  .drop-indicator-vertical.drop-indicator-center {
    inset: 25% 0;
  }

  /* Horizontal split (bottom area): left/right zones */
  .drop-indicator-horizontal.drop-indicator-before {
    inset: 0 auto 0 0;
    width: 25%;
  }

  .drop-indicator-horizontal.drop-indicator-after {
    inset: 0 0 0 auto;
    width: 25%;
  }

  .drop-indicator-horizontal.drop-indicator-center {
    inset: 0 25%;
  }
</style>
