<!--
  @component Workspace

  Main workspace layout shell with dock areas on left, right, and bottom.
  Dock content is provided by the consumer via snippets.

  ## Layout Structure
  ```
  ┌───────┬─────────────────┬───────┐
  │       │                 │       │
  │       │     MAIN        │       │
  │ LEFT  │    CONTENT      │ RIGHT │
  │       │                 │       │
  │       ├─────────────────┤       │
  │       │    BOTTOM       │       │
  └───────┴─────────────────┴───────┘
  ```
-->
<script lang="ts" module>
  export type DockArea = "left" | "right" | "bottom";

  export const DEFAULT_DOCK_SIZES: Record<DockArea, number> = {
    left: 200,
    right: 200,
    bottom: 200,
  };
</script>

<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    centralContent: Snippet;
    left?: Snippet;
    right?: Snippet;
    bottom?: Snippet;
    /** Collapse dock when true (default true). Host typically drives from content emptiness. */
    leftEmpty?: boolean;
    rightEmpty?: boolean;
    bottomEmpty?: boolean;
    /** When omitted, uses {@link DEFAULT_DOCK_SIZES} (200px each). */
    dockSizes?: Record<DockArea, number>;
    onDockSizeChange?: (area: DockArea, size: number) => void;
  }

  let {
    centralContent,
    left,
    right,
    bottom,
    leftEmpty = true,
    rightEmpty = true,
    bottomEmpty = true,
    dockSizes: dockSizesProp,
    onDockSizeChange,
  }: Props = $props();

  let localDockSizes = $state<Record<DockArea, number>>({ ...DEFAULT_DOCK_SIZES });
  let dockSizes = $derived(dockSizesProp ?? localDockSizes);

  let isLeftCollapsed = $derived(leftEmpty || left == null);
  let isRightCollapsed = $derived(rightEmpty || right == null);
  let isBottomCollapsed = $derived(bottomEmpty || bottom == null);

  function applyDockSize(area: DockArea, size: number): void {
    onDockSizeChange?.(area, size);
    if (dockSizesProp === undefined) {
      localDockSizes = { ...localDockSizes, [area]: size };
    }
  }

  let resizeOffset = { x: 0, y: 0 };

  let resizingArea = $state<DockArea | null>(null);
  let isInteracting = $derived(resizingArea !== null);

  $effect(() => {
    if (isInteracting) {
      attachGlobalListeners();
    } else {
      detachGlobalListeners();
    }
  });

  // Global event listeners management
  let listenersAttached = false;

  function attachGlobalListeners(): void {
    if (listenersAttached) return;
    document.addEventListener("mousemove", onGlobalMouseMove);
    document.addEventListener("mouseup", onGlobalMouseUp);
    listenersAttached = true;
  }

  function detachGlobalListeners(): void {
    if (!listenersAttached) return;
    document.removeEventListener("mousemove", onGlobalMouseMove);
    document.removeEventListener("mouseup", onGlobalMouseUp);
    listenersAttached = false;
  }

  // Global mouse event handlers
  function onGlobalMouseMove(event: MouseEvent): void {
    const posX = event.clientX - resizeOffset.x;
    const posY = event.clientY - resizeOffset.y;
    resizeOffset = {
      x: event.clientX,
      y: event.clientY,
    };
    if (resizingArea === "left") {
      applyDockSize("left", dockSizes.left + posX);
    } else if (resizingArea === "right") {
      applyDockSize("right", dockSizes.right - posX);
    } else if (resizingArea === "bottom") {
      applyDockSize("bottom", dockSizes.bottom - posY);
    }
  }

  function onGlobalMouseUp(): void {
    resizingArea = null;
  }

  function startResizing(event: MouseEvent, area: DockArea) {
    event.preventDefault();
    if (event.button !== 0) return;

    resizingArea = area;
    resizeOffset = {
      x: event.clientX,
      y: event.clientY,
    };
  }
</script>

<div
  class="workspace"
  style:--left-width={isLeftCollapsed ? "0px" : dockSizes.left + "px"}
  style:--right-width={isRightCollapsed ? "0px" : dockSizes.right + "px"}
  style:--bottom-height={isBottomCollapsed ? "0px" : dockSizes.bottom + "px"}
>
  <div class="left-dock" class:hidden={isLeftCollapsed}>
    {@render left?.()}
    <div
      class="resize-handle resize-handle-vertical"
      class:resizing={resizingArea === "left"}
      onmousedown={(e) => startResizing(e, "left")}
      aria-hidden="true"
    ></div>
  </div>
  <div class="central-content">
    {@render centralContent()}
  </div>
  <div class="bottom-dock" class:hidden={isBottomCollapsed}>
    <div
      class="resize-handle resize-handle-horizontal"
      class:resizing={resizingArea === "bottom"}
      onmousedown={(e) => startResizing(e, "bottom")}
      aria-hidden="true"
    ></div>
    {@render bottom?.()}
  </div>
  <div class="right-dock" class:hidden={isRightCollapsed}>
    <div
      class="resize-handle resize-handle-vertical"
      class:resizing={resizingArea === "right"}
      onmousedown={(e) => startResizing(e, "right")}
      aria-hidden="true"
    ></div>
    {@render right?.()}
  </div>
</div>

<style>
  .workspace {
    display: grid;
    grid-template-columns: var(--left-width) 1fr var(--right-width);
    grid-template-rows: 1fr var(--bottom-height);
    grid-template-areas:
      "left central right"
      "left bottom right";
    flex: 1;
    min-height: 0;
    min-width: 0;
    position: relative;
  }

  .left-dock {
    grid-area: left;
    overflow: hidden;
    border-right: 1px solid #dadada;
    z-index: 3;
  }

  .right-dock {
    grid-area: right;
    overflow: hidden;
    border-left: 1px solid #dadada;
    z-index: 3;
  }

  .bottom-dock {
    grid-area: bottom;
    overflow: hidden;
    border-top: 1px solid #dadada;
    z-index: 2;
  }

  .central-content {
    grid-area: central;
    overflow: auto;
    background-color: #ffffff;
    min-width: 0;
    min-height: 0;
  }

  .resize-handle {
    position: absolute;
    z-index: 1;
    background: transparent;
  }

  .resize-handle:hover,
  .resize-handle.resizing {
    background-color: #3b82f6;
    transition: background-color 0.25s ease;
  }

  .resize-handle-vertical {
    top: 0;
    bottom: 0;
    width: 4px;
    cursor: col-resize;
  }

  .resize-handle-horizontal {
    left: 0;
    right: 0;
    height: 4px;
    cursor: row-resize;
  }

  .left-dock .resize-handle {
    right: calc(100% - var(--left-width));
    transform: translateX(2px);
  }

  .right-dock .resize-handle {
    left: calc(100% - var(--right-width));
    transform: translateX(-2px);
  }

  .bottom-dock .resize-handle {
    top: calc(100% - var(--bottom-height));
    transform: translateY(-2px);
  }
</style>
