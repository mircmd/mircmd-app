<!--
  @component Workspace

  Main workspace layout component with dock panels.
  Provides a flexible layout system with dock areas on left, right, and bottom sides.

  ## Layout Structure
  ```
  ┌───────┬─────────────────┬───────┐
  │       │                 │       │
  │       │     MAIN        │       │
  │ LEFT  │    CONTENT      │ RIGHT │
  │       │                 │       │
  │       ├─────────────────┤       │
  │       │    BOTTOM       │       │
  └───────┴─────────────────┴───────┘
  ```
-->
<script lang="ts">
  import type { Snippet } from "svelte";
  import Layout from "./Layout.svelte";

  interface Props {
    centralContent: Snippet;
  }

  let { centralContent }: Props = $props();

  let leftDock: ReturnType<typeof Layout> = $state()!;
  let rightDock: ReturnType<typeof Layout> = $state()!;
  let bottomDock: ReturnType<typeof Layout> = $state()!;
  let isLeftEmpty = $state(true);
  let isRightEmpty = $state(true);
  let isBottomEmpty = $state(true);

  export function addWidgetToDock(area: "left" | "right" | "bottom", content: Snippet) {
    if (area === "left") leftDock.addWidget(content);
    else if (area === "right") rightDock.addWidget(content);
    else if (area === "bottom") bottomDock.addWidget(content);
  }
</script>

<div
  class="workspace"
  style:--left-width={isLeftEmpty ? "0px" : "200px"}
  style:--right-width={isRightEmpty ? "0px" : "200px"}
  style:--bottom-height={isBottomEmpty ? "0px" : "150px"}
>
  <div class="left-dock" class:hidden={isLeftEmpty}>
    <Layout bind:this={leftDock} bind:isEmpty={isLeftEmpty} orientation="vertical" />
  </div>
  <div class="central-content">
    {@render centralContent()}
  </div>
  <div class="bottom-dock" class:hidden={isBottomEmpty}>
    <Layout bind:this={bottomDock} bind:isEmpty={isBottomEmpty} orientation="horizontal" />
  </div>
  <div class="right-dock" class:hidden={isRightEmpty}>
    <Layout bind:this={rightDock} bind:isEmpty={isRightEmpty} orientation="vertical" />
  </div>
</div>

<style>
  .workspace {
    display: grid;
    grid-template-columns: var(--left-width) 1fr var(--right-width);
    grid-template-rows: 1fr var(--bottom-height);
    grid-template-areas:
      "left central right"
      "left bottom right";
    flex: 1;
    min-height: 0;
    min-width: 0;
  }

  .left-dock {
    grid-area: left;
    overflow: hidden;
    border-right: 1px solid #dadada;
  }

  .left-dock.hidden {
    border-right: none;
  }

  .right-dock {
    grid-area: right;
    overflow: hidden;
    border-left: 1px solid #dadada;
  }

  .right-dock.hidden {
    border-left: none;
  }

  .bottom-dock {
    grid-area: bottom;
    overflow: hidden;
    border-top: 1px solid #dadada;
  }

  .bottom-dock.hidden {
    border-top: none;
  }

  .central-content {
    grid-area: central;
    overflow: auto;
    background-color: #ffffff;
    min-width: 0;
    min-height: 0;
  }
</style>
