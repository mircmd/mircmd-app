<!--
  @component WindowManager

  Window manager component with internal state management.
  Provides a container for managing multiple sub-windows with full lifecycle control.

  ## Features
  - Internal window state management (add, remove, focus)
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

  ## External Access
  Use `getWindowManager()` from `window_manager_context.ts` to access:
  - `addWindow(title, pluginPath, htmlContent, icon?)` - Add a new window
  - `removeWindow(id)` - Remove window by id

  ## Constants
  - `MIN_WIDTH = 150` - Minimum window width in pixels
  - `MIN_HEIGHT = 100` - Minimum window height in pixels
-->
<script lang="ts">
  import { onDestroy, tick } from "svelte";

  import SubWindow from "./sub_window.svelte";
  import type { WindowData, ResizeDirection } from "./sub_window.svelte";
  import {
    registerWindowManager,
    unregisterWindowManager,
    type PluginWindowData,
  } from "./window_manager_context";

  interface InternalWindowData extends WindowData {
    pluginData?: PluginWindowData;
  }

  interface WindowGeometry {
    x: number;
    y: number;
    width: number;
    height: number;
  }

  // Constants
  const MIN_WIDTH = 150;
  const MIN_HEIGHT = 100;

  // Internal state
  let windows = $state<InternalWindowData[]>([]);
  let containerElement: HTMLElement | undefined = $state();
  let maxZIndex = $state(1);
  let prevOffsetX = $state(0);
  let prevOffsetY = $state(0);
  let savedGeometry = $state<Record<string, WindowGeometry>>({});
  let minimizedOrder = $state<Record<string, number>>({});
  let minimizeCounter = $state(0);

  // Interaction state
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

  let dragState = $state<DragState | null>(null);
  let resizeState = $state<ResizeState | null>(null);

  // Derived state
  let normalWindows = $derived(
    windows.filter((w) => (w.state ?? "normal") === "normal")
  );

  let minimizedWindows = $derived(
    windows
      .filter((w) => w.state === "minimized")
      .sort((a, b) => (minimizedOrder[a.id] ?? 0) - (minimizedOrder[b.id] ?? 0))
  );

  let maximizedWindows = $derived(
    windows.filter((w) => w.state === "maximized")
  );

  let isInteracting = $derived(dragState !== null || resizeState !== null);

  let windowBounds = $derived(
    normalWindows.reduce(
      (bounds, win) => ({
        minX: Math.min(bounds.minX, win.x),
        minY: Math.min(bounds.minY, win.y),
        maxX: Math.max(bounds.maxX, win.x + win.width),
        maxY: Math.max(bounds.maxY, win.y + win.height),
      }),
      { minX: 0, minY: 0, maxX: 0, maxY: 0 }
    )
  );

  let offsetX = $derived(Math.max(0, -windowBounds.minX));
  let offsetY = $derived(Math.max(0, -windowBounds.minY));

  let contentWidth = $derived(
    normalWindows.length > 0 ? offsetX + windowBounds.maxX : 0
  );
  let contentHeight = $derived(
    normalWindows.length > 0 ? offsetY + windowBounds.maxY : 0
  );

  // Context API methods
  function addWindow(
    title: string,
    pluginPath: string,
    htmlContent: string,
    icon?: string
  ): void {
    const id = `window-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const newWindow: InternalWindowData = {
      id,
      title,
      icon,
      x: 50 + (windows.length % 5) * 30,
      y: 30 + (windows.length % 5) * 30,
      width: 400,
      height: 300,
      zIndex: maxZIndex++,
      pluginData: {
        pluginPath,
        htmlContent,
      },
    };
    windows = [...windows, newWindow];
  }

  function removeWindow(id: string): void {
    windows = windows.filter((w) => w.id !== id);
    const { [id]: _saved, ...restSaved } = savedGeometry;
    savedGeometry = restSaved;
    const { [id]: _order, ...restOrder } = minimizedOrder;
    minimizedOrder = restOrder;
  }

  // Register methods for external access
  registerWindowManager({ addWindow, removeWindow });

  // Helper functions
  function findWindow(id: string): InternalWindowData | undefined {
    return windows.find((w) => w.id === id);
  }

  function updateWindow(
    id: string,
    updates: Partial<InternalWindowData>
  ): void {
    windows = windows.map((w) => (w.id === id ? { ...w, ...updates } : w));
  }

  function saveGeometry(win: InternalWindowData): void {
    savedGeometry = {
      ...savedGeometry,
      [win.id]: {
        x: win.x,
        y: win.y,
        width: win.width,
        height: win.height,
      },
    };
  }

  function restoreGeometry(id: string): WindowGeometry | undefined {
    const geometry = savedGeometry[id];
    if (geometry) {
      const { [id]: _, ...rest } = savedGeometry;
      savedGeometry = rest;
    }
    return geometry;
  }

  // Window operations
  function bringToFront(windowId: string): void {
    updateWindow(windowId, { zIndex: maxZIndex++ });
  }

  function closeWindow(windowId: string): void {
    removeWindow(windowId);
  }

  function minimizeWindow(windowId: string): void {
    const win = findWindow(windowId);
    if (!win) return;

    const currentState = win.state ?? "normal";

    if (currentState === "minimized") {
      const geometry = restoreGeometry(windowId);
      const { [windowId]: _, ...rest } = minimizedOrder;
      minimizedOrder = rest;
      updateWindow(windowId, { state: "normal", ...geometry });
    } else {
      if (currentState === "normal") {
        saveGeometry(win);
      }
      minimizedOrder = { ...minimizedOrder, [windowId]: minimizeCounter++ };
      updateWindow(windowId, { state: "minimized" });
    }
  }

  function maximizeWindow(windowId: string): void {
    const win = findWindow(windowId);
    if (!win) return;

    const currentState = win.state ?? "normal";

    if (currentState === "maximized") {
      const geometry = restoreGeometry(windowId);
      updateWindow(windowId, { state: "normal", ...geometry });
    } else {
      if (currentState === "normal") {
        saveGeometry(win);
      }
      updateWindow(windowId, { state: "maximized" });
    }
  }

  // Drag operations
  function startDrag(windowId: string, clientX: number, clientY: number): void {
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

  function processDrag(event: MouseEvent): void {
    if (!dragState) return;

    const deltaX = event.clientX - dragState.startMouseX;
    const deltaY = event.clientY - dragState.startMouseY;
    const newX = Math.max(0, dragState.startWindowX + deltaX);
    const newY = Math.max(0, dragState.startWindowY + deltaY);

    updateWindow(dragState.windowId, { x: newX, y: newY });
  }

  function endDrag(): void {
    dragState = null;
  }

  // Resize operations
  function startResize(
    windowId: string,
    clientX: number,
    clientY: number,
    direction: ResizeDirection
  ): void {
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

  function processResize(event: MouseEvent): void {
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

    if (direction.includes("e")) {
      newWidth = Math.max(MIN_WIDTH, startWidth + deltaX);
    } else if (direction.includes("w")) {
      let widthDelta = Math.min(deltaX, startWidth - MIN_WIDTH);
      widthDelta = Math.max(widthDelta, -startWindowX);
      newWidth = startWidth - widthDelta;
      newX = startWindowX + widthDelta;
    }

    if (direction.includes("s")) {
      newHeight = Math.max(MIN_HEIGHT, startHeight + deltaY);
    } else if (direction.includes("n")) {
      let heightDelta = Math.min(deltaY, startHeight - MIN_HEIGHT);
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
  }

  function endResize(): void {
    resizeState = null;
  }

  // Global mouse event handlers
  function onGlobalMouseMove(event: MouseEvent): void {
    if (dragState) {
      processDrag(event);
    } else if (resizeState) {
      processResize(event);
    }
  }

  function onGlobalMouseUp(): void {
    if (dragState) endDrag();
    if (resizeState) endResize();
  }

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

  $effect(() => {
    if (isInteracting) {
      attachGlobalListeners();
    } else {
      detachGlobalListeners();
    }
  });

  // Adjust scroll when offset changes
  $effect(() => {
    if (containerElement) {
      const deltaX = offsetX - prevOffsetX;
      const deltaY = offsetY - prevOffsetY;
      if (deltaX !== 0 || deltaY !== 0) {
        containerElement.scrollLeft += deltaX;
        containerElement.scrollTop += deltaY;
        prevOffsetX = offsetX;
        prevOffsetY = offsetY;
      }
    }
  });

  // Execute scripts in plugin HTML after rendering
  function executeScriptsAction(node: HTMLElement, _windowId: string) {
    tick().then(() => {
      const scripts = node.querySelectorAll("script");
      scripts.forEach((oldScript) => {
        const newScript = document.createElement("script");
        newScript.textContent = oldScript.textContent;
        oldScript.parentNode?.replaceChild(newScript, oldScript);
      });
    });
    return {};
  }

  onDestroy(() => {
    detachGlobalListeners();
    unregisterWindowManager();
  });
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
        {#if win.pluginData}
          <div
            class="plugin-content"
            id="plugin-container-{win.id}"
            use:executeScriptsAction={win.id}
          >
            {@html win.pluginData.htmlContent}
          </div>
        {:else}
          <div class="default-content">
            <p>Window: {win.title}</p>
          </div>
        {/if}
      </SubWindow>
    {/each}
  </div>

  <!-- Minimized windows dock -->
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
          {#if win.pluginData}
            <div class="plugin-content">
              {@html win.pluginData.htmlContent}
            </div>
          {/if}
        </SubWindow>
      {/each}
    </div>
  {/if}

  <!-- Maximized windows -->
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
      {#if win.pluginData}
        <div
          class="plugin-content"
          id="plugin-container-{win.id}"
          use:executeScriptsAction={win.id}
        >
          {@html win.pluginData.htmlContent}
        </div>
      {:else}
        <div class="default-content">
          <p>Window: {win.title}</p>
        </div>
      {/if}
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

  .plugin-content {
    width: 100%;
    height: 100%;
    padding: 0;
    box-sizing: border-box;
    background: #f5f5f5;
    overflow: hidden;
  }

  .plugin-content :global(h2) {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #333;
  }

  .plugin-content :global(p) {
    margin: 4px 0;
    font-size: 12px;
    color: #666;
  }

  .plugin-content :global(ul) {
    margin: 8px 0 0 0;
    padding-left: 20px;
  }

  .plugin-content :global(li) {
    font-size: 12px;
    color: #555;
  }

  .default-content {
    padding: 12px;
  }

  .default-content p {
    margin: 0;
    font-size: 12px;
    color: #555;
  }
</style>
