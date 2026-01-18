<!--
  @component SubWindow

  Individual sub-window component.
  Represents a single sub-window within a window manager area with title bar and window controls.

  ## Features
  - Title bar with window title and optional icon
  - Window control buttons: minimize, maximize/restore, close
  - Draggable by title bar (in normal state)
  - Resizable from all 8 directions via resize handles
  - Window states: normal, minimized, maximized
  - Double-click title bar to maximize/restore
  - Visual styling with shadow and rounded corners
  - Minimize button icon rotates to indicate restore action
  - Maximize button shows different icon based on state

  ## Props
  - `window: WindowData` - Window data object (see Types below)
  - `offsetX: number` - Horizontal offset for scroll compensation (default: 0)
  - `offsetY: number` - Vertical offset for scroll compensation (default: 0)

  ## Events
  - `close` - Fired when close button is clicked
  - `minimize` - Fired when minimize button is clicked
  - `maximize` - Fired when maximize button is clicked or title bar double-clicked
  - `focus` - Fired when window is clicked
  - `dragstart` - Fired when drag starts: `{ clientX: number, clientY: number }`
  - `resizestart` - Fired when resize starts: `{ clientX: number, clientY: number, direction: ResizeDirection }`

  ## Slots
  - default - Content of the window

  ## Types
  ```typescript
  type WindowState = "normal" | "minimized" | "maximized";

  interface WindowData {
    id: string;          // Unique window identifier
    title: string;       // Window title text
    icon?: string;       // Optional icon URL for title bar
    x: number;           // Horizontal position (px)
    y: number;           // Vertical position (px)
    width: number;       // Window width (px)
    height: number;      // Window height (px)
    zIndex: number;      // Stacking order
    state?: WindowState; // Window state (default: "normal")
  }

  type ResizeDirection = "n" | "s" | "e" | "w" | "ne" | "nw" | "se" | "sw";
  ```

  ## Usage Example
  ```svelte
  <SubWindow
    window={{
      id: "editor",
      title: "Document Editor",
      icon: "/icons/edit.svg",
      x: 100,
      y: 50,
      width: 600,
      height: 400,
      zIndex: 1,
      state: "normal"
    }}
    on:close={handleClose}
    on:maximize={handleMaximize}
  >
    <EditorContent />
  </SubWindow>
  ```
-->
<script context="module" lang="ts">
  export type WindowState = "normal" | "minimized" | "maximized";

  export interface WindowData {
    id: string;
    title: string;
    icon?: string;
    x: number;
    y: number;
    width: number;
    height: number;
    zIndex: number;
    state?: WindowState;
  }

  export type ResizeDirection =
    | "n"
    | "s"
    | "e"
    | "w"
    | "ne"
    | "nw"
    | "se"
    | "sw";
</script>

<script lang="ts">
  import { createEventDispatcher } from "svelte";

  import arrowDownIcon from "../../assets/icons/arrow_down.svg";
  import closeIcon from "../../assets/icons/close.svg";
  import squareEmptyIcon from "../../assets/icons/square_empty.svg";
  import squareFilledIcon from "../../assets/icons/square_filled.svg";

  export let window: WindowData;
  export let offsetX: number = 0;
  export let offsetY: number = 0;

  const dispatch = createEventDispatcher<{
    close: void;
    minimize: void;
    maximize: void;
    focus: void;
    dragstart: { clientX: number; clientY: number };
    resizestart: {
      clientX: number;
      clientY: number;
      direction: ResizeDirection;
    };
  }>();

  // Derived state from window.state
  $: windowState = window.state ?? "normal";
  $: isNormal = windowState === "normal";
  $: isMinimized = windowState === "minimized";
  $: isMaximized = windowState === "maximized";

  // Event handlers
  function onTitleBarMouseDown(event: MouseEvent) {
    if (isMaximized) return;
    event.preventDefault();
    dispatch("dragstart", { clientX: event.clientX, clientY: event.clientY });
  }

  function onResizeHandleMouseDown(
    event: MouseEvent,
    direction: ResizeDirection
  ) {
    event.preventDefault();
    event.stopPropagation();
    dispatch("resizestart", {
      clientX: event.clientX,
      clientY: event.clientY,
      direction,
    });
  }

  function onWindowMouseDown() {
    dispatch("focus");
  }

  function onClose() {
    dispatch("close");
  }

  function onMinimize() {
    dispatch("minimize");
  }

  function onMaximize() {
    dispatch("maximize");
  }
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
  class="sub-window"
  class:minimized={isMinimized}
  class:maximized={isMaximized}
  style:z-index={window.zIndex}
  style:left={isMaximized ? null : `${window.x + offsetX}px`}
  style:top={isMaximized ? null : `${window.y + offsetY}px`}
  style:width={isMaximized ? null : `${window.width}px`}
  style:height={isMaximized || isMinimized ? null : `${window.height}px`}
  on:mousedown={onWindowMouseDown}
>
  <!-- Title bar -->
  <div
    class="sub-window-title-bar"
    on:mousedown={onTitleBarMouseDown}
    on:dblclick|stopPropagation={onMaximize}
    role="button"
    tabindex="0"
  >
    <div class="sub-window-icon-container">
      {#if window.icon}
        <img src={window.icon} alt="" class="sub-window-icon" />
      {/if}
    </div>
    <span class="sub-window-title disable-selection">{window.title}</span>
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="sub-window-buttons" on:dblclick|stopPropagation>
      <button
        class="sub-window-btn minimize"
        on:click|stopPropagation={onMinimize}
        aria-label={isMinimized ? "Restore window" : "Minimize window"}
      >
        <img
          src={arrowDownIcon}
          alt={isMinimized ? "Restore" : "Minimize"}
          class="sub-window-btn-icon"
          class:rotated={isMinimized}
        />
      </button>
      <button
        class="sub-window-btn maximize"
        on:click|stopPropagation={onMaximize}
        aria-label={isMaximized ? "Restore window" : "Maximize window"}
      >
        <img
          src={isMaximized ? squareFilledIcon : squareEmptyIcon}
          alt={isMaximized ? "Restore" : "Maximize"}
          class="sub-window-btn-icon"
        />
      </button>
      <button
        class="sub-window-btn close"
        on:click|stopPropagation={onClose}
        aria-label="Close window"
      >
        <img src={closeIcon} alt="Close" class="sub-window-btn-icon" />
      </button>
    </div>
  </div>

  <!-- Content area (hidden when minimized) -->
  {#if !isMinimized}
    <div class="sub-window-content">
      <slot>
        <p>Window content</p>
      </slot>
    </div>
  {/if}

  <!-- Resize handles (only in normal state) -->
  {#if isNormal}
    {#each ["n", "s", "e", "w", "ne", "nw", "se", "sw"] as dir (dir)}
      <div
        class="resize-handle resize-{dir}"
        on:mousedown={(e) => onResizeHandleMouseDown(e, dir as ResizeDirection)}
        role="button"
        tabindex="-1"
        aria-label="Resize {dir}"
      ></div>
    {/each}
  {/if}
</div>

<style>
  .sub-window {
    --title-bar-height: 28px;
    --minimized-width: 230px;

    position: absolute;
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    border: 1px solid #a0a0a0;
    box-shadow:
      0 16px 48px rgba(0, 0, 0, 0.25),
      0 8px 16px rgba(0, 0, 0, 0.15);
    border-radius: 8px;
    overflow: hidden;
  }

  .sub-window-title-bar {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: var(--title-bar-height);
    padding: 0 4px;
    background: linear-gradient(180deg, #f8f8f8 0%, #e8e8e8 100%);
    border-bottom: 1px solid #c0c0c0;
    cursor: move;
    user-select: none;
    flex-shrink: 0;
  }

  .sub-window-icon-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding-left: 4px;
    flex-shrink: 0;
    z-index: 1;
  }

  .sub-window-icon {
    width: 18px;
    height: 18px;
    object-fit: contain;
  }

  .sub-window-title {
    position: absolute;
    left: 30px;
    right: 72px;
    font-weight: 500;
    color: #333333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: center;
    pointer-events: none;
  }

  .sub-window-buttons {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-right: -1px;
    flex-shrink: 0;
    z-index: 1;
  }

  .sub-window-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    padding: 0;
    border: none;
    border-radius: 5px;
    background-color: transparent;
    cursor: default;
    transition: background-color 0.1s ease;
  }

  .sub-window-btn:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }

  .sub-window-btn.close:hover {
    background-color: #e81123;
  }

  .sub-window-btn.close:hover .sub-window-btn-icon {
    filter: brightness(0) invert(1);
  }

  .sub-window-btn-icon {
    width: 10px;
    height: 10px;
    transition: transform 0.15s ease;
  }

  .sub-window-btn-icon.rotated {
    transform: rotate(180deg);
  }

  /* Minimized window */
  .sub-window.minimized {
    position: relative;
    width: var(--minimized-width) !important;
    height: auto !important;
    left: unset !important;
    top: unset !important;
    border-radius: 8px 8px 0 0;
    box-shadow: none;
    border-bottom: none;
  }

  .sub-window.minimized .sub-window-title-bar {
    cursor: default;
  }

  /* Maximized window - fills the visible container area */
  .sub-window.maximized {
    position: absolute;
    inset: 0;
    width: 100% !important;
    height: 100% !important;
    border-radius: 0;
    border: none;
    box-shadow: none;
  }

  .sub-window.maximized .sub-window-title-bar {
    cursor: default;
  }

  .sub-window-content {
    flex: 1;
    overflow: hidden;
    min-height: 0;
    background-color: #ffffff;
  }

  /* Resize handles */
  .resize-handle {
    position: absolute;
    background: transparent;
  }

  .resize-n {
    top: -3px;
    left: 6px;
    right: 6px;
    height: 6px;
    cursor: ns-resize;
  }

  .resize-s {
    bottom: -3px;
    left: 6px;
    right: 6px;
    height: 6px;
    cursor: ns-resize;
  }

  .resize-e {
    right: -3px;
    top: 6px;
    bottom: 6px;
    width: 6px;
    cursor: ew-resize;
  }

  .resize-w {
    left: -3px;
    top: 6px;
    bottom: 6px;
    width: 6px;
    cursor: ew-resize;
  }

  .resize-ne {
    top: -3px;
    right: -3px;
    width: 10px;
    height: 10px;
    cursor: nesw-resize;
  }

  .resize-nw {
    top: -3px;
    left: -3px;
    width: 10px;
    height: 10px;
    cursor: nwse-resize;
  }

  .resize-se {
    bottom: -3px;
    right: -3px;
    width: 10px;
    height: 10px;
    cursor: nwse-resize;
  }

  .resize-sw {
    bottom: -3px;
    left: -3px;
    width: 10px;
    height: 10px;
    cursor: nesw-resize;
  }
</style>
