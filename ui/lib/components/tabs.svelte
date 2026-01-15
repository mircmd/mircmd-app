<!--
  @component Tabs

  Tabs widget component for switching between content panels.
  Provides a tab bar with selectable tabs and associated content area.

  ## Features
  - Horizontal tabs (top) or vertical tabs (left/right)
  - Active tab highlighting
  - Optional single tab hiding (hideSingleTab)
  - Tab dragging out of widget (for panel undocking)
  - Tab reordering within the tab bar
  - Drop indicator during reorder operations
  - Keyboard navigation support

  ## Props
  - `tabs: Tab[]` - Array of tab objects with id and title
  - `activeTabId: string` - ID of currently active tab
  - `hideSingleTab: boolean` - Hide tab bar when only one tab exists (default: true)
  - `draggable: boolean` - Enable dragging tabs out of widget (default: false)
  - `reorderable: boolean` - Enable tab reordering (default: false)
  - `tabPosition: TabPosition` - Position of tab bar: "top" | "left" | "right" (default: "top")

  ## Events
  - `change` - Fired when active tab changes: `string` (tab id)
  - `reorder` - Fired when tabs are reordered: `{ tabs: Tab[] }`
  - `tabdragstart` - Fired when tab drag starts: `{ tabId: string, x: number, y: number }`
  - `tabdragmove` - Fired during tab drag: `{ tabId: string, x: number, y: number }`
  - `tabdragend` - Fired when tab drag ends: `{ tabId: string }`

  ## Slots
  - default - Content area, receives `activeTabId` prop via let:activeTabId
-->
<script lang="ts" context="module">
  export interface Tab {
    id: string;
    title: string;
  }

  export type TabPosition = "top" | "left" | "right";
</script>

<script lang="ts">
  import { createEventDispatcher, onDestroy } from "svelte";

  export let tabs: Tab[] = [];
  export let activeTabId: string = "";
  export let hideSingleTab: boolean = true;
  export let draggable: boolean = false;
  export let reorderable: boolean = false;
  export let tabPosition: TabPosition = "top";

  const dispatch = createEventDispatcher<{
    change: string;
    reorder: { tabs: Tab[] };
    tabdragstart: { tabId: string; x: number; y: number };
    tabdragmove: { tabId: string; x: number; y: number };
    tabdragend: { tabId: string };
  }>();

  $: showTabBar = !(hideSingleTab && tabs.length === 1);
  $: isVertical = tabPosition === "left" || tabPosition === "right";

  $: if (tabs.length > 0 && !tabs.some((t) => t.id === activeTabId)) {
    activeTabId = tabs[0].id;
  }

  // Tab dragging state (for dragging out of widget)
  let draggingTabId: string | null = null;
  let dragStartX = 0;
  let dragStartY = 0;
  let isDraggingOut = false;

  // Reorder state (for reordering within tab bar)
  let isReordering = false;
  let reorderTabId: string | null = null;
  let dropIndicatorIndex: number = -1;
  let tabBarElement: HTMLElement;
  let tabElements: Map<string, HTMLElement> = new Map();

  function selectTab(tabId: string) {
    if (activeTabId !== tabId) {
      activeTabId = tabId;
      dispatch("change", tabId);
    }
  }

  function handleTabMouseDown(event: MouseEvent, tabId: string) {
    if (!draggable && !reorderable) return;

    draggingTabId = tabId;
    reorderTabId = tabId;
    dragStartX = event.clientX;
    dragStartY = event.clientY;
    isDraggingOut = false;
    isReordering = false;
    dropIndicatorIndex = -1;

    document.addEventListener("mousemove", handleTabMouseMove);
    document.addEventListener("mouseup", handleTabMouseUp);

    event.preventDefault();
  }

  function handleTabMouseMove(event: MouseEvent) {
    if (!draggingTabId) return;

    const deltaX = Math.abs(event.clientX - dragStartX);
    const deltaY = Math.abs(event.clientY - dragStartY);
    const hasMoved = deltaX > 5 || deltaY > 5;

    if (!hasMoved) return;

    // Check if cursor is within tab bar bounds
    const tabBarRect = tabBarElement?.getBoundingClientRect();
    let isInsideTabBar = false;
    if (tabBarRect) {
      if (isVertical) {
        isInsideTabBar =
          event.clientY >= tabBarRect.top &&
          event.clientY <= tabBarRect.bottom &&
          event.clientX >= tabBarRect.left - 20 &&
          event.clientX <= tabBarRect.right + 20;
      } else {
        isInsideTabBar =
          event.clientX >= tabBarRect.left &&
          event.clientX <= tabBarRect.right &&
          event.clientY >= tabBarRect.top - 20 &&
          event.clientY <= tabBarRect.bottom + 20;
      }
    }

    if (reorderable && isInsideTabBar && !isDraggingOut) {
      // Reordering mode
      isReordering = true;
      updateDropIndicator(isVertical ? event.clientY : event.clientX);
    } else if (draggable) {
      // Dragging out mode
      if (!isDraggingOut) {
        isDraggingOut = true;
        isReordering = false;
        dropIndicatorIndex = -1;
        dispatch("tabdragstart", {
          tabId: draggingTabId,
          x: event.clientX,
          y: event.clientY,
        });
      }
      dispatch("tabdragmove", {
        tabId: draggingTabId,
        x: event.clientX,
        y: event.clientY,
      });
    }
  }

  function updateDropIndicator(clientPos: number) {
    if (!reorderTabId) return;

    const currentIndex = tabs.findIndex((t) => t.id === reorderTabId);
    let newIndex = tabs.length;

    // Find the tab position based on cursor position
    for (let i = 0; i < tabs.length; i++) {
      const tabEl = tabElements.get(tabs[i].id);
      if (!tabEl) continue;

      const rect = tabEl.getBoundingClientRect();
      const midPos = isVertical
        ? rect.top + rect.height / 2
        : rect.left + rect.width / 2;

      if (clientPos < midPos) {
        newIndex = i;
        break;
      }
    }

    // Adjust index if dropping after current position
    if (newIndex > currentIndex) {
      dropIndicatorIndex = newIndex;
    } else {
      dropIndicatorIndex = newIndex;
    }
  }

  function handleTabMouseUp() {
    document.removeEventListener("mousemove", handleTabMouseMove);
    document.removeEventListener("mouseup", handleTabMouseUp);

    if (isDraggingOut && draggingTabId) {
      dispatch("tabdragend", { tabId: draggingTabId });
    } else if (isReordering && reorderTabId && dropIndicatorIndex !== -1) {
      const currentIndex = tabs.findIndex((t) => t.id === reorderTabId);
      if (
        currentIndex !== -1 &&
        currentIndex !== dropIndicatorIndex &&
        currentIndex !== dropIndicatorIndex - 1
      ) {
        // Reorder tabs
        const newTabs = [...tabs];
        const [movedTab] = newTabs.splice(currentIndex, 1);
        const insertIndex =
          dropIndicatorIndex > currentIndex
            ? dropIndicatorIndex - 1
            : dropIndicatorIndex;
        newTabs.splice(insertIndex, 0, movedTab);
        dispatch("reorder", { tabs: newTabs });
      }
    } else if (draggingTabId && !isDraggingOut && !isReordering) {
      // Simple click without drag - select the tab
      selectTab(draggingTabId);
    }

    draggingTabId = null;
    reorderTabId = null;
    isDraggingOut = false;
    isReordering = false;
    dropIndicatorIndex = -1;
  }

  function registerTabElement(element: HTMLElement, tabId: string) {
    tabElements.set(tabId, element);
    return {
      destroy() {
        tabElements.delete(tabId);
      },
    };
  }

  onDestroy(() => {
    document.removeEventListener("mousemove", handleTabMouseMove);
    document.removeEventListener("mouseup", handleTabMouseUp);
  });
</script>

<div
  class="tabs-widget"
  class:vertical={isVertical}
  class:position-left={tabPosition === "left"}
  class:position-right={tabPosition === "right"}
>
  {#if showTabBar}
    <div class="tabs-bar" bind:this={tabBarElement}>
      {#each tabs as tab, index (tab.id)}
        {#if isReordering && dropIndicatorIndex === index}
          <div class="drop-indicator"></div>
        {/if}
        <button
          class="tabs-button"
          class:active={activeTabId === tab.id}
          class:dragging={(draggingTabId === tab.id && isDraggingOut) ||
            (reorderTabId === tab.id && isReordering)}
          use:registerTabElement={tab.id}
          on:click={() => selectTab(tab.id)}
          on:mousedown={(e) => handleTabMouseDown(e, tab.id)}
        >
          <span class="tabs-title">{tab.title}</span>
        </button>
      {/each}
      {#if isReordering && dropIndicatorIndex === tabs.length}
        <div class="drop-indicator"></div>
      {/if}
    </div>
  {/if}

  <div class="tabs-content">
    <slot {activeTabId} />
  </div>
</div>

<style>
  .tabs-widget {
    --tab-border-color: #dadada;
    --tab-bg: #ffffff;
    --tab-active-bg: #317ae7;
    --tab-active-color: #ffffff;
    --tab-content-bg: #e8e8e8;

    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
  }

  /* Vertical layout */
  .tabs-widget.vertical {
    flex-direction: row;
  }

  .tabs-widget.vertical.position-right {
    flex-direction: row-reverse;
  }

  /* Tab bar */
  .tabs-bar {
    display: flex;
    justify-content: center;
    flex-shrink: 0;
    border-bottom: 1px solid var(--tab-border-color);
  }

  .tabs-widget.vertical .tabs-bar {
    flex-direction: column;
    border-bottom: none;
    border-right: 1px solid var(--tab-border-color);
  }

  .tabs-widget.vertical.position-right .tabs-bar {
    border-right: none;
    border-left: 1px solid var(--tab-border-color);
  }

  /* Tab button - horizontal */
  .tabs-button {
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 70px;
    height: 22px;
    padding: 0 10px;
    border: none;
    border-left: 1px solid var(--tab-border-color);
    border-radius: 0;
    color: inherit;
    font: inherit;
    background: var(--tab-bg);
    cursor: pointer;
    transition:
      background-color 0.15s,
      color 0.15s;
  }

  /* Tab button - vertical */
  .tabs-widget.vertical .tabs-button {
    min-width: unset;
    width: 22px;
    min-height: 70px;
    height: auto;
    padding: 10px 0;
    border-left: none;
    border-top: 1px solid var(--tab-border-color);
  }

  /* Tab title */
  .tabs-title {
    white-space: nowrap;
    color: inherit;
  }

  .tabs-widget.vertical .tabs-title {
    writing-mode: vertical-rl;
    text-orientation: mixed;
  }

  .tabs-widget.vertical.position-left .tabs-title {
    transform: rotate(180deg);
  }

  /* Separator logic - horizontal */
  .tabs-button:first-child,
  .tabs-button.active,
  .tabs-button.active + .tabs-button {
    border-left-color: transparent;
  }

  /* Separator logic - vertical */
  .tabs-widget.vertical .tabs-button:first-child,
  .tabs-widget.vertical .tabs-button.active,
  .tabs-widget.vertical .tabs-button.active + .tabs-button {
    border-left: none;
    border-top-color: transparent;
  }

  .tabs-button:hover:not(.active) {
    background: color-mix(in srgb, var(--tab-active-bg) 15%, var(--tab-bg));
  }

  .tabs-button.active {
    color: var(--tab-active-color);
    background: var(--tab-active-bg);
  }

  .tabs-button.dragging {
    opacity: 0.5;
  }

  /* Drop indicator - horizontal */
  .drop-indicator {
    width: 2px;
    height: 16px;
    background-color: var(--tab-active-bg);
    margin: 3px 0;
    flex-shrink: 0;
  }

  /* Drop indicator - vertical */
  .tabs-widget.vertical .drop-indicator {
    width: 16px;
    height: 2px;
    margin: 0 3px;
  }

  /* Tab content */
  .tabs-content {
    flex: 1;
    min-height: 0;
    min-width: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: var(--tab-content-bg);
  }

  .tabs-content > :global(*) {
    flex: 1;
    min-height: 0;
    min-width: 0;
  }
</style>
