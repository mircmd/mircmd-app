<!--
  @component Tabs

  Tab widget component for switching between content panels.
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
  - `activeTabId: string` - ID of currently active tab (bindable)
  - `hideSingleTab: boolean` - Hide tab bar when only one tab exists (default: true)
  - `draggable: boolean` - Enable dragging tabs out of widget (default: false)
  - `reorderable: boolean` - Enable tab reordering (default: false)
  - `tabPosition: TabPosition` - Position of tab bar: "top" | "left" | "right" (default: "top")
  - `onchange: (tabId: string) => void` - Callback when active tab changes
  - `onreorder: (tabs: Tab[]) => void` - Callback when tabs are reordered
  - `ontabdragstart: (data: TabDragEvent) => void` - Callback when tab drag starts
  - `ontabdragmove: (data: TabDragEvent) => void` - Callback during tab drag
  - `ontabdragend: (data: { tabId: string }) => void` - Callback when tab drag ends

  ## Slots
  - children - Content area, rendered via snippet with `activeTabId` parameter
-->
<script lang="ts" module>
  export interface Tab {
    id: string;
    title: string;
  }

  export type TabPosition = "top" | "left" | "right";

  export interface TabDragEvent {
    tabId: string;
    x: number;
    y: number;
  }
</script>

<script lang="ts">
  import { onDestroy, type Snippet } from "svelte";

  interface Props {
    tabs: Tab[];
    activeTabId?: string;
    hideSingleTab?: boolean;
    draggable?: boolean;
    reorderable?: boolean;
    tabPosition?: TabPosition;
    onchange?: (tabId: string) => void;
    onreorder?: (tabs: Tab[]) => void;
    ontabdragstart?: (data: TabDragEvent) => void;
    ontabdragmove?: (data: TabDragEvent) => void;
    ontabdragend?: (data: { tabId: string }) => void;
    children?: Snippet<[string]>;
  }

  let {
    tabs = [],
    activeTabId = $bindable(""),
    hideSingleTab = true,
    draggable = false,
    reorderable = false,
    tabPosition = "top",
    onchange,
    onreorder,
    ontabdragstart,
    ontabdragmove,
    ontabdragend,
    children,
  }: Props = $props();

  // Derived state
  let showTabBar = $derived(!(hideSingleTab && tabs.length === 1));
  let isVertical = $derived(tabPosition === "left" || tabPosition === "right");

  // Auto-select first tab if current is invalid
  $effect(() => {
    if (tabs.length > 0 && !tabs.some((t) => t.id === activeTabId)) {
      activeTabId = tabs[0].id;
    }
  });

  // Interaction state
  let draggingTabId: string | null = $state(null);
  let dragStartX = $state(0);
  let dragStartY = $state(0);
  let isDraggingOut = $state(false);
  let isReordering = $state(false);
  let reorderTabId: string | null = $state(null);
  let dropIndicatorIndex = $state(-1);
  let tabBarElement: HTMLElement | undefined = $state();
  let tabElements = new Map<string, HTMLElement>();

  function selectTab(tabId: string): void {
    if (activeTabId !== tabId) {
      activeTabId = tabId;
      onchange?.(tabId);
    }
  }

  function handleTabMouseDown(event: MouseEvent, tabId: string): void {
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

  function handleTabMouseMove(event: MouseEvent): void {
    if (!draggingTabId) return;

    const deltaX = Math.abs(event.clientX - dragStartX);
    const deltaY = Math.abs(event.clientY - dragStartY);
    const hasMoved = deltaX > 5 || deltaY > 5;

    if (!hasMoved) return;

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
      isReordering = true;
      updateDropIndicator(isVertical ? event.clientY : event.clientX);
    } else if (draggable) {
      if (!isDraggingOut) {
        isDraggingOut = true;
        isReordering = false;
        dropIndicatorIndex = -1;
        ontabdragstart?.({
          tabId: draggingTabId,
          x: event.clientX,
          y: event.clientY,
        });
      }
      ontabdragmove?.({
        tabId: draggingTabId,
        x: event.clientX,
        y: event.clientY,
      });
    }
  }

  function updateDropIndicator(clientPos: number): void {
    if (!reorderTabId) return;

    const currentIndex = tabs.findIndex((t) => t.id === reorderTabId);
    let newIndex = tabs.length;

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

    dropIndicatorIndex = newIndex > currentIndex ? newIndex : newIndex;
  }

  function handleTabMouseUp(): void {
    document.removeEventListener("mousemove", handleTabMouseMove);
    document.removeEventListener("mouseup", handleTabMouseUp);

    if (isDraggingOut && draggingTabId) {
      ontabdragend?.({ tabId: draggingTabId });
    } else if (isReordering && reorderTabId && dropIndicatorIndex !== -1) {
      const currentIndex = tabs.findIndex((t) => t.id === reorderTabId);
      if (
        currentIndex !== -1 &&
        currentIndex !== dropIndicatorIndex &&
        currentIndex !== dropIndicatorIndex - 1
      ) {
        const newTabs = [...tabs];
        const [movedTab] = newTabs.splice(currentIndex, 1);
        const insertIndex =
          dropIndicatorIndex > currentIndex
            ? dropIndicatorIndex - 1
            : dropIndicatorIndex;
        newTabs.splice(insertIndex, 0, movedTab);
        onreorder?.(newTabs);
      }
    } else if (draggingTabId && !isDraggingOut && !isReordering) {
      selectTab(draggingTabId);
    }

    draggingTabId = null;
    reorderTabId = null;
    isDraggingOut = false;
    isReordering = false;
    dropIndicatorIndex = -1;
  }

  function registerTabElement(
    element: HTMLElement,
    tabId: string
  ): { destroy: () => void } {
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
          onclick={() => selectTab(tab.id)}
          onmousedown={(e) => handleTabMouseDown(e, tab.id)}
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
    {#if children}
      {@render children(activeTabId)}
    {/if}
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

  .tabs-widget.vertical {
    flex-direction: row;
  }

  .tabs-widget.vertical.position-right {
    flex-direction: row-reverse;
  }

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

  .tabs-widget.vertical .tabs-button {
    min-width: unset;
    width: 22px;
    min-height: 70px;
    height: auto;
    padding: 10px 0;
    border-left: none;
    border-top: 1px solid var(--tab-border-color);
  }

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

  .tabs-button:first-child,
  .tabs-button.active,
  .tabs-button.active + .tabs-button {
    border-left-color: transparent;
  }

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

  .drop-indicator {
    width: 2px;
    height: 16px;
    background-color: var(--tab-active-bg);
    margin: 3px 0;
    flex-shrink: 0;
  }

  .tabs-widget.vertical .drop-indicator {
    width: 16px;
    height: 2px;
    margin: 0 3px;
  }

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
