<!--
  @component Tree

  Hierarchical tree component for displaying nested data.
  Provides an expandable/collapsible tree structure with selection support.

  ## Features
  - Hierarchical node display with unlimited nesting depth
  - Expand/collapse nodes with children
  - Single node selection
  - Optional icons for each node
  - Keyboard navigation (Enter/Space to select, Arrow keys to expand/collapse)
  - Double-click to toggle expand/collapse
  - Customizable indentation size
  - Recursive component architecture

  ## Props
  - `nodes: TreeNode[]` - Array of root tree nodes
  - `selectedId: string | null` - ID of currently selected node (default: null)
  - `indentSize: number` - Pixels to indent each nesting level (default: 16)
  - `depth: number` - Current depth level, used internally (default: 0)

  ## Events
  - `select` - Fired when node is selected: `{ node: TreeNode }`
  - `toggle` - Fired when node is expanded/collapsed: `{ node: TreeNode, expanded: boolean }`

  ## TreeNode Interface
  ```typescript
  interface TreeNode {
    id: string;           // Unique identifier
    label: string;        // Display text
    icon?: string;        // Optional icon URL
    children?: TreeNode[]; // Child nodes
    expanded?: boolean;   // Initial expanded state
  }
  ```

  ## Usage Example
  ```svelte
  <Tree
    nodes={[
      { id: "1", label: "Root", children: [
        { id: "1.1", label: "Child 1" },
        { id: "1.2", label: "Child 2" }
      ]}
    ]}
    on:select={(e) => console.log('Selected:', e.detail.node)}
  />
  ```
-->
<script lang="ts" context="module">
  export interface TreeNode {
    id: string;
    label: string;
    icon?: string;
    children?: TreeNode[];
    expanded?: boolean;
  }
</script>

<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import { writable, type Writable } from "svelte/store";
  import arrowRight from "../assets/icons/arrow_right.svg";
  import arrowDown from "../assets/icons/arrow_down.svg";

  export let nodes: TreeNode[] = [];
  export let selectedId: string | null = null;
  export let indentSize: number = 16;
  export let depth: number = 0;
  // Internal prop for sharing expanded store across recursive calls
  export let _expandedStore: Writable<Record<string, boolean>> | null = null;

  const dispatch = createEventDispatcher<{
    select: { node: TreeNode };
    toggle: { node: TreeNode; expanded: boolean };
  }>();

  $: isRoot = depth === 0;

  // Root component creates the store
  const localStore = writable<Record<string, boolean>>({});
  $: expandedStore = _expandedStore !== null ? _expandedStore : localStore;

  // Initialize expanded state from nodes (only at root level)
  function initExpandedState(
    nodeList: TreeNode[],
    state: Record<string, boolean>
  ): Record<string, boolean> {
    nodeList.forEach((node) => {
      if (node.expanded !== undefined && state[node.id] === undefined) {
        state[node.id] = node.expanded;
      }
      if (node.children) {
        initExpandedState(node.children, state);
      }
    });
    return state;
  }

  onMount(() => {
    if (isRoot) {
      expandedStore.update((state) => initExpandedState(nodes, state));
    }
  });

  // Also react to nodes changes
  $: if (isRoot && nodes) {
    expandedStore.update((state) => initExpandedState(nodes, { ...state }));
  }

  function hasChildren(node: TreeNode): boolean {
    return !!node.children && node.children.length > 0;
  }

  function toggleNode(node: TreeNode): void {
    if (!hasChildren(node)) return;

    expandedStore.update((state) => {
      const newExpanded = !state[node.id];
      dispatch("toggle", { node, expanded: newExpanded });
      return { ...state, [node.id]: newExpanded };
    });
  }

  function selectNode(node: TreeNode): void {
    selectedId = node.id;
    dispatch("select", { node });
  }

  function handleKeyDown(event: KeyboardEvent, node: TreeNode): void {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectNode(node);
    } else if (
      event.key === "ArrowRight" &&
      hasChildren(node) &&
      !$expandedStore[node.id]
    ) {
      event.preventDefault();
      toggleNode(node);
    } else if (
      event.key === "ArrowLeft" &&
      hasChildren(node) &&
      $expandedStore[node.id]
    ) {
      event.preventDefault();
      toggleNode(node);
    }
  }

  function handleArrowClick(event: MouseEvent, node: TreeNode): void {
    event.stopPropagation();
    toggleNode(node);
  }

  function forwardSelect(event: CustomEvent<{ node: TreeNode }>) {
    dispatch("select", event.detail);
  }

  function forwardToggle(
    event: CustomEvent<{ node: TreeNode; expanded: boolean }>
  ) {
    dispatch("toggle", event.detail);
  }
</script>

<div class="tree" class:is-root={isRoot} role={isRoot ? "tree" : "group"}>
  {#each nodes as node (node.id)}
    <div class="tree-node">
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <div
        class="tree-item"
        class:selected={selectedId === node.id}
        style="padding-left: {depth * indentSize + 4}px;"
        data-node-id={node.id}
        on:click={() => selectNode(node)}
        on:dblclick={() => toggleNode(node)}
        on:keydown={(e) => handleKeyDown(e, node)}
        role="treeitem"
        tabindex="0"
        aria-expanded={hasChildren(node)
          ? ($expandedStore[node.id] ?? false)
          : undefined}
        aria-selected={selectedId === node.id}
      >
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <span
          class="tree-arrow"
          class:has-children={hasChildren(node)}
          class:expanded={$expandedStore[node.id]}
          on:click={(e) => handleArrowClick(e, node)}
          on:keydown={(e) => e.key === "Enter" && toggleNode(node)}
        >
          {#if hasChildren(node)}
            <img
              src={$expandedStore[node.id] ? arrowDown : arrowRight}
              alt=""
              class="arrow-icon"
            />
          {/if}
        </span>

        {#if node.icon}
          <img src={node.icon} alt="" class="tree-icon" />
        {:else}
          <span class="tree-icon-placeholder"></span>
        {/if}

        <span class="tree-label disable-selection">{node.label}</span>
      </div>

      {#if hasChildren(node) && $expandedStore[node.id]}
        <svelte:self
          nodes={node.children}
          {selectedId}
          {indentSize}
          depth={depth + 1}
          _expandedStore={expandedStore}
          on:select={forwardSelect}
          on:toggle={forwardToggle}
        />
      {/if}
    </div>
  {/each}
</div>

<style>
  .tree {
    display: flex;
    flex-direction: column;
  }

  .tree.is-root {
    width: 100%;
    height: 100%;
    overflow: auto;
    font-size: 12px;
    user-select: none;
  }

  .tree-node {
    display: flex;
    flex-direction: column;
  }

  .tree-item {
    display: flex;
    align-items: center;
    height: 22px;
    padding-right: 8px;
    cursor: pointer;
    white-space: nowrap;
    border-radius: 3px;
    margin: 1px 4px;
  }

  .tree-item:hover {
    background-color: #e8e8e8;
  }

  .tree-item.selected {
    background-color: #d0e4ff;
  }

  .tree-item.selected:hover {
    background-color: #c0d8f8;
  }

  .tree-item:focus {
    outline: 1px solid #317ae7;
    outline-offset: -1px;
  }

  .tree-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-right: 5px;
  }

  .tree-arrow.has-children {
    cursor: pointer;
  }

  .arrow-icon {
    width: 10px;
    height: 10px;
  }

  .tree-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    margin-right: 5px;
    object-fit: contain;
  }

  .tree-icon-placeholder {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    margin-right: 5px;
  }

  .tree-label {
    overflow: hidden;
    text-overflow: ellipsis;
    color: #1a1a1a;
  }
</style>
