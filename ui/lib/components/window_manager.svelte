<!--
  @component WindowManager

  Window manager area component.
  Provides a container for managing multiple child windows (sub-windows) within a single parent area.

  ## Features
  - Window management (create, close, focus)
  - Window states: normal, minimized, maximized
  - Drag and drop window positioning
  - Resize windows from all 8 directions (n, s, e, w, ne, nw, se, sw)
  - Z-index management for window layering
  - Automatic scroll area for windows positioned outside visible bounds
  - Geometry save/restore for minimize/maximize operations
  - Minimized windows dock at bottom-left with wrap support
  - Maximized windows fill entire container area
  - Visual stability: scroll position adjusts when windows move to negative coordinates
  - Minimum window size constraints (150x100 px)
  - Windows cannot be dragged/resized past top-left boundary (0, 0)

  ## Props
  - `windows: WindowData[]` - Array of window data objects (bindable for two-way sync)

  ## Events
  - `close` - Fired when window is closed: `{ id: string }`
  - `move` - Fired when window is moved: `{ id: string, x: number, y: number }`
  - `resize` - Fired when window is resized: `{ id: string, width: number, height: number }`
  - `focus` - Fired when window receives focus: `{ id: string }`
  - `minimize` - Fired when window is minimized: `{ id: string }`
  - `maximize` - Fired when window is maximized: `{ id: string }`
  - `restore` - Fired when window is restored from minimized/maximized: `{ id: string }`

  ## Slots
  - `windowContent` - Content for each window, receives `window: WindowData` prop

  ## Types
  ```typescript
  // Re-exported from SubWindow
  type WindowState = "normal" | "minimized" | "maximized";
  type WindowItem = WindowData;  // Alias for convenience

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
  ```

  ## Constants
  - `MIN_WIDTH = 150` - Minimum window width in pixels
  - `MIN_HEIGHT = 100` - Minimum window height in pixels
  - `TITLE_HEIGHT = 28` - Title bar height in pixels

  ## Usage Example
  ```svelte
  <script>
    let windows = [
      { id: "1", title: "Editor", x: 50, y: 50, width: 400, height: 300, zIndex: 1 },
      { id: "2", title: "Console", x: 100, y: 100, width: 300, height: 200, zIndex: 2 }
    ];
  </script>

  <WindowManager
    bind:windows
    on:close={(e) => console.log('Closed:', e.detail.id)}
    on:focus={(e) => console.log('Focused:', e.detail.id)}
  >
    <svelte:fragment slot="windowContent" let:window>
      {#if window.id === "1"}
        <TextEditor />
      {:else if window.id === "2"}
        <Console />
      {:else}
        <p>Window: {window.title}</p>
      {/if}
    </svelte:fragment>
  </WindowManager>
  ```
-->
<script context="module" lang="ts">
  export type {
    WindowState,
    WindowData as WindowItem,
  } from "./sub_window.svelte";

  interface WindowGeometry {
    x: number;
    y: number;
    width: number;
    height: number;
  }
</script>

<script lang="ts">
  import { createEventDispatcher, onDestroy } from "svelte";
  import { writable } from "svelte/store";

  import SubWindow from "./sub_window.svelte";
  import type { WindowData, ResizeDirection } from "./sub_window.svelte";

  // Constants
  const MIN_WIDTH = 150;
  const MIN_HEIGHT = 100;
  // Reserved for future snap-to-edges feature
  const TITLE_HEIGHT = 28;

  // Props
  export let windows: WindowData[] = [];

  // Local state
  let containerElement: HTMLElement;
  let maxZIndex = 1;
  let prevOffsetX = 0;
  let prevOffsetY = 0;

  // Reactive store for saving window geometry before maximize/minimize
  const savedGeometry = writable<Record<string, WindowGeometry>>({});

  // Reactive store for tracking minimize order
  const minimizedOrder = writable<Record<string, number>>({});
  let minimizeCounter = 0;

  const dispatch = createEventDispatcher<{
    close: { id: string };
    move: { id: string; x: number; y: number };
    resize: { id: string; width: number; height: number };
    focus: { id: string };
    minimize: { id: string };
    maximize: { id: string };
    restore: { id: string };
  }>();

  // Derived: split windows by state for separate rendering
  $: normalWindows = windows.filter((w) => (w.state ?? "normal") === "normal");
  $: minimizedWindows = windows
    .filter((w) => w.state === "minimized")
    .sort(
      (a, b) => ($minimizedOrder[a.id] ?? 0) - ($minimizedOrder[b.id] ?? 0)
    );
  $: maximizedWindows = windows.filter((w) => w.state === "maximized");

  // Interaction state (drag or resize)
  interface DragState {
    windowId: string;
    startMouseX: number;
    startMouseY: number;
    startWindowX: number;
    startWindowY: number;
  }

  interface ResizeState extends DragState {
    direction: ResizeDirection;
    startWidth: number;
    startHeight: number;
  }

  let dragState: DragState | null = null;
  let resizeState: ResizeState | null = null;

  // Helper: find window by id
  function findWindow(id: string): WindowData | undefined {
    return windows.find((w) => w.id === id);
  }

  // Helper: update a single window
  function updateWindow(id: string, updates: Partial<WindowData>) {
    windows = windows.map((w) => (w.id === id ? { ...w, ...updates } : w));
  }

  // Helper: save current geometry for later restoration
  function saveGeometry(win: WindowData) {
    savedGeometry.update((store) => ({
      ...store,
      [win.id]: {
        x: win.x,
        y: win.y,
        width: win.width,
        height: win.height,
      },
    }));
  }

  // Helper: restore saved geometry and remove from storage
  function restoreGeometry(id: string): WindowGeometry | undefined {
    let geometry: WindowGeometry | undefined;
    savedGeometry.update((store) => {
      geometry = store[id];
      if (geometry) {
        const { [id]: _, ...rest } = store;
        return rest;
      }
      return store;
    });
    return geometry;
  }

  // Window operations
  function bringToFront(windowId: string) {
    maxZIndex++;
    updateWindow(windowId, { zIndex: maxZIndex });
    dispatch("focus", { id: windowId });
  }

  function closeWindow(windowId: string) {
    windows = windows.filter((w) => w.id !== windowId);
    savedGeometry.update((store) => {
      const { [windowId]: _, ...rest } = store;
      return rest;
    });
    minimizedOrder.update((store) => {
      const { [windowId]: _, ...rest } = store;
      return rest;
    });
    dispatch("close", { id: windowId });
  }

  function minimizeWindow(windowId: string) {
    const win = findWindow(windowId);
    if (!win) return;

    const currentState = win.state ?? "normal";

    if (currentState === "minimized") {
      // Restore from minimized
      const geometry = restoreGeometry(windowId);
      minimizedOrder.update((store) => {
        const { [windowId]: _, ...rest } = store;
        return rest;
      });
      updateWindow(windowId, { state: "normal", ...geometry });
      dispatch("restore", { id: windowId });
    } else {
      // Save geometry only from normal state
      if (currentState === "normal") {
        saveGeometry(win);
      }
      minimizedOrder.update((store) => ({
        ...store,
        [windowId]: minimizeCounter++,
      }));
      updateWindow(windowId, { state: "minimized" });
      dispatch("minimize", { id: windowId });
    }
  }

  function maximizeWindow(windowId: string) {
    const win = findWindow(windowId);
    if (!win) return;

    const currentState = win.state ?? "normal";

    if (currentState === "maximized") {
      // Restore from maximized
      const geometry = restoreGeometry(windowId);
      updateWindow(windowId, { state: "normal", ...geometry });
      dispatch("restore", { id: windowId });
    } else {
      // Save geometry only from normal state
      if (currentState === "normal") {
        saveGeometry(win);
      }
      updateWindow(windowId, { state: "maximized" });
      dispatch("maximize", { id: windowId });
    }
  }

  // Drag operations
  function startDrag(windowId: string, clientX: number, clientY: number) {
    const win = findWindow(windowId);
    if (!win) return;

    bringToFront(windowId);
    dragState = {
      windowId,
      startMouseX: clientX,
      startMouseY: clientY,
      startWindowX: win.x,
      startWindowY: win.y,
    };
  }

  function processDrag(event: MouseEvent) {
    if (!dragState) return;

    const deltaX = event.clientX - dragState.startMouseX;
    const deltaY = event.clientY - dragState.startMouseY;
    // Prevent window from moving past left and top edges
    const newX = Math.max(0, dragState.startWindowX + deltaX);
    const newY = Math.max(0, dragState.startWindowY + deltaY);

    updateWindow(dragState.windowId, { x: newX, y: newY });
    dispatch("move", { id: dragState.windowId, x: newX, y: newY });
  }

  function endDrag() {
    dragState = null;
  }

  // Resize operations
  function startResize(
    windowId: string,
    clientX: number,
    clientY: number,
    direction: ResizeDirection
  ) {
    const win = findWindow(windowId);
    if (!win) return;

    bringToFront(windowId);
    resizeState = {
      windowId,
      direction,
      startMouseX: clientX,
      startMouseY: clientY,
      startWindowX: win.x,
      startWindowY: win.y,
      startWidth: win.width,
      startHeight: win.height,
    };
  }

  function processResize(event: MouseEvent) {
    if (!resizeState) return;

    const {
      direction,
      startMouseX,
      startMouseY,
      startWindowX,
      startWindowY,
      startWidth,
      startHeight,
    } = resizeState;
    const deltaX = event.clientX - startMouseX;
    const deltaY = event.clientY - startMouseY;

    let newX = startWindowX;
    let newY = startWindowY;
    let newWidth = startWidth;
    let newHeight = startHeight;

    // Horizontal resizing
    if (direction.includes("e")) {
      newWidth = Math.max(MIN_WIDTH, startWidth + deltaX);
    } else if (direction.includes("w")) {
      let widthDelta = Math.min(deltaX, startWidth - MIN_WIDTH);
      // Prevent window from moving past left edge
      widthDelta = Math.max(widthDelta, -startWindowX);
      newWidth = startWidth - widthDelta;
      newX = startWindowX + widthDelta;
    }

    // Vertical resizing
    if (direction.includes("s")) {
      newHeight = Math.max(MIN_HEIGHT, startHeight + deltaY);
    } else if (direction.includes("n")) {
      let heightDelta = Math.min(deltaY, startHeight - MIN_HEIGHT);
      // Prevent window from moving past top edge
      heightDelta = Math.max(heightDelta, -startWindowY);
      newHeight = startHeight - heightDelta;
      newY = startWindowY + heightDelta;
    }

    updateWindow(resizeState.windowId, {
      x: newX,
      y: newY,
      width: newWidth,
      height: newHeight,
    });
    dispatch("resize", {
      id: resizeState.windowId,
      width: newWidth,
      height: newHeight,
    });
  }

  function endResize() {
    resizeState = null;
  }

  // Global mouse event handlers
  function onGlobalMouseMove(event: MouseEvent) {
    if (dragState) {
      processDrag(event);
    } else if (resizeState) {
      processResize(event);
    }
  }

  function onGlobalMouseUp() {
    if (dragState) endDrag();
    if (resizeState) endResize();
  }

  // Manage global event listeners based on interaction state
  $: isInteracting = dragState !== null || resizeState !== null;

  // Track if listeners are currently attached to prevent duplicate additions
  let listenersAttached = false;

  function attachGlobalListeners() {
    if (listenersAttached) return;
    document.addEventListener("mousemove", onGlobalMouseMove);
    document.addEventListener("mouseup", onGlobalMouseUp);
    listenersAttached = true;
  }

  function detachGlobalListeners() {
    if (!listenersAttached) return;
    document.removeEventListener("mousemove", onGlobalMouseMove);
    document.removeEventListener("mouseup", onGlobalMouseUp);
    listenersAttached = false;
  }

  $: if (isInteracting) {
    attachGlobalListeners();
  } else {
    detachGlobalListeners();
  }

  onDestroy(detachGlobalListeners);

  // Calculate bounding box of all normal windows
  $: windowBounds = normalWindows.reduce(
    (bounds, win) => {
      return {
        minX: Math.min(bounds.minX, win.x),
        minY: Math.min(bounds.minY, win.y),
        maxX: Math.max(bounds.maxX, win.x + win.width),
        maxY: Math.max(bounds.maxY, win.y + win.height),
      };
    },
    { minX: 0, minY: 0, maxX: 0, maxY: 0 }
  );

  // Offset to handle negative window positions (shift all windows to keep visible)
  $: offsetX = Math.max(0, -windowBounds.minX);
  $: offsetY = Math.max(0, -windowBounds.minY);

  // Adjust scroll when offset changes to maintain visual stability
  $: if (containerElement) {
    const deltaX = offsetX - prevOffsetX;
    const deltaY = offsetY - prevOffsetY;
    if (deltaX !== 0 || deltaY !== 0) {
      containerElement.scrollLeft += deltaX;
      containerElement.scrollTop += deltaY;
      prevOffsetX = offsetX;
      prevOffsetY = offsetY;
    }
  }

  // Content dimensions (scrollable area size)
  $: contentWidth = normalWindows.length > 0 ? offsetX + windowBounds.maxX : 0;
  $: contentHeight = normalWindows.length > 0 ? offsetY + windowBounds.maxY : 0;
</script>

<div
  class="window-manager"
  bind:this={containerElement}
  class:dragging={dragState !== null}
  class:resizing={resizeState !== null}
>
  <!-- Scrollable canvas for normal windows -->
  <div
    class="window-manager-content"
    style:min-width="{contentWidth}px"
    style:min-height="{contentHeight}px"
  >
    {#each normalWindows as win (win.id)}
      <SubWindow
        window={win}
        {offsetX}
        {offsetY}
        on:focus={() => bringToFront(win.id)}
        on:close={() => closeWindow(win.id)}
        on:minimize={() => minimizeWindow(win.id)}
        on:maximize={() => maximizeWindow(win.id)}
        on:dragstart={(e) =>
          startDrag(win.id, e.detail.clientX, e.detail.clientY)}
        on:resizestart={(e) =>
          startResize(
            win.id,
            e.detail.clientX,
            e.detail.clientY,
            e.detail.direction
          )}
      >
        <slot name="windowContent" window={win}>
          <p>Window content</p>
        </slot>
      </SubWindow>
    {/each}
  </div>

  <!-- Minimized windows dock at bottom-left -->
  {#if minimizedWindows.length > 0}
    <div class="minimized-dock">
      {#each minimizedWindows as win (win.id)}
        <SubWindow
          window={win}
          offsetX={0}
          offsetY={0}
          on:focus={() => bringToFront(win.id)}
          on:close={() => closeWindow(win.id)}
          on:minimize={() => minimizeWindow(win.id)}
          on:maximize={() => maximizeWindow(win.id)}
          on:dragstart={(e) =>
            startDrag(win.id, e.detail.clientX, e.detail.clientY)}
          on:resizestart={(e) =>
            startResize(
              win.id,
              e.detail.clientX,
              e.detail.clientY,
              e.detail.direction
            )}
        >
          <slot name="windowContent" window={win}>
            <p>Window content</p>
          </slot>
        </SubWindow>
      {/each}
    </div>
  {/if}

  <!-- Maximized windows rendered outside scrollable content -->
  {#each maximizedWindows as win (win.id)}
    <SubWindow
      window={win}
      offsetX={0}
      offsetY={0}
      on:focus={() => bringToFront(win.id)}
      on:close={() => closeWindow(win.id)}
      on:minimize={() => minimizeWindow(win.id)}
      on:maximize={() => maximizeWindow(win.id)}
      on:dragstart={(e) =>
        startDrag(win.id, e.detail.clientX, e.detail.clientY)}
      on:resizestart={(e) =>
        startResize(
          win.id,
          e.detail.clientX,
          e.detail.clientY,
          e.detail.direction
        )}
    >
      <slot name="windowContent" window={win}>
        <p>Window content</p>
      </slot>
    </SubWindow>
  {/each}
</div>

<style>
  .window-manager {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: #bbbbbb;
  }

  .window-manager-content {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .window-manager.dragging,
  .window-manager.resizing {
    user-select: none;
  }

  .minimized-dock {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    flex-direction: row;
    flex-wrap: wrap-reverse;
    align-content: flex-start;
    z-index: 0;
  }
</style>
