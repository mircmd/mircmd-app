<!--
  @component Panel

  Panel widget component for dockable panel content within Workspace.
  Represents a single dockable panel with optional title bar and drag-out capability.

  ## Features
  - Optional title bar with text label
  - Draggable title bar for undocking
  - Floating mode during drag operations
  - Visibility toggle support

  ## Props
  - `title: string` - Title bar text (default: "")
  - `visible: boolean` - Visibility state (default: true)
  - `movable: boolean` - Enable drag-to-undock (default: true)
  - `showTitle: boolean` - Show title bar (default: true)
  - `onundock: (position: { x: number, y: number }) => void` - Callback when panel starts floating
  - `ondragmove: (position: { x: number, y: number }) => void` - Callback during floating drag
  - `ondragend: () => void` - Callback when floating drag ends

  ## Slots
  - children - Content of the panel
-->
<script lang="ts">
  import { onDestroy, type Snippet } from "svelte";

  interface DragPosition {
    x: number;
    y: number;
  }

  interface Props {
    title?: string;
    visible?: boolean;
    movable?: boolean;
    showTitle?: boolean;
    onundock?: (position: DragPosition) => void;
    ondragmove?: (position: DragPosition) => void;
    ondragend?: () => void;
    children?: Snippet;
  }

  let {
    title = "",
    visible = true,
    movable = true,
    showTitle = true,
    onundock,
    ondragmove,
    ondragend,
    children,
  }: Props = $props();

  let isDragging = $state(false);
  let isFloating = $state(false);
  let dragStartX = $state(0);
  let dragStartY = $state(0);
  let floatingX = $state(0);
  let floatingY = $state(0);

  function handleDragStart(event: MouseEvent): void {
    if (!movable) return;

    isDragging = true;
    dragStartX = event.clientX;
    dragStartY = event.clientY;

    document.addEventListener("mousemove", handleDragMove);
    document.addEventListener("mouseup", handleDragEnd);

    event.preventDefault();
  }

  function handleDragMove(event: MouseEvent): void {
    if (!isDragging) return;

    const deltaX = event.clientX - dragStartX;
    const deltaY = event.clientY - dragStartY;

    if (!isFloating && (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10)) {
      isFloating = true;
      floatingX = event.clientX;
      floatingY = event.clientY;
      onundock?.({ x: event.clientX, y: event.clientY });
    }

    if (isFloating) {
      floatingX = event.clientX;
      floatingY = event.clientY;
      ondragmove?.({ x: event.clientX, y: event.clientY });
    }
  }

  function handleDragEnd(): void {
    document.removeEventListener("mousemove", handleDragMove);
    document.removeEventListener("mouseup", handleDragEnd);

    if (!isDragging) return;

    isDragging = false;

    if (isFloating) {
      ondragend?.();
      isFloating = false;
    }
  }

  onDestroy(() => {
    document.removeEventListener("mousemove", handleDragMove);
    document.removeEventListener("mouseup", handleDragEnd);
  });

  let floatingStyle = $derived(
    isFloating
      ? `position: fixed; left: ${floatingX - 100}px; top: ${floatingY - 10}px; width: 200px; height: 150px; z-index: 10000; box-shadow: 0 4px 12px rgba(0,0,0,0.3);`
      : ""
  );
</script>

{#if visible}
  <div class="panel-widget" class:floating={isFloating} style={floatingStyle}>
    {#if showTitle && title}
      <div
        class="panel-title disable-selection background"
        class:draggable={movable}
        onmousedown={handleDragStart}
        role="button"
        tabindex="0"
      >
        <span class="title-text">{title}</span>
      </div>
    {/if}

    <div class="panel-content background">
      {#if children}
        {@render children()}
      {/if}
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
