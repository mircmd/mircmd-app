<!--
  @component WindowManager

  Window manager component with internal state management.
  Provides a container for managing multiple sub-windows with full lifecycle control.
-->
<script lang="ts" module>
  let id_counter = 0;

  function generateId() {
    return "window-" + (id_counter++).toString();
  }

  export type WindowState = "normal" | "minimized" | "maximized";

  export type Window = {
    id?: string;
    icon: string;
    title: string;
    state?: WindowState;
    pos?: [number, number]; // top left corner of the window
    size?: [number, number];
    minSize?: [number, number];
    onmount?: (ctx: HTMLElement) => void;
    htmlContent?: string;
    snippet?: Snippet;
    component?: Component<any>;
    props?: Record<string, any>;
  };

  type ResizeEdge = "n" | "s" | "e" | "w";

  export type WindowInput = Partial<Omit<Window, "id">>;

  const DEFAULTS = {
    state: "normal",
    pos: [0, 0],
    size: [500, 500],
    minSize: [50, 50],
  };

  const RESIZE_HANDLE_SIZE = 8;
</script>

<script lang="ts">
  import type { Component, Snippet } from "svelte";
  import { onDestroy } from "svelte";
  import hideWindowIcon from "../assets/icons/window_hide.svg";
  import closeWindowIcon from "../assets/icons/window_close.svg";
  import expandWindowIcon from "../assets/icons/window_expand.svg";
  import collapseWindowIcon from "../assets/icons/window_collapse.svg";
  import { getContextMenu } from "../core/context_menu.svelte";

  const contextMenu = getContextMenu();

  // Internal state
  let windows = $state<Window[]>([]);
  let windowsZIndex = $state<string[]>([]);

  let windowAction = $state<"drag" | "resize" | null>(null);
  let hasMaximizedWindow = $state<boolean>(false);
  let windowUnderAction = $state<Window | null>(null);
  let lastMouseState = { clientX: 0, clientY: 0, layerX: 0, layerY: 0 };
  let lastWindowState = { w: 0, h: 0, x: 0, y: 0 };
  let windowResizeEdges: ResizeEdge[] = [];

  let isInteracting = $derived(windowUnderAction !== null);
  let activeWindow = $derived(windowsZIndex[windowsZIndex.length - 1]);

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
    processDragOrResizeWindow(event);
  }

  function onGlobalMouseUp(): void {
    windowUnderAction = null;
    windowAction = null;
    document.body.style.cursor = "";
  }

  function getRelativeMousePosition(event: MouseEvent, element: HTMLElement): [number, number] {
    const rect = element.getBoundingClientRect();
    return [event.clientX - rect.left, event.clientY - rect.top];
  }

  function getResizeEdges(x: number, y: number, width: number, height: number): ResizeEdge[] {
    const edges: ResizeEdge[] = [];

    width += RESIZE_HANDLE_SIZE * 2;
    height += RESIZE_HANDLE_SIZE * 2;

    if (x < RESIZE_HANDLE_SIZE) {
      edges.push("w");
    } else if (x > width - RESIZE_HANDLE_SIZE) {
      edges.push("e");
    }

    if (y < RESIZE_HANDLE_SIZE) {
      edges.push("n");
    } else if (y > height - RESIZE_HANDLE_SIZE) {
      edges.push("s");
    }

    return edges;
  }

  function getResizeCursor(edges: ResizeEdge[]): string | null {
    const set = new Set(edges);

    if (set.has("n") && set.has("e")) return "nesw-resize";
    if (set.has("n") && set.has("w")) return "nwse-resize";
    if (set.has("s") && set.has("e")) return "nwse-resize";
    if (set.has("s") && set.has("w")) return "nesw-resize";
    if (set.has("n")) return "n-resize";
    if (set.has("s")) return "s-resize";
    if (set.has("e")) return "e-resize";
    if (set.has("w")) return "w-resize";

    return null;
  }

  function updateWindowCursor(event: MouseEvent, window: Window): void {
    const element = event.currentTarget as HTMLElement;

    if (window.state !== "normal" || isInteracting) {
      element.style.cursor = "";
      return;
    }

    const [x, y] = getRelativeMousePosition(event, element);

    const width = window.size?.[0] ?? 0;
    const height = window.size?.[1] ?? 0;
    element.style.cursor = getResizeCursor(getResizeEdges(x, y, width, height)) ?? "";
  }

  function clearWindowCursor(event: MouseEvent): void {
    (event.currentTarget as HTMLElement).style.cursor = "";
  }

  function processDragOrResizeWindow(event: MouseEvent) {
    event.preventDefault();
    if (windowUnderAction) {
      const xDiff = event.clientX - lastMouseState.clientX;
      const yDiff = event.clientY - lastMouseState.clientY;

      if (windowAction === "drag") {
        windowUnderAction.pos = [
          lastWindowState.x + xDiff,
          Math.max(-RESIZE_HANDLE_SIZE, lastWindowState.y + yDiff), // Fix for the window being dragged up too far
        ];
      } else if (windowAction === "resize") {
        let newSize = [lastWindowState.w, lastWindowState.h];
        let newPos = [lastWindowState.x, lastWindowState.y];

        if (windowResizeEdges.includes("e")) {
          newSize[0] = lastWindowState.w + xDiff;
        }
        if (windowResizeEdges.includes("s")) {
          newSize[1] = lastWindowState.h + yDiff;
        }
        if (windowResizeEdges.includes("w")) {
          newSize[0] = lastWindowState.w - xDiff;
          newPos[0] = lastWindowState.x + xDiff;
        }
        if (windowResizeEdges.includes("n")) {
          newSize[1] = lastWindowState.h - yDiff;
          newPos[1] = lastWindowState.y + yDiff;
        }
        // Fix the window being resized up too far
        if (newPos[1] < -RESIZE_HANDLE_SIZE) {
          newPos[1] = -RESIZE_HANDLE_SIZE;
          newSize[1] = lastWindowState.h + lastWindowState.y + RESIZE_HANDLE_SIZE;
        }
        windowUnderAction.size = [newSize[0], newSize[1]];
        windowUnderAction.pos = [newPos[0], newPos[1]];
      }
    }
  }

  // Context API methods
  export function addWindow(params: WindowInput) {
    const windowId = generateId();
    let pos = params.pos ?? [0, 0];
    params.pos = [pos[0] - RESIZE_HANDLE_SIZE, pos[1] - RESIZE_HANDLE_SIZE];
    const newWindow: Window = {
      id: windowId,
      ...DEFAULTS,
      ...params,
    } as Window;

    windows.push(newWindow);
    windowsZIndex.push(windowId);
  }

  function getWindow(windowId: string): Window | null {
    return windows.find((w) => w.id === windowId) ?? null;
  }

  // Window operations
  function setFocus(window: Window) {
    const index = windowsZIndex.indexOf(window.id!);
    if (index !== -1 && index !== windowsZIndex.length - 1) {
      windowsZIndex.splice(index, 1);
      windowsZIndex.push(window.id!);
    }
  }

  function closeWindow(window: Window): void {
    windows = windows.filter((w) => w.id !== window.id);
    windowsZIndex = windowsZIndex.filter((w) => w !== window.id);
  }

  function startDragging(event: MouseEvent, window: Window): void {
    event.preventDefault();
    event.stopPropagation();

    if (event.button !== 0) return;
    if (window.state !== "normal") return;

    setFocus(window);

    windowUnderAction = window;
    windowAction = "drag";

    lastMouseState = { clientX: event.clientX, clientY: event.clientY, layerX: event.layerX, layerY: event.layerY };
    lastWindowState = {
      w: window.size?.[0] ?? 0,
      h: window.size?.[1] ?? 0,
      x: window.pos?.[0] ?? 0,
      y: window.pos?.[1] ?? 0,
    };
    windowResizeEdges = [];
  }

  function startResize(event: MouseEvent, window: Window): void {
    event.preventDefault();
    if (event.button !== 0) return;
    if (window.state !== "normal") return;

    setFocus(window);

    const width = window.size?.[0] ?? 0;
    const height = window.size?.[1] ?? 0;

    const element = event.currentTarget as HTMLElement;
    const [x, y] = getRelativeMousePosition(event, element);
    const edges = getResizeEdges(x, y, width, height);

    if (edges.length === 0) {
      windowResizeEdges = [];
      return;
    }

    windowUnderAction = window;
    windowAction = "resize";
    document.body.style.cursor = getResizeCursor(edges) ?? "";

    lastMouseState = { clientX: event.clientX, clientY: event.clientY, layerX: event.layerX, layerY: event.layerY };
    lastWindowState = {
      w: window.size?.[0] ?? 0,
      h: window.size?.[1] ?? 0,
      x: window.pos?.[0] ?? 0,
      y: window.pos?.[1] ?? 0,
    };
    windowResizeEdges = edges;
  }

  function minimizeWindowHandler(window: Window): void {
    if (window.state === "minimized") {
      window.state = "normal";
      hasMaximizedWindow = false;
    } else {
      window.state = "minimized";
      hasMaximizedWindow = false;
    }
    setFocus(window);
  }

  function maximizeWindowHandler(window: Window): void {
    if (window.state === "maximized") {
      window.state = "normal";
      hasMaximizedWindow = false;
    } else {
      window.state = "maximized";
      hasMaximizedWindow = true;
    }
    setFocus(window);
  }

  function execute(node: HTMLElement, window: Window): void {
    window.onmount?.(node);
  }

  onDestroy(() => {
    detachGlobalListeners();
  });
</script>

{#snippet window(window: Window)}
  <div
    class="window"
    class:inactive={window.state === "normal" && activeWindow !== window.id}
    class:minimized={window.state === "minimized"}
    class:maximized={window.state === "maximized"}
    style:min-width="{window.state === 'minimized' ? 0 : window.minSize?.[0]}px"
    style:min-height="{window.state === 'minimized' ? 0 : window.minSize?.[1]}px"
    style:left={window.state === "normal" ? `${window.pos?.[0]}px` : null}
    style:top={window.state === "normal" ? `${window.pos?.[1]}px` : null}
    style:width={window.state === "normal" ? `${window.size?.[0]}px` : null}
    style:height={window.state === "normal" ? `${window.size?.[1]}px` : null}
    style:z-index={10 + windowsZIndex.indexOf(window.id!)}
    style:--resize-handle-size="{RESIZE_HANDLE_SIZE}px"
    onmousedown={(e) => startResize(e, window)}
    onmousemove={(e) => updateWindowCursor(e, window)}
    onmouseleave={clearWindowCursor}
    role="dialog"
    tabindex="0"
  >
    <div class="window-shadow">
      <!-- Title bar -->
      <div
        class="window-title-bar"
        onmousedown={(e) => startDragging(e, window)}
        ondblclick={() => maximizeWindowHandler(window)}
        role="none"
      >
        <div class="window-icon-container">
          <img src={window.icon} alt="" class="window-icon" />
        </div>
        <span class="window-title">{window.title}</span>
        <div class="window-buttons">
          <button
            class="window-btn minimize"
            onclick={(e) => {
              e.stopPropagation();
              minimizeWindowHandler(window);
            }}
            aria-label={window.state === "minimized" ? "Restore window" : "Minimize window"}
          >
            <img
              src={hideWindowIcon}
              alt={window.state === "minimized" ? "Restore" : "Minimize"}
              class="window-btn-icon"
              class:rotated={window.state === "minimized"}
            />
          </button>
          <button
            class="window-btn maximize"
            onclick={(e) => {
              e.stopPropagation();
              maximizeWindowHandler(window);
            }}
            aria-label={window.state === "maximized" ? "Restore window" : "Maximize window"}
          >
            <img
              src={window.state === "maximized" ? collapseWindowIcon : expandWindowIcon}
              alt={window.state === "maximized" ? "Restore" : "Maximize"}
              class="window-btn-icon"
            />
          </button>
          <button
            class="window-btn close"
            onclick={(e) => {
              e.stopPropagation();
              closeWindow(window);
            }}
            aria-label="Close window"
          >
            <img src={closeWindowIcon} alt="Close" class="window-btn-icon" />
          </button>
        </div>
      </div>

      <!-- Content area (hidden when minimized) -->
      <div
        class="window-content"
        style:display={window.state === "minimized" ? "none" : "block"}
        use:execute={window}
        onmousedown={(e) => {
          e.stopPropagation();
          setFocus(window);
        }}
        role="none"
      >
        {#if window.htmlContent}
          {@html window.htmlContent}
        {:else if window.snippet}
          {@render window.snippet()}
        {:else if window.component}
          {@const Cmp = window.component}
          <Cmp {...window.props} />
        {/if}
      </div>
    </div>
  </div>
{/snippet}

<div class="window-manager" style:overflow={hasMaximizedWindow ? "hidden" : "auto"}>
  {#each windows as win (win.id)}
    {@render window(win)}
  {/each}
</div>

<style>
  .window-manager {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: #bbbbbb;
    display: flex;
    flex-direction: row;
    flex-wrap: wrap-reverse;
    align-content: flex-start;
    justify-content: flex-start;
  }

  .window {
    --title-bar-height: 28px;
    --minimized-width: 200px;

    padding: var(--resize-handle-size);

    position: absolute;
    display: flex;
    flex-direction: column;
    background-color: transparent;
  }

  .window.minimized {
    position: relative;
    width: var(--minimized-width) !important;
    height: auto !important;
    left: unset !important;
    top: unset !important;
    padding: 0px;
  }

  .window.maximized {
    position: absolute;
    inset: 0;
    width: 100% !important;
    height: 100% !important;
    padding: 0px;
  }

  .window-shadow {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    width: 100%;
    overflow: hidden;
    background-color: transparent;
    margin: 0px;
    padding: 0px;
    border: 1px solid #a0a0a0;
    border-radius: 8px;
    box-shadow:
      0 16px 48px rgba(0, 0, 0, 0.25),
      0 8px 16px rgba(0, 0, 0, 0.15);
  }

  .window.minimized .window-shadow {
    border-radius: 8px 8px 0 0;
    box-shadow: none;
    border-bottom: none;
  }

  .window.maximized .window-shadow {
    border: none;
    border-radius: 0px;
    box-shadow: none;
  }

  .window-title-bar {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: var(--title-bar-height);
    padding: 0 4px;
    background: linear-gradient(180deg, #f8f8f8 0%, #e8e8e8 100%);
    border-bottom: 1px solid #c0c0c0;
    user-select: none;
    flex-shrink: 0;
  }

  .window.minimized .window-title-bar {
    border-bottom: none;
  }

  .window-icon-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding-left: 4px;
    flex-shrink: 0;
  }

  .window-icon {
    width: 18px;
    height: 18px;
    object-fit: contain;
  }

  .window-title {
    position: absolute;
    left: 30px;
    right: 72px;
    font-weight: 500;
    color: #000000;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: center;
    pointer-events: none;
  }

  .window.inactive .window-title {
    color: #a0a0a0;
  }

  .window-buttons {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-right: -1px;
    flex-shrink: 0;
  }

  .window-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    padding: 0;
    border: none;
    border-radius: 5px;
    background-color: transparent;
    transition: background-color 0.1s ease;
  }

  .window-btn:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }

  .window-btn.close:hover {
    background-color: #e81123;
  }

  .window-btn.close:hover .window-btn-icon {
    filter: brightness(0) invert(1);
  }

  .window-btn-icon {
    width: 16px;
    height: 16px;
    transition: transform 0.15s ease;
  }

  .window-btn-icon.rotated {
    transform: rotate(180deg);
  }

  .window-content {
    flex: 1;
    overflow: hidden;
    min-height: 0;
    background-color: #ffffff;
  }
</style>
