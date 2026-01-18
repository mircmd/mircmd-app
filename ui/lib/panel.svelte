<!--
  @component Panel

  Panel widget component for dockable panel content.
  Represents a single dockable panel with optional title bar and drag-out capability.

  ## Features
  - Optional title bar with text label
  - Draggable title bar for undocking
  - Floating mode during drag operations
  - Position-aware styling (left/right/bottom)
  - Visibility toggle support

  ## Props
  - `position: "left" | "right" | "bottom"` - Panel area position (default: "left")
  - `title: string` - Title bar text (default: "")
  - `visible: boolean` - Visibility state (default: true)
  - `movable: boolean` - Enable drag-to-undock (default: true)
  - `showTitle: boolean` - Show title bar (default: true)

  ## Events
  - `undock` - Fired when panel starts floating: `{ x: number, y: number }`
  - `dragmove` - Fired during floating drag: `{ x: number, y: number }`
  - `dragend` - Fired when floating drag ends

  ## Slots
  - default - Content of the panel

  ## Usage Example
  ```svelte
  <Panel
    position="left"
    title="Project Explorer"
    on:undock={(e) => handleUndock(e.detail)}
  >
    <Tree nodes={projectNodes} />
  </Panel>
  ```
-->
<script lang="ts">
  import { createEventDispatcher, onDestroy } from "svelte";

  export let position: "left" | "right" | "bottom" = "left";
  export let title: string = "";
  export let visible: boolean = true;
  export let movable: boolean = true;
  export let showTitle: boolean = true;

  const dispatch = createEventDispatcher();

  let isDragging = false;
  let isFloating = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let floatingX = 0;
  let floatingY = 0;

  function handleDragStart(event: MouseEvent) {
    if (!movable) return;

    isDragging = true;
    dragStartX = event.clientX;
    dragStartY = event.clientY;

    event.preventDefault();
  }

  function handleDragMove(event: MouseEvent) {
    if (!isDragging) return;

    const deltaX = event.clientX - dragStartX;
    const deltaY = event.clientY - dragStartY;

    // Start floating mode if moved more than 10px
    if (!isFloating && (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10)) {
      isFloating = true;
      floatingX = event.clientX;
      floatingY = event.clientY;
      dispatch("undock", { x: event.clientX, y: event.clientY });
    }

    if (isFloating) {
      floatingX = event.clientX;
      floatingY = event.clientY;
      dispatch("dragmove", { x: event.clientX, y: event.clientY });
    }
  }

  function handleDragEnd() {
    if (!isDragging) return;

    isDragging = false;

    if (isFloating) {
      dispatch("dragend");
      isFloating = false;
    }
  }

  function addDragListeners() {
    document.addEventListener("mousemove", handleDragMove);
    document.addEventListener("mouseup", handleDragEnd);
  }

  function removeDragListeners() {
    document.removeEventListener("mousemove", handleDragMove);
    document.removeEventListener("mouseup", handleDragEnd);
  }

  $: {
    if (isDragging) {
      addDragListeners();
    } else {
      removeDragListeners();
    }
  }

  onDestroy(() => {
    removeDragListeners();
  });

  $: floatingStyle = isFloating
    ? `position: fixed; left: ${floatingX - 100}px; top: ${floatingY - 10}px; width: 200px; height: 150px; z-index: 10000; box-shadow: 0 4px 12px rgba(0,0,0,0.3);`
    : "";
</script>

{#if visible}
  <div
    class="panel-widget panel-{position}"
    class:floating={isFloating}
    style={floatingStyle}
  >
    {#if showTitle && title}
      <div
        class="panel-title disable-selection background"
        class:draggable={movable}
        on:mousedown={handleDragStart}
        role="button"
        tabindex="0"
      >
        <span class="title-text">{title}</span>
      </div>
    {/if}

    <div class="panel-content background">
      <slot />
    </div>
  </div>
{/if}

<style>
  .panel-widget {
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    position: relative;
    box-sizing: border-box;
  }

  .panel-title {
    display: flex;
    align-items: center;
    padding: 5px 10px;
    border-bottom: 1px solid #dadada;
    height: 22px;
    box-sizing: border-box;
    overflow: hidden;
    min-width: 0;
  }

  .panel-title.draggable {
    cursor: move;
    user-select: none;
  }

  .panel-title.draggable:active {
    background-color: #dadada;
  }

  .title-text {
    font-size: 11px;
    color: #000000df;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .floating {
    border: 2px solid #317ae7 !important;
    opacity: 0.9;
  }

  .panel-content {
    flex: 1;
    overflow: auto;
    min-height: 0;
    min-width: 0;
  }
</style>
