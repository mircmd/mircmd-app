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
    pos?: [number, number];
    size?: [number, number];
    minSize?: [number, number];
    onmount?: (ctx: HTMLElement) => void;
    htmlContent?: string;
    snippet?: Snippet;
    component?: Component<any>;
    props?: Record<string, any>;
  };

  export type WindowInput = Partial<Omit<Window, "id">>;

  const DEFAULTS = {
    state: "normal",
    pos: [0, 0],
    size: [400, 300],
    minSize: [50, 50],
  };
</script>

<script lang="ts">
  import type { Component, Snippet } from "svelte";
  import { onDestroy } from "svelte";
  import hideWindowIcon from "../assets/icons/window_hide.svg";
  import closeWindowIcon from "../assets/icons/window_close.svg";
  import expandWindowIcon from "../assets/icons/window_expand.svg";
  import collapseWindowIcon from "../assets/icons/window_collapse.svg";

  // Internal state
  let windows = $state<Window[]>([]);
  let windowsZIndex = $state<string[]>([]);

  let draggingWindow = $state<Window | null>(null);
  let dragOffset = { x: 0, y: 0 };

  let isInteracting = $derived(draggingWindow !== null);
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
    processDragWindow(event);
  }

  function onGlobalMouseUp(): void {
    draggingWindow = null;
  }

  function processDragWindow(event: MouseEvent) {
    if (draggingWindow) {
      // event.preventDefault();
      draggingWindow.pos = [event.clientX - dragOffset.x, event.clientY - dragOffset.y];
    }
  }

  // Context API methods
  export function addWindow(params: WindowInput) {
    const windowId = generateId();
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

  function startDragging(event: MouseEvent, window: Window) {
    if (event.button !== 0) return;
    if (window.state !== "normal") return;

    draggingWindow = window;
    const currentX = window.pos?.[0] ?? 0;
    const currentY = window.pos?.[1] ?? 0;

    dragOffset = {
      x: event.clientX - currentX,
      y: event.clientY - currentY,
    };
  }

  function minimizeWindowHandler(window: Window) {
    if (window.state === "minimized") {
      window.state = "normal";
    } else {
      window.state = "minimized";
    }
    setFocus(window);
  }

  function maximizeWindowHandler(window: Window) {
    if (window.state === "maximized") {
      window.state = "normal";
    } else {
      window.state = "maximized";
    }
    setFocus(window);
  }

  function execute(node: HTMLElement, window: Window) {
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
    onmousedown={() => setFocus(window)}
    style:z-index={10 + windowsZIndex.indexOf(window.id!)}
    role="dialog"
    tabindex="0"
  >
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
    <div class="window-content" style:display={window.state === "minimized" ? "none" : "block"} use:execute={window}>
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
{/snippet}

<div class="window-manager">
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

  .window-title-bar {
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
    cursor: default;
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

  /* Minimized window */
  .window.minimized {
    position: relative;
    width: var(--minimized-width) !important;
    height: auto !important;
    left: unset !important;
    top: unset !important;
    border-radius: 8px 8px 0 0;
    box-shadow: none;
    border-bottom: none;
  }

  .window.minimized .window-title-bar {
    cursor: default;
  }

  /* Maximized window */
  .window.maximized {
    position: absolute;
    inset: 0;
    width: 100% !important;
    height: 100% !important;
    border-radius: 0;
    border: none;
    box-shadow: none;
  }

  .window.maximized .window-title-bar {
    cursor: default;
  }
</style>
