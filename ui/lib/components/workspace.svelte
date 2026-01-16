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
  - `state: WorkspaceState` - State object containing left, right, bottom dock groups

  ## Slots
  - default - Main content area (center)
  - `dockContent` - Content for each dock, receives `dock: DockItem` and `position: DockPosition` props

  ## Types
  ```typescript
  interface DockItem {
    id: string;       // Unique dock identifier
    title: string;    // Display title for tab/panel
    content: string;  // Default content (used if no slot provided)
  }

  interface DockGroup {
    id: string;           // Unique group identifier
    items: DockItem[];    // Docks in this group
    activeTabId: string;  // Currently active tab ID
    size: number;         // Flex size for group resizing
  }

  type DockPosition = "left" | "right" | "bottom";

  interface WorkspaceState {
    left: DockGroup[];    // Left dock area groups
    right: DockGroup[];   // Right dock area groups
    bottom: DockGroup[];  // Bottom dock area groups
  }
  ```

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
  <Workspace bind:state={workspaceState}>
    <div>Main content here</div>

    <svelte:fragment slot="dockContent" let:dock let:position>
      {#if dock.id === "explorer"}
        <FileExplorer />
      {:else if dock.id === "console"}
        <Console />
      {:else}
        <p>{dock.content}</p>
      {/if}
    </svelte:fragment>
  </Workspace>
  ```
-->
<script context="module" lang="ts">
  export interface DockItem {
    id: string;
    title: string;
    content: string;
  }

  export interface DockGroup {
    id: string;
    items: DockItem[];
    activeTabId: string;
    size: number;
  }

  export type DockPosition = "left" | "right" | "bottom";

  export interface WorkspaceState {
    left: DockGroup[];
    right: DockGroup[];
    bottom: DockGroup[];
  }
</script>

<script lang="ts">
  import { onDestroy } from "svelte";
  import Panel from "./panel.svelte";
  import Tabs from "./tabs.svelte";

  // Constants
  const AREA_MIN_SIZE = 100;
  const AREA_MAX_SIZE = 600;
  const AREA_DEFAULT_LEFT = 200;
  const AREA_DEFAULT_RIGHT = 250;
  const AREA_DEFAULT_BOTTOM = 200;
  const GROUP_MIN_SIZE = 50;
  const EDGE_ZONE_RATIO = 0.2;

  export let state: WorkspaceState = {
    left: [],
    right: [],
    bottom: [],
  };

  // Area sizes
  let leftAreaWidth = AREA_DEFAULT_LEFT;
  let rightAreaWidth = AREA_DEFAULT_RIGHT;
  let bottomAreaHeight = AREA_DEFAULT_BOTTOM;

  // Area resize state
  type AreaResizeState = {
    active: boolean;
    area: DockPosition | null;
    startPos: number;
    startSize: number;
  };

  let areaResize: AreaResizeState = {
    active: false,
    area: null,
    startPos: 0,
    startSize: 0,
  };

  // Group resize state
  type GroupResizeState = {
    active: boolean;
    position: DockPosition | null;
    groupIndex: number;
    startPos: number;
    currentStartSize: number;
    nextStartSize: number;
  };

  let groupResize: GroupResizeState = {
    active: false,
    position: null,
    groupIndex: -1,
    startPos: 0,
    currentStartSize: 0,
    nextStartSize: 0,
  };

  // Drag state for dock repositioning
  type DropZone = "center" | "before" | "after";

  type DragState = {
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
  };

  let dragState: DragState = {
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

  // Track group element refs for drop zone detection
  let groupElements: Map<string, HTMLElement> = new Map();

  // Computed helpers
  $: leftGroups = state.left;
  $: rightGroups = state.right;
  $: bottomGroups = state.bottom;

  function getGroupsForPosition(position: DockPosition): DockGroup[] {
    return state[position];
  }

  function isHorizontalSplit(position: DockPosition): boolean {
    return position === "bottom";
  }

  // Generate unique ID
  function generateId(): string {
    return Math.random().toString(36).substring(2, 11);
  }

  // Update active tab for a group
  function setActiveTab(
    position: DockPosition,
    groupId: string,
    tabId: string
  ) {
    state = {
      ...state,
      [position]: state[position].map((g) =>
        g.id === groupId ? { ...g, activeTabId: tabId } : g
      ),
    };
  }

  // Area resize handlers
  function startAreaResize(area: DockPosition, event: MouseEvent) {
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

  function handleAreaResizeMove(event: MouseEvent) {
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
  ) {
    const groups = getGroupsForPosition(position);
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

    state = {
      ...state,
      [position]: state[position].map((g) => {
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

  function handleGroupResizeMove(event: MouseEvent) {
    if (!groupResize.active || !groupResize.position) return;

    const { position, groupIndex, startPos, currentStartSize, nextStartSize } =
      groupResize;
    const groups = getGroupsForPosition(position);
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

    state = {
      ...state,
      [position]: state[position].map((g) => {
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
  ) {
    const groups = getGroupsForPosition(position);
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

    // Remove dock from source group
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
  ) {
    handleDockUndock(position, groupId, dockId, x, y);
  }

  function handleTabReorder(
    position: DockPosition,
    groupId: string,
    newItems: DockItem[]
  ) {
    state = {
      ...state,
      [position]: state[position].map((g) =>
        g.id === groupId ? { ...g, items: newItems } : g
      ),
    };
  }

  function removeDockFromGroup(
    position: DockPosition,
    groupId: string,
    dockId: string
  ) {
    state = {
      ...state,
      [position]: state[position]
        .map((g) => {
          if (g.id !== groupId) return g;
          const newItems = g.items.filter((d) => d.id !== dockId);
          const newActiveTabId =
            g.activeTabId === dockId ? (newItems[0]?.id ?? "") : g.activeTabId;
          return { ...g, items: newItems, activeTabId: newActiveTabId };
        })
        .filter((g) => g.items.length > 0), // Remove empty groups
    };
  }

  function handleFloatingDragMove(event: MouseEvent) {
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
        // Find which position this group belongs to
        const position = findGroupPosition(groupId);
        if (position) {
          newHighlightArea = position;
          newHighlightGroupId = groupId;

          // Determine drop zone (center, before, after)
          const isHorizontal = isHorizontalSplit(position);
          if (isHorizontal) {
            // Horizontal split: left/right zones
            const relX = (x - rect.left) / rect.width;
            if (relX < 0.25) {
              newHighlightDropZone = "before";
            } else if (relX > 0.75) {
              newHighlightDropZone = "after";
            } else {
              newHighlightDropZone = "center";
            }
          } else {
            // Vertical split: top/bottom zones
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
      if (leftGroups.length > 0 && x < leftAreaWidth) {
        newHighlightArea = "left";
      } else if (rightGroups.length > 0 && x > windowWidth - rightAreaWidth) {
        newHighlightArea = "right";
      } else if (
        bottomGroups.length > 0 &&
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

  function findGroupPosition(groupId: string): DockPosition | null {
    if (state.left.some((g) => g.id === groupId)) return "left";
    if (state.right.some((g) => g.id === groupId)) return "right";
    if (state.bottom.some((g) => g.id === groupId)) return "bottom";
    return null;
  }

  function handleFloatingDragEnd() {
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
      // Dropping on an existing group
      if (highlightedDropZone === "center") {
        // Add to existing group as a tab
        addDockToGroup(highlightedArea, highlightedGroupId, dock);
      } else {
        // Create new group before/after
        const groups = getGroupsForPosition(highlightedArea);
        const groupIndex = groups.findIndex((g) => g.id === highlightedGroupId);
        const insertIndex =
          highlightedDropZone === "before" ? groupIndex : groupIndex + 1;
        insertNewGroup(highlightedArea, insertIndex, dock);
      }
    } else if (highlightedArea) {
      // Dropping on an area (but not on a specific group)
      // Add as new group at the end
      addNewGroupToArea(highlightedArea, dock);
    } else if (sourcePosition) {
      // No valid drop target, return to original position
      addNewGroupToArea(sourcePosition, dock);
    }

    resetDragState();
  }

  function addDockToGroup(
    position: DockPosition,
    groupId: string,
    dock: DockItem
  ) {
    state = {
      ...state,
      [position]: state[position].map((g) =>
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
  ) {
    const newGroup: DockGroup = {
      id: generateId(),
      items: [dock],
      activeTabId: dock.id,
      size: 1,
    };

    const groups = [...state[position]];
    groups.splice(index, 0, newGroup);

    state = {
      ...state,
      [position]: groups,
    };
  }

  function addNewGroupToArea(position: DockPosition, dock: DockItem) {
    const newGroup: DockGroup = {
      id: generateId(),
      items: [dock],
      activeTabId: dock.id,
      size: 1,
    };

    state = {
      ...state,
      [position]: [...state[position], newGroup],
    };
  }

  // Utility functions
  function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }

  function resetDragState() {
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

  function resetAllResizeState() {
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
  function handleGlobalMouseMove(event: MouseEvent) {
    if (areaResize.active) {
      handleAreaResizeMove(event);
    } else if (groupResize.active) {
      handleGroupResizeMove(event);
    }
  }

  function handleGlobalMouseUp() {
    resetAllResizeState();
  }

  // Reactive event listener management
  $: isResizing = areaResize.active || groupResize.active;

  $: if (isResizing) {
    document.addEventListener("mousemove", handleGlobalMouseMove);
    document.addEventListener("mouseup", handleGlobalMouseUp);
  } else {
    document.removeEventListener("mousemove", handleGlobalMouseMove);
    document.removeEventListener("mouseup", handleGlobalMouseUp);
  }

  // Cleanup on component destroy
  onDestroy(() => {
    document.removeEventListener("mousemove", handleGlobalMouseMove);
    document.removeEventListener("mouseup", handleGlobalMouseUp);
    document.removeEventListener("mousemove", handleFloatingDragMove);
    document.removeEventListener("mouseup", handleFloatingDragEnd);
  });

  // Helper to get drop zone highlight class
  function getDropZoneClass(groupId: string): string {
    if (!dragState.active || dragState.highlightedGroupId !== groupId)
      return "";
    return `drop-highlight drop-${dragState.highlightedDropZone}`;
  }

  // Svelte action for registering group elements
  function registerGroupRef(element: HTMLElement, groupId: string) {
    groupElements.set(groupId, element);

    return {
      update(newGroupId: string) {
        groupElements.delete(groupId);
        groupId = newGroupId;
        groupElements.set(groupId, element);
      },
      destroy() {
        groupElements.delete(groupId);
      },
    };
  }
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
    {#if leftGroups.length > 0}
      <div class="dock-area dock-area-left" style="width: {leftAreaWidth}px;">
        {#each leftGroups as group, index (group.id)}
          <div
            class="group-wrapper {getDropZoneClass(group.id)}"
            style="flex-grow: {group.size};"
            use:registerGroupRef={group.id}
          >
            {#if group.items.length === 1}
              <!-- Single panel: show panel title, hide tab bar -->
              {@const dock = group.items[0]}
              <Panel
                position="left"
                title={dock.title}
                showTitle={true}
                on:undock={(e) =>
                  handleDockUndock(
                    "left",
                    group.id,
                    dock.id,
                    e.detail.x,
                    e.detail.y
                  )}
              >
                <div class="panel-content-wrapper">
                  <slot name="dockContent" {dock} position="left">
                    <p>{dock.content}</p>
                  </slot>
                </div>
              </Panel>
            {:else}
              <!-- Multiple panels: show tab bar, hide panel titles -->
              <Tabs
                tabs={group.items.map((d) => ({ id: d.id, title: d.title }))}
                activeTabId={group.activeTabId}
                hideSingleTab={false}
                draggable={true}
                reorderable={true}
                tabPosition="left"
                on:change={(e) => setActiveTab("left", group.id, e.detail)}
                on:reorder={(e) =>
                  handleTabReorder(
                    "left",
                    group.id,
                    e.detail.tabs.map(
                      (t) => group.items.find((d) => d.id === t.id)!
                    )
                  )}
                on:tabdragstart={(e) =>
                  handleTabDragStart(
                    "left",
                    group.id,
                    e.detail.tabId,
                    e.detail.x,
                    e.detail.y
                  )}
              >
                <svelte:fragment let:activeTabId>
                  {#each group.items as dock (dock.id)}
                    {#if dock.id === activeTabId}
                      <Panel
                        position="left"
                        title={dock.title}
                        showTitle={false}
                      >
                        <div class="panel-content-wrapper">
                          <slot name="dockContent" {dock} position="left">
                            <p>{dock.content}</p>
                          </slot>
                        </div>
                      </Panel>
                    {/if}
                  {/each}
                </svelte:fragment>
              </Tabs>
            {/if}

            <!-- Drop zone indicators -->
            {#if dragState.active && dragState.highlightedGroupId === group.id}
              <div
                class="drop-indicator drop-indicator-{dragState.highlightedDropZone} drop-indicator-vertical"
              ></div>
            {/if}
          </div>
          {#if index < leftGroups.length - 1}
            <!-- svelte-ignore a11y-no-noninteractive-tabindex a11y-no-noninteractive-element-interactions -->
            <div
              class="group-resizer group-resizer-horizontal"
              role="separator"
              tabindex="0"
              aria-label="Resize dock group"
              on:mousedown={(e) => startGroupResize("left", index, e)}
              on:keydown={(e) => e.key === "Enter" && e.preventDefault()}
            ></div>
          {/if}
        {/each}
        <!-- svelte-ignore a11y-no-noninteractive-tabindex a11y-no-noninteractive-element-interactions -->
        <div
          class="area-resizer area-resizer-vertical"
          role="separator"
          tabindex="0"
          aria-label="Resize left panel"
          on:mousedown={(e) => startAreaResize("left", e)}
          on:keydown={(e) => e.key === "Enter" && e.preventDefault()}
        ></div>
      </div>
    {/if}

    <div class="vertical-layout">
      <!-- Main content area -->
      <main class="main-content">
        <slot />
      </main>

      <!-- Bottom dock area -->
      {#if bottomGroups.length > 0}
        <div
          class="dock-area dock-area-bottom"
          style="height: {bottomAreaHeight}px;"
        >
          <!-- svelte-ignore a11y-no-noninteractive-tabindex a11y-no-noninteractive-element-interactions -->
          <div
            class="area-resizer area-resizer-horizontal"
            role="separator"
            tabindex="0"
            aria-label="Resize bottom panel"
            on:mousedown={(e) => startAreaResize("bottom", e)}
            on:keydown={(e) => e.key === "Enter" && e.preventDefault()}
          ></div>
          {#each bottomGroups as group, index (group.id)}
            <div
              class="group-wrapper {getDropZoneClass(group.id)}"
              style="flex-grow: {group.size};"
              use:registerGroupRef={group.id}
            >
              {#if group.items.length === 1}
                {@const dock = group.items[0]}
                <Panel
                  position="bottom"
                  title={dock.title}
                  showTitle={true}
                  on:undock={(e) =>
                    handleDockUndock(
                      "bottom",
                      group.id,
                      dock.id,
                      e.detail.x,
                      e.detail.y
                    )}
                >
                  <div class="panel-content-wrapper">
                    <slot name="dockContent" {dock} position="bottom">
                      <p>{dock.content}</p>
                    </slot>
                  </div>
                </Panel>
              {:else}
                <Tabs
                  tabs={group.items.map((d) => ({ id: d.id, title: d.title }))}
                  activeTabId={group.activeTabId}
                  hideSingleTab={false}
                  draggable={true}
                  reorderable={true}
                  on:change={(e) => setActiveTab("bottom", group.id, e.detail)}
                  on:reorder={(e) =>
                    handleTabReorder(
                      "bottom",
                      group.id,
                      e.detail.tabs.map(
                        (t) => group.items.find((d) => d.id === t.id)!
                      )
                    )}
                  on:tabdragstart={(e) =>
                    handleTabDragStart(
                      "bottom",
                      group.id,
                      e.detail.tabId,
                      e.detail.x,
                      e.detail.y
                    )}
                >
                  <svelte:fragment let:activeTabId>
                    {#each group.items as dock (dock.id)}
                      {#if dock.id === activeTabId}
                        <Panel
                          position="bottom"
                          title={dock.title}
                          showTitle={false}
                        >
                          <div class="panel-content-wrapper">
                            <slot name="dockContent" {dock} position="bottom">
                              <p>{dock.content}</p>
                            </slot>
                          </div>
                        </Panel>
                      {/if}
                    {/each}
                  </svelte:fragment>
                </Tabs>
              {/if}

              {#if dragState.active && dragState.highlightedGroupId === group.id}
                <div
                  class="drop-indicator drop-indicator-{dragState.highlightedDropZone} drop-indicator-horizontal"
                ></div>
              {/if}
            </div>
            {#if index < bottomGroups.length - 1}
              <!-- svelte-ignore a11y-no-noninteractive-tabindex a11y-no-noninteractive-element-interactions -->
              <div
                class="group-resizer group-resizer-vertical"
                role="separator"
                tabindex="0"
                aria-label="Resize dock group"
                on:mousedown={(e) => startGroupResize("bottom", index, e)}
                on:keydown={(e) => e.key === "Enter" && e.preventDefault()}
              ></div>
            {/if}
          {/each}
        </div>
      {/if}
    </div>

    <!-- Right dock area -->
    {#if rightGroups.length > 0}
      <div class="dock-area dock-area-right" style="width: {rightAreaWidth}px;">
        <!-- svelte-ignore a11y-no-noninteractive-tabindex a11y-no-noninteractive-element-interactions -->
        <div
          class="area-resizer area-resizer-vertical"
          role="separator"
          tabindex="0"
          aria-label="Resize right panel"
          on:mousedown={(e) => startAreaResize("right", e)}
          on:keydown={(e) => e.key === "Enter" && e.preventDefault()}
        ></div>
        {#each rightGroups as group, index (group.id)}
          <div
            class="group-wrapper {getDropZoneClass(group.id)}"
            style="flex-grow: {group.size};"
            use:registerGroupRef={group.id}
          >
            {#if group.items.length === 1}
              {@const dock = group.items[0]}
              <Panel
                position="right"
                title={dock.title}
                showTitle={true}
                on:undock={(e) =>
                  handleDockUndock(
                    "right",
                    group.id,
                    dock.id,
                    e.detail.x,
                    e.detail.y
                  )}
              >
                <div class="panel-content-wrapper">
                  <slot name="dockContent" {dock} position="right">
                    <p>{dock.content}</p>
                  </slot>
                </div>
              </Panel>
            {:else}
              <Tabs
                tabs={group.items.map((d) => ({ id: d.id, title: d.title }))}
                activeTabId={group.activeTabId}
                hideSingleTab={false}
                draggable={true}
                reorderable={true}
                tabPosition="right"
                on:change={(e) => setActiveTab("right", group.id, e.detail)}
                on:reorder={(e) =>
                  handleTabReorder(
                    "right",
                    group.id,
                    e.detail.tabs.map(
                      (t) => group.items.find((d) => d.id === t.id)!
                    )
                  )}
                on:tabdragstart={(e) =>
                  handleTabDragStart(
                    "right",
                    group.id,
                    e.detail.tabId,
                    e.detail.x,
                    e.detail.y
                  )}
              >
                <svelte:fragment let:activeTabId>
                  {#each group.items as dock (dock.id)}
                    {#if dock.id === activeTabId}
                      <Panel
                        position="right"
                        title={dock.title}
                        showTitle={false}
                      >
                        <div class="panel-content-wrapper">
                          <slot name="dockContent" {dock} position="right">
                            <p>{dock.content}</p>
                          </slot>
                        </div>
                      </Panel>
                    {/if}
                  {/each}
                </svelte:fragment>
              </Tabs>
            {/if}

            {#if dragState.active && dragState.highlightedGroupId === group.id}
              <div
                class="drop-indicator drop-indicator-{dragState.highlightedDropZone} drop-indicator-vertical"
              ></div>
            {/if}
          </div>
          {#if index < rightGroups.length - 1}
            <!-- svelte-ignore a11y-no-noninteractive-tabindex a11y-no-noninteractive-element-interactions -->
            <div
              class="group-resizer group-resizer-horizontal"
              role="separator"
              tabindex="0"
              aria-label="Resize dock group"
              on:mousedown={(e) => startGroupResize("right", index, e)}
              on:keydown={(e) => e.key === "Enter" && e.preventDefault()}
            ></div>
          {/if}
        {/each}
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

  /* Layout containers */
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

  /* Main content */
  .main-content {
    flex: 1;
    overflow: auto;
    min-height: 0;
  }

  /* Dock areas */
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

  /* Group wrappers */
  .group-wrapper {
    position: relative;
    flex: 1 1 0;
    min-height: 0;
    min-width: 0;
    display: flex;
    flex-direction: column;
    overflow: visible;
  }

  .dock-area-bottom .group-wrapper {
    flex-direction: row;
  }

  .group-wrapper > :global(.panel-widget),
  .group-wrapper > :global(.tabs-widget) {
    flex: 1;
    min-height: 0;
    min-width: 0;
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

  /* Drop indicators on groups */
  .drop-indicator {
    position: absolute;
    background-color: var(--drop-zone-bg);
    border: 2px solid var(--drop-zone-border);
    pointer-events: none;
    z-index: 100;
    animation: fade-in 0.1s ease;
  }

  /* Vertical split (left/right areas): top/bottom zones */
  .drop-indicator-vertical.drop-indicator-before {
    inset: 0 0 auto 0;
    height: 25%;
  }

  .drop-indicator-vertical.drop-indicator-after {
    inset: auto 0 0 0;
    height: 25%;
  }

  .drop-indicator-vertical.drop-indicator-center {
    inset: 25% 0;
  }

  /* Horizontal split (bottom area): left/right zones */
  .drop-indicator-horizontal.drop-indicator-before {
    inset: 0 auto 0 0;
    width: 25%;
  }

  .drop-indicator-horizontal.drop-indicator-after {
    inset: 0 0 0 auto;
    width: 25%;
  }

  .drop-indicator-horizontal.drop-indicator-center {
    inset: 0 25%;
  }

  /* Resizers - shared styles */
  .group-resizer,
  .area-resizer {
    flex-shrink: 0;
    background-color: var(--border-color);
    background-clip: content-box;
    transition:
      background-color 0.1s ease,
      background-clip 0.1s ease;
  }

  .group-resizer:hover,
  .group-resizer:active,
  .area-resizer:hover,
  .area-resizer:active {
    background-color: var(--resizer-hover-color);
    background-clip: border-box;
    z-index: 2000;
  }

  /* Group resizers */
  .group-resizer {
    z-index: 500;
  }

  .group-resizer-horizontal {
    height: 1px;
    width: 100%;
    padding: 1.5px 0;
    margin: -1.5px 0;
    cursor: ns-resize;
  }

  .group-resizer-vertical {
    width: 1px;
    height: 100%;
    padding: 0 1.5px;
    margin: 0 -1.5px;
    cursor: ew-resize;
  }

  /* Area resizers */
  .area-resizer {
    position: absolute;
    z-index: 1000;
  }

  .area-resizer-vertical {
    width: 1px;
    height: 100%;
    top: 0;
    padding: 0 1.5px;
    cursor: ew-resize;
  }

  .dock-area-left .area-resizer-vertical {
    right: -1.5px;
  }

  .dock-area-right .area-resizer-vertical {
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

  .panel-content-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    box-sizing: border-box;
  }

  .panel-content-wrapper > :global(*) {
    flex: 1;
    min-height: 0;
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
