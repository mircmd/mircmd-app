<!--
  @component Workspace

  Main workspace layout component with dock panels.
  Provides a flexible layout system with dock areas on left, right, and bottom sides.

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
<script lang="ts">
  import type { Snippet } from "svelte";
  import Layout from "./Layout.svelte";

  interface Props {
    centralContent: Snippet;
  }

  let { centralContent }: Props = $props();

  let leftDock: ReturnType<typeof Layout> = $state()!;
  let rightDock: ReturnType<typeof Layout> = $state()!;
  let bottomDock: ReturnType<typeof Layout> = $state()!;
  let isLeftEmpty = $state(true);
  let isRightEmpty = $state(true);
  let isBottomEmpty = $state(true);
  let leftWidth = $state(200);
  let rightWidth = $state(200);
  let bottomHeight = $state(150);

  export function addWidgetToDock(area: "left" | "right" | "bottom", content: Snippet) {
    if (area === "left") leftDock.addWidget(content);
    else if (area === "right") rightDock.addWidget(content);
    else if (area === "bottom") bottomDock.addWidget(content);
  }

  let resizeOffset = { x: 0, y: 0 };

  let resizingArea = $state<"left" | "right" | "bottom" | null>(null);
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
      leftWidth += posX;
    } else if (resizingArea === "right") {
      rightWidth -= posX;
    } else if (resizingArea === "bottom") {
      bottomHeight -= posY;
    }
  }

  function onGlobalMouseUp(): void {
    resizingArea = null;
  }

  function startResizing(event: MouseEvent, area: "left" | "right" | "bottom") {
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
  style:--left-width={isLeftEmpty ? "0px" : leftWidth + "px"}
  style:--right-width={isRightEmpty ? "0px" : rightWidth + "px"}
  style:--bottom-height={isBottomEmpty ? "0px" : bottomHeight + "px"}
>
  <div class="left-dock" class:hidden={isLeftEmpty}>
    <Layout bind:this={leftDock} bind:isEmpty={isLeftEmpty} orientation="vertical" />
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
  <div class="bottom-dock" class:hidden={isBottomEmpty}>
    <div
      class="resize-handle resize-handle-horizontal"
      class:resizing={resizingArea === "bottom"}
      onmousedown={(e) => startResizing(e, "bottom")}
      aria-hidden="true"
    ></div>
    <Layout bind:this={bottomDock} bind:isEmpty={isBottomEmpty} orientation="horizontal" />
  </div>
  <div class="right-dock" class:hidden={isRightEmpty}>
    <div
      class="resize-handle resize-handle-vertical"
      class:resizing={resizingArea === "right"}
      onmousedown={(e) => startResizing(e, "right")}
      aria-hidden="true"
    ></div>
    <Layout bind:this={rightDock} bind:isEmpty={isRightEmpty} orientation="vertical" />
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
