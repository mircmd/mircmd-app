<!--
  @component Workspace

  Main workspace layout component with dockable panels.
  Provides a flexible layout system with dock areas on left, right, and bottom sides.

  ## Features
  - Three dock areas: left, right, bottom
  - Resizable dock areas with min/max size constraints (100-600px)
  - Multiple dock groups within each area
  - Resizable groups within areas
  - Tab support for multiple docks in a single group
  - Tab reordering via drag and drop within groups
  - Drag and drop dock repositioning between groups and areas
  - Drop zone indicators for visual feedback during drag (before/center/after)
  - Floating dock preview during drag operations
  - Automatic group removal when empty
  - Single panel mode: when group has only one item, shows Panel with title bar instead of Tabs
  - Tab position support: left/right areas use side-aligned tabs

  ## Props
  - `data: WorkspaceState` - State object containing left, right, bottom dock groups (bindable)
  - `children: Snippet` - Main content area (center)
  - `dockContent: Snippet<[DockItem, DockPosition]>` - Content for each dock

  ## Layout Structure
  ```
  ┌───────┬─────────────────┬───────┐
  │       │                 │       │
  │ LEFT  │     MAIN        │ RIGHT │
  │       │    CONTENT      │       │
  │       │                 │       │
  ├───────┴─────────────────┴───────┤
  │            BOTTOM               │
  └─────────────────────────────────┘
  ```

  ## Usage Example
  ```svelte
  <Workspace bind:data={workspaceState}>
    <div>Main content here</div>

    {#snippet dockContent(dock, position)}
      {#if dock.id === "explorer"}
        <FileExplorer />
      {:else if dock.id === "console"}
        <Console />
      {:else}
        <p>{dock.content}</p>
      {/if}
    {/snippet}
  </Workspace>
  ```
-->
<script lang="ts" module>
  export type {
    DockItem,
    DockGroup,
    DockPosition,
    DropZone,
    WorkspaceState,
  } from "./types";
</script>

<script lang="ts">
  import { onDestroy, type Snippet } from "svelte";
  import type {
    DockItem,
    DockGroup,
    DockPosition,
    DropZone,
    WorkspaceState,
  } from "./types";
  import DockArea from "./dock_area.svelte";

  // Constants
  const AREA_MIN_SIZE = 100;
  const AREA_MAX_SIZE = 600;
  const AREA_DEFAULT_LEFT = 200;
  const AREA_DEFAULT_RIGHT = 250;
  const AREA_DEFAULT_BOTTOM = 200;
  const GROUP_MIN_SIZE = 50;
  const EDGE_ZONE_RATIO = 0.2;

  interface Props {
    data?: WorkspaceState;
    children?: Snippet;
    dockContent?: Snippet<[DockItem, DockPosition]>;
  }

  let {
    data = $bindable({ left: [], right: [], bottom: [] }),
    children,
    dockContent,
  }: Props = $props();

  // Area sizes
  let leftAreaWidth = $state(AREA_DEFAULT_LEFT);
  let rightAreaWidth = $state(AREA_DEFAULT_RIGHT);
  let bottomAreaHeight = $state(AREA_DEFAULT_BOTTOM);

  // Area resize state
  interface AreaResizeState {
    active: boolean;
    area: DockPosition | null;
    startPos: number;
    startSize: number;
  }

  let areaResize = $state<AreaResizeState>({
    active: false,
    area: null,
    startPos: 0,
    startSize: 0,
  });

  // Group resize state
  interface GroupResizeState {
    active: boolean;
    position: DockPosition | null;
    groupIndex: number;
    startPos: number;
    currentStartSize: number;
    nextStartSize: number;
  }

  let groupResize = $state<GroupResizeState>({
    active: false,
    position: null,
    groupIndex: -1,
    startPos: 0,
    currentStartSize: 0,
    nextStartSize: 0,
  });

  // Drag state for dock repositioning
  interface DragState {
    active: boolean;
    dockId: string | null;
    sourcePosition: DockPosition | null;
    sourceGroupId: string | null;
    floatingDock: DockItem | null;
    floatingX: number;
    floatingY: number;
    highlightedArea: DockPosition | null;
    highlightedGroupId: string | null;
    highlightedDropZone: DropZone | null;
  }

  let dragState = $state<DragState>({
    active: false,
    dockId: null,
    sourcePosition: null,
    sourceGroupId: null,
    floatingDock: null,
    floatingX: 0,
    floatingY: 0,
    highlightedArea: null,
    highlightedGroupId: null,
    highlightedDropZone: null,
  });

  // Track group element refs for drop zone detection
  let groupElements = new Map<string, HTMLElement>();

  // Derived state
  let isResizing = $derived(areaResize.active || groupResize.active);

  // Utility functions
  function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }

  function generateId(): string {
    return Math.random().toString(36).substring(2, 11);
  }

  function isHorizontalSplit(position: DockPosition): boolean {
    return position === "bottom";
  }

  // Update active tab for a group
  function setActiveTab(
    position: DockPosition,
    groupId: string,
    tabId: string
  ): void {
    data = {
      ...data,
      [position]: data[position].map((g) =>
        g.id === groupId ? { ...g, activeTabId: tabId } : g
      ),
    };
  }

  // Area resize handlers
  function startAreaResize(area: DockPosition, event: MouseEvent): void {
    const isHorizontal = area === "bottom";
    const startSize =
      area === "left"
        ? leftAreaWidth
        : area === "right"
          ? rightAreaWidth
          : bottomAreaHeight;

    areaResize = {
      active: true,
      area,
      startPos: isHorizontal ? event.clientY : event.clientX,
      startSize,
    };

    event.preventDefault();
  }

  function handleAreaResizeMove(event: MouseEvent): void {
    if (!areaResize.active || !areaResize.area) return;

    const { area, startPos, startSize } = areaResize;
    let delta: number;
    let newSize: number;

    switch (area) {
      case "left":
        delta = event.clientX - startPos;
        newSize = clamp(startSize + delta, AREA_MIN_SIZE, AREA_MAX_SIZE);
        leftAreaWidth = newSize;
        break;
      case "right":
        delta = startPos - event.clientX;
        newSize = clamp(startSize + delta, AREA_MIN_SIZE, AREA_MAX_SIZE);
        rightAreaWidth = newSize;
        break;
      case "bottom":
        delta = startPos - event.clientY;
        newSize = clamp(startSize + delta, AREA_MIN_SIZE, AREA_MAX_SIZE);
        bottomAreaHeight = newSize;
        break;
    }
  }

  // Group resize handlers
  function startGroupResize(
    position: DockPosition,
    groupIndex: number,
    event: MouseEvent
  ): void {
    const groups = data[position];
    if (groupIndex >= groups.length - 1) return;

    const target = event.target as HTMLElement;
    const areaElement = target.closest(".dock-area") as HTMLElement;
    if (!areaElement) return;

    const isHorizontal = isHorizontalSplit(position);
    const allWrappers = Array.from(
      areaElement.querySelectorAll(":scope > .group-wrapper")
    ) as HTMLElement[];

    if (allWrappers.length !== groups.length) return;

    // Normalize all groups to current pixel sizes
    const normalizedSizes = new Map<string, number>();
    groups.forEach((group, i) => {
      const wrapper = allWrappers[i];
      const rect = wrapper.getBoundingClientRect();
      const size = isHorizontal ? rect.width : rect.height;
      normalizedSizes.set(group.id, size);
    });

    data = {
      ...data,
      [position]: data[position].map((g) => {
        const normalizedSize = normalizedSizes.get(g.id);
        return normalizedSize !== undefined
          ? { ...g, size: normalizedSize }
          : g;
      }),
    };

    const currentWrapper = allWrappers[groupIndex];
    const nextWrapper = allWrappers[groupIndex + 1];

    if (!currentWrapper || !nextWrapper) return;

    const currentRect = currentWrapper.getBoundingClientRect();
    const nextRect = nextWrapper.getBoundingClientRect();

    groupResize = {
      active: true,
      position,
      groupIndex,
      startPos: isHorizontal ? event.clientX : event.clientY,
      currentStartSize: isHorizontal ? currentRect.width : currentRect.height,
      nextStartSize: isHorizontal ? nextRect.width : nextRect.height,
    };

    event.preventDefault();
    event.stopPropagation();
  }

  function handleGroupResizeMove(event: MouseEvent): void {
    if (!groupResize.active || !groupResize.position) return;

    const { position, groupIndex, startPos, currentStartSize, nextStartSize } =
      groupResize;
    const groups = data[position];
    const currentGroup = groups[groupIndex];
    const nextGroup = groups[groupIndex + 1];

    if (!currentGroup || !nextGroup) return;

    const isHorizontal = isHorizontalSplit(position);
    const currentPos = isHorizontal ? event.clientX : event.clientY;
    const delta = currentPos - startPos;
    const totalSize = currentStartSize + nextStartSize;

    let newCurrentSize = currentStartSize + delta;
    let newNextSize = nextStartSize - delta;

    if (newCurrentSize < GROUP_MIN_SIZE) {
      newCurrentSize = GROUP_MIN_SIZE;
      newNextSize = totalSize - GROUP_MIN_SIZE;
    } else if (newNextSize < GROUP_MIN_SIZE) {
      newNextSize = GROUP_MIN_SIZE;
      newCurrentSize = totalSize - GROUP_MIN_SIZE;
    }

    data = {
      ...data,
      [position]: data[position].map((g) => {
        if (g.id === currentGroup.id) return { ...g, size: newCurrentSize };
        if (g.id === nextGroup.id) return { ...g, size: newNextSize };
        return g;
      }),
    };
  }

  // Drag and drop handlers
  function handleDockUndock(
    position: DockPosition,
    groupId: string,
    dockId: string,
    x: number,
    y: number
  ): void {
    const groups = data[position];
    const group = groups.find((g) => g.id === groupId);
    const dock = group?.items.find((d) => d.id === dockId);
    if (!dock) return;

    dragState = {
      active: true,
      dockId,
      sourcePosition: position,
      sourceGroupId: groupId,
      floatingDock: { ...dock },
      floatingX: x,
      floatingY: y,
      highlightedArea: null,
      highlightedGroupId: null,
      highlightedDropZone: null,
    };

    removeDockFromGroup(position, groupId, dockId);

    document.addEventListener("mousemove", handleFloatingDragMove);
    document.addEventListener("mouseup", handleFloatingDragEnd);
  }

  function handleTabDragStart(
    position: DockPosition,
    groupId: string,
    dockId: string,
    x: number,
    y: number
  ): void {
    handleDockUndock(position, groupId, dockId, x, y);
  }

  function handleTabReorder(
    position: DockPosition,
    groupId: string,
    newItems: DockItem[]
  ): void {
    data = {
      ...data,
      [position]: data[position].map((g) =>
        g.id === groupId ? { ...g, items: newItems } : g
      ),
    };
  }

  function removeDockFromGroup(
    position: DockPosition,
    groupId: string,
    dockId: string
  ): void {
    data = {
      ...data,
      [position]: data[position]
        .map((g) => {
          if (g.id !== groupId) return g;
          const newItems = g.items.filter((d) => d.id !== dockId);
          const newActiveTabId =
            g.activeTabId === dockId ? (newItems[0]?.id ?? "") : g.activeTabId;
          return { ...g, items: newItems, activeTabId: newActiveTabId };
        })
        .filter((g) => g.items.length > 0),
    };
  }

  function findGroupPosition(groupId: string): DockPosition | null {
    if (data.left.some((g) => g.id === groupId)) return "left";
    if (data.right.some((g) => g.id === groupId)) return "right";
    if (data.bottom.some((g) => g.id === groupId)) return "bottom";
    return null;
  }

  function handleFloatingDragMove(event: MouseEvent): void {
    const x = event.clientX;
    const y = event.clientY;

    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    let newHighlightArea: DockPosition | null = null;
    let newHighlightGroupId: string | null = null;
    let newHighlightDropZone: DropZone | null = null;

    // Check if over any existing group
    for (const [groupId, element] of groupElements) {
      const rect = element.getBoundingClientRect();
      if (
        x >= rect.left &&
        x <= rect.right &&
        y >= rect.top &&
        y <= rect.bottom
      ) {
        const position = findGroupPosition(groupId);
        if (position) {
          newHighlightArea = position;
          newHighlightGroupId = groupId;

          const isHorizontal = isHorizontalSplit(position);
          if (isHorizontal) {
            const relX = (x - rect.left) / rect.width;
            if (relX < 0.25) {
              newHighlightDropZone = "before";
            } else if (relX > 0.75) {
              newHighlightDropZone = "after";
            } else {
              newHighlightDropZone = "center";
            }
          } else {
            const relY = (y - rect.top) / rect.height;
            if (relY < 0.25) {
              newHighlightDropZone = "before";
            } else if (relY > 0.75) {
              newHighlightDropZone = "after";
            } else {
              newHighlightDropZone = "center";
            }
          }
        }
        break;
      }
    }

    // If not over any group, check edge zones for new area
    if (!newHighlightGroupId) {
      if (data.left.length > 0 && x < leftAreaWidth) {
        newHighlightArea = "left";
      } else if (data.right.length > 0 && x > windowWidth - rightAreaWidth) {
        newHighlightArea = "right";
      } else if (
        data.bottom.length > 0 &&
        y > windowHeight - bottomAreaHeight
      ) {
        newHighlightArea = "bottom";
      } else if (x < windowWidth * EDGE_ZONE_RATIO) {
        newHighlightArea = "left";
      } else if (x > windowWidth * (1 - EDGE_ZONE_RATIO)) {
        newHighlightArea = "right";
      } else if (y > windowHeight * (1 - EDGE_ZONE_RATIO)) {
        newHighlightArea = "bottom";
      }
    }

    dragState = {
      ...dragState,
      floatingX: x,
      floatingY: y,
      highlightedArea: newHighlightArea,
      highlightedGroupId: newHighlightGroupId,
      highlightedDropZone: newHighlightDropZone,
    };
  }

  function handleFloatingDragEnd(): void {
    document.removeEventListener("mousemove", handleFloatingDragMove);
    document.removeEventListener("mouseup", handleFloatingDragEnd);

    if (!dragState.floatingDock) {
      resetDragState();
      return;
    }

    const dock = dragState.floatingDock;
    const {
      highlightedArea,
      highlightedGroupId,
      highlightedDropZone,
      sourcePosition,
    } = dragState;

    if (highlightedGroupId && highlightedArea) {
      if (highlightedDropZone === "center") {
        addDockToGroup(highlightedArea, highlightedGroupId, dock);
      } else {
        const groups = data[highlightedArea];
        const groupIndex = groups.findIndex((g) => g.id === highlightedGroupId);
        const insertIndex =
          highlightedDropZone === "before" ? groupIndex : groupIndex + 1;
        insertNewGroup(highlightedArea, insertIndex, dock);
      }
    } else if (highlightedArea) {
      addNewGroupToArea(highlightedArea, dock);
    } else if (sourcePosition) {
      addNewGroupToArea(sourcePosition, dock);
    }

    resetDragState();
  }

  function addDockToGroup(
    position: DockPosition,
    groupId: string,
    dock: DockItem
  ): void {
    data = {
      ...data,
      [position]: data[position].map((g) =>
        g.id === groupId
          ? { ...g, items: [...g.items, dock], activeTabId: dock.id }
          : g
      ),
    };
  }

  function insertNewGroup(
    position: DockPosition,
    index: number,
    dock: DockItem
  ): void {
    const newGroup: DockGroup = {
      id: generateId(),
      items: [dock],
      activeTabId: dock.id,
      size: 1,
    };

    const groups = [...data[position]];
    groups.splice(index, 0, newGroup);

    data = {
      ...data,
      [position]: groups,
    };
  }

  function addNewGroupToArea(position: DockPosition, dock: DockItem): void {
    const newGroup: DockGroup = {
      id: generateId(),
      items: [dock],
      activeTabId: dock.id,
      size: 1,
    };

    data = {
      ...data,
      [position]: [...data[position], newGroup],
    };
  }

  function resetDragState(): void {
    dragState = {
      active: false,
      dockId: null,
      sourcePosition: null,
      sourceGroupId: null,
      floatingDock: null,
      floatingX: 0,
      floatingY: 0,
      highlightedArea: null,
      highlightedGroupId: null,
      highlightedDropZone: null,
    };
  }

  function resetAllResizeState(): void {
    areaResize = {
      active: false,
      area: null,
      startPos: 0,
      startSize: 0,
    };
    groupResize = {
      active: false,
      position: null,
      groupIndex: -1,
      startPos: 0,
      currentStartSize: 0,
      nextStartSize: 0,
    };
  }

  // Global mouse event handlers
  function handleGlobalMouseMove(event: MouseEvent): void {
    if (areaResize.active) {
      handleAreaResizeMove(event);
    } else if (groupResize.active) {
      handleGroupResizeMove(event);
    }
  }

  function handleGlobalMouseUp(): void {
    resetAllResizeState();
  }

  // Reactive event listener management
  $effect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleGlobalMouseMove);
      document.addEventListener("mouseup", handleGlobalMouseUp);
    } else {
      document.removeEventListener("mousemove", handleGlobalMouseMove);
      document.removeEventListener("mouseup", handleGlobalMouseUp);
    }
  });

  onDestroy(() => {
    document.removeEventListener("mousemove", handleGlobalMouseMove);
    document.removeEventListener("mouseup", handleGlobalMouseUp);
    document.removeEventListener("mousemove", handleFloatingDragMove);
    document.removeEventListener("mouseup", handleFloatingDragEnd);
  });

  // Create drag state object for DockArea
  let dockAreaDragState = $derived({
    active: dragState.active,
    highlightedGroupId: dragState.highlightedGroupId,
    highlightedDropZone: dragState.highlightedDropZone,
  });
</script>

<div class="workspace-container">
  <!-- Drop zone overlays during drag (for empty areas) -->
  {#if dragState.active && !dragState.highlightedGroupId}
    {#if dragState.highlightedArea === "left"}
      <div
        class="drop-zone-overlay overlay-left"
        style="width: {leftAreaWidth}px;"
      ></div>
    {:else if dragState.highlightedArea === "right"}
      <div
        class="drop-zone-overlay overlay-right"
        style="width: {rightAreaWidth}px;"
      ></div>
    {:else if dragState.highlightedArea === "bottom"}
      <div
        class="drop-zone-overlay overlay-bottom"
        style="height: {bottomAreaHeight}px;"
      ></div>
    {/if}
  {/if}

  <!-- Floating dock during drag -->
  {#if dragState.floatingDock}
    <div
      class="floating-dock"
      style="left: {dragState.floatingX - 100}px; top: {dragState.floatingY -
        15}px;"
    >
      <div class="floating-dock-title">{dragState.floatingDock.title}</div>
      <div class="floating-dock-content">
        <p>{dragState.floatingDock.content}</p>
      </div>
    </div>
  {/if}

  <div class="horizontal-layout">
    <!-- Left dock area -->
    {#if data.left.length > 0}
      <div class="dock-area dock-area-left" style="width: {leftAreaWidth}px;">
        <DockArea
          position="left"
          groups={data.left}
          dragState={dockAreaDragState}
          {groupElements}
          onactiveTabChange={(groupId, tabId) =>
            setActiveTab("left", groupId, tabId)}
          onTabReorder={(groupId, items) =>
            handleTabReorder("left", groupId, items)}
          onTabDragStart={(groupId, dockId, x, y) =>
            handleTabDragStart("left", groupId, dockId, x, y)}
          onDockUndock={(groupId, dockId, x, y) =>
            handleDockUndock("left", groupId, dockId, x, y)}
          onGroupResize={(index, e) => startGroupResize("left", index, e)}
          {dockContent}
        />
        <div
          class="area-resizer area-resizer-vertical area-resizer-left"
          role="separator"
          tabindex="0"
          aria-label="Resize left panel"
          onmousedown={(e) => startAreaResize("left", e)}
          onkeydown={(e) => e.key === "Enter" && e.preventDefault()}
        ></div>
      </div>
    {/if}

    <div class="vertical-layout">
      <!-- Main content area -->
      <main class="main-content">
        {#if children}
          {@render children()}
        {/if}
      </main>

      <!-- Bottom dock area -->
      {#if data.bottom.length > 0}
        <div
          class="dock-area dock-area-bottom"
          style="height: {bottomAreaHeight}px;"
        >
          <div
            class="area-resizer area-resizer-horizontal"
            role="separator"
            tabindex="0"
            aria-label="Resize bottom panel"
            onmousedown={(e) => startAreaResize("bottom", e)}
            onkeydown={(e) => e.key === "Enter" && e.preventDefault()}
          ></div>
          <DockArea
            position="bottom"
            groups={data.bottom}
            dragState={dockAreaDragState}
            {groupElements}
            onactiveTabChange={(groupId, tabId) =>
              setActiveTab("bottom", groupId, tabId)}
            onTabReorder={(groupId, items) =>
              handleTabReorder("bottom", groupId, items)}
            onTabDragStart={(groupId, dockId, x, y) =>
              handleTabDragStart("bottom", groupId, dockId, x, y)}
            onDockUndock={(groupId, dockId, x, y) =>
              handleDockUndock("bottom", groupId, dockId, x, y)}
            onGroupResize={(index, e) => startGroupResize("bottom", index, e)}
            {dockContent}
          />
        </div>
      {/if}
    </div>

    <!-- Right dock area -->
    {#if data.right.length > 0}
      <div class="dock-area dock-area-right" style="width: {rightAreaWidth}px;">
        <div
          class="area-resizer area-resizer-vertical area-resizer-right"
          role="separator"
          tabindex="0"
          aria-label="Resize right panel"
          onmousedown={(e) => startAreaResize("right", e)}
          onkeydown={(e) => e.key === "Enter" && e.preventDefault()}
        ></div>
        <DockArea
          position="right"
          groups={data.right}
          dragState={dockAreaDragState}
          {groupElements}
          onactiveTabChange={(groupId, tabId) =>
            setActiveTab("right", groupId, tabId)}
          onTabReorder={(groupId, items) =>
            handleTabReorder("right", groupId, items)}
          onTabDragStart={(groupId, dockId, x, y) =>
            handleTabDragStart("right", groupId, dockId, x, y)}
          onDockUndock={(groupId, dockId, x, y) =>
            handleDockUndock("right", groupId, dockId, x, y)}
          onGroupResize={(index, e) => startGroupResize("right", index, e)}
          {dockContent}
        />
      </div>
    {/if}
  </div>
</div>

<style>
  .workspace-container {
    --resizer-hover-color: #317ae7;
    --drop-zone-bg: rgba(49, 122, 231, 0.15);
    --drop-zone-border: rgba(49, 122, 231, 0.5);
    --border-color: #dadada;

    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .horizontal-layout {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  .vertical-layout {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
  }

  .main-content {
    flex: 1;
    overflow: auto;
    min-height: 0;
  }

  .dock-area {
    display: flex;
    position: relative;
    min-height: 0;
    min-width: 0;
    flex-shrink: 0;
    overflow: visible;
  }

  .dock-area-left,
  .dock-area-right {
    flex-direction: column;
  }

  .dock-area-bottom {
    flex-direction: row;
  }

  /* Drop zone overlays */
  .drop-zone-overlay {
    position: fixed;
    background-color: var(--drop-zone-bg);
    box-shadow: inset 0 0 0 2px var(--drop-zone-border);
    pointer-events: none;
    z-index: 9999;
    animation: fade-in 0.15s ease;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .overlay-left {
    inset: 0 auto 0 0;
  }

  .overlay-right {
    inset: 0 0 0 auto;
  }

  .overlay-bottom {
    inset: auto 0 0 0;
  }

  /* Area resizers */
  .area-resizer {
    position: absolute;
    z-index: 1000;
    flex-shrink: 0;
    background-color: var(--border-color);
    background-clip: content-box;
    transition:
      background-color 0.1s ease,
      background-clip 0.1s ease;
  }

  .area-resizer:hover,
  .area-resizer:active {
    background-color: var(--resizer-hover-color);
    background-clip: border-box;
    z-index: 2000;
  }

  .area-resizer-vertical {
    width: 1px;
    height: 100%;
    top: 0;
    padding: 0 1.5px;
    cursor: ew-resize;
  }

  .area-resizer-left {
    right: -1.5px;
  }

  .area-resizer-right {
    left: -1.5px;
  }

  .area-resizer-horizontal {
    height: 1px;
    width: 100%;
    left: 0;
    top: -1.5px;
    padding: 1.5px 0;
    cursor: ns-resize;
  }

  /* Floating dock during drag */
  .floating-dock {
    position: fixed;
    width: 200px;
    height: 150px;
    z-index: 10000;
    background-color: #ffffff;
    border: 2px solid #317ae7;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    opacity: 0.9;
    pointer-events: none;
    display: flex;
    flex-direction: column;
  }

  .floating-dock-title {
    display: flex;
    align-items: center;
    padding: 5px 10px;
    background-color: #f5f5f5;
    border-bottom: 1px solid #dadada;
    height: 20px;
    box-sizing: border-box;
    overflow: hidden;
    min-width: 0;
    color: #000000df;
  }

  .floating-dock-content {
    flex: 1;
    overflow: hidden;
    padding: 10px;
  }
</style>
