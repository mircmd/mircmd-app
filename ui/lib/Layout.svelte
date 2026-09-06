<!--
  @component DockArea

  Internal component for rendering a dock area (left, right, or bottom) within Workspace.
  Handles groups of dockable panels with resize functionality.

  ## Features
  - Renders multiple dock groups
  - Resizable groups within the area
  - Single panel mode: shows Panel with title bar instead of Tabs
  - Multi panel mode: shows Tabs with tab bar
  - Tab reordering and dragging support
  - Drop zone indicators during drag operations

  ## Layout Structure for vertical orientation
  ```
  ┌─────────────────────────────────┐
  │                                 │
  │             ITEM 1              │
  │                                 │
  ├─────────────────────────────────┤
  │                                 │
  │             ITEM 2              │
  │                                 │
  └─────────────────────────────────┘
  ```

  ## Layout Structure for horizontal orientation
  ```
  ┌────────────────┬────────────────┐
  │                │                │
  │                │                │
  │     ITEM 1     │     ITEM 2     │
  │                │                │
  │                │                │
  └────────────────┴────────────────┘
  ```
-->

<script lang="ts" module>
  let id_counter = 0;
  function generateId() {
    return "layout-item-" + (id_counter++).toString();
  }

  export type Orientation = "horizontal" | "vertical";

  export type LayoutItem = {
    id?: string;
    visible?: boolean;
    snippet?: Snippet;
    component?: Component<any>;
    props?: Record<string, any>;
  };

  export type LayoutItemHandle = {
    id: string;
    setVisible(visible: boolean): void;
    remove(): void;
  };

  export type LayoutWidgetInput =
    | Snippet
    | {
        component: Component<any>;
        props?: Record<string, any>;
      };
</script>

<script lang="ts">
  import type { Component, Snippet } from "svelte";

  interface Props {
    orientation?: Orientation;
    layoutItems?: LayoutItem[];
    isEmpty?: boolean;
  }

  let {
    orientation: initialOrientation = "horizontal",
    layoutItems: initialLayoutItems = [],
    isEmpty = $bindable(true),
  }: Props = $props();
  let orientation = $state(initialOrientation);
  let layoutItems = $state(
    [...initialLayoutItems].map((layout_item) => ({
      ...layout_item,
      id: generateId(),
    })),
  );

  $effect(() => {
    // TODO: treat as empty when no *visible* items remain
    isEmpty = layoutItems.length === 0;
  });

  export function addWidget(widget: LayoutWidgetInput): LayoutItemHandle {
    const id = generateId();
    if (typeof widget === "function") {
      layoutItems.push({
        id,
        visible: true,
        snippet: widget,
      });
    } else {
      layoutItems.push({
        id,
        visible: true,
        component: widget.component,
        props: widget.props ?? {},
      });
    }

    return {
      id,
      setVisible: (visible: boolean) => {
        // TODO: update item.visible and recompute isEmpty / separators
        const item = layoutItems.find((entry) => entry.id === id);
        if (item) item.visible = visible;
      },
      remove: () => {
        // TODO: idempotent remove
        layoutItems = layoutItems.filter((entry) => entry.id !== id);
      },
    };
  }
</script>

<div class="layout" class:horizontal={orientation === "horizontal"} class:vertical={orientation === "vertical"}>
  {#each layoutItems as layout_item, index (layout_item.id)}
    <div class="layout-item">
      {#if layout_item.component}
        {@const Cmp = layout_item.component}
        <Cmp {...layout_item.props} />
      {:else if layout_item.snippet}
        {@render layout_item.snippet()}
      {:else}
        <p>No component or snippet found for tab {index}</p>
      {/if}
    </div>
  {/each}
</div>

<style>
  .layout {
    display: flex;
    width: 100%;
    height: 100%;
  }

  .layout.horizontal {
    flex-direction: row;
  }

  .layout.vertical {
    flex-direction: column;
  }

  .layout-item {
    flex: 1;
    min-width: 0;
    min-height: 0;
    display: flex;
  }

  .layout-item > :global(*) {
    flex: 1;
    width: 100%;
    height: 100%;
  }

  .layout.horizontal .layout-item:not(:last-child) {
    border-right: 1px solid #dadada;
  }

  .layout.vertical .layout-item:not(:last-child) {
    border-bottom: 1px solid #dadada;
  }
</style>
