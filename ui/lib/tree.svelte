<!--
  @component Tree

  Hierarchical tree component for displaying nested data.
  Provides an expandable/collapsible tree structure with selection support.

  ## Features
  - Hierarchical node display with unlimited nesting depth
  - Expand/collapse nodes with children
  - Single node selection with two-way binding
  - Optional icons for each node
  - Keyboard navigation (Enter/Space to select, Arrow keys to expand/collapse)
  - Double-click to toggle expand/collapse
  - Customizable indentation size
  - Recursive component architecture with shared state via context

  ## Props
  - `nodes: TreeNode[]` - Array of root tree nodes
  - `selectedId: string | null` - ID of currently selected node, supports binding (default: null)
  - `indentSize: number` - Pixels to indent each nesting level (default: 16)
  - `onselect: (node: TreeNode) => void` - Callback when node is selected
  - `ontoggle: (node: TreeNode, expanded: boolean) => void` - Callback when node is expanded/collapsed

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
    bind:selectedId
    onselect={(node) => console.log('Selected:', node)}
  />
  ```
-->
<script lang="ts" module>
  export interface TreeNode {
    id: string;
    label: string;
    icon?: string;
    children?: TreeNode[];
    expanded?: boolean;
  }

  export type ExpandedState = Record<string, boolean>;
</script>

<script lang="ts">
  import { onMount } from "svelte";
  import { get, writable, type Writable } from "svelte/store";
  import arrowDown from "../assets/icons/arrow_down.svg";
  import arrowRight from "../assets/icons/arrow_right.svg";
  import Tree from "./tree.svelte";

  interface Props {
    nodes: TreeNode[];
    selectedId?: string | null;
    expandedState?: Record<string, boolean>;
    indentSize?: number;
    onselect?: (node: TreeNode) => void;
    ontoggle?: (node: TreeNode, expanded: boolean) => void;
    _depth?: number;
    _expandedStore?: Writable<Record<string, boolean>>;
  }

  let {
    nodes = [],
    selectedId = $bindable(null),
    expandedState: externalExpandedState = $bindable({}),
    indentSize = 16,
    onselect,
    ontoggle,
    _depth = 0,
    _expandedStore,
  }: Props = $props();

  // Compute isRoot once at initialization - _depth is a constant prop
  const isRoot = _depth === 0;

  // Use store for shared expanded state across recursive components
  // Pass store explicitly as prop to avoid context issues with conditional rendering
  const expandedStore: Writable<Record<string, boolean>> = isRoot
    ? writable<Record<string, boolean>>(externalExpandedState)
    : _expandedStore!;

  // Local reactive copy of expanded state for this component
  let expandedState: Record<string, boolean> = $state(get(expandedStore));

  // Subscribe to store changes on mount
  onMount(() => {
    const unsubscribe = expandedStore.subscribe((value) => {
      expandedState = value;
      if (isRoot) {
        externalExpandedState = value;
      }
    });
    return unsubscribe;
  });

  // Sync external state changes to internal store (only for root)
  $effect(() => {
    if (isRoot && externalExpandedState) {
      const currentStore = get(expandedStore);
      if (
        JSON.stringify(currentStore) !== JSON.stringify(externalExpandedState)
      ) {
        expandedStore.set(externalExpandedState);
      }
    }
  });

  // Initialize expanded state from nodes
  function initExpandedState(nodeList: TreeNode[]): void {
    expandedStore.update((current) => {
      const updates: Record<string, boolean> = {};
      function traverse(list: TreeNode[]): void {
        for (const node of list) {
          if (node.expanded !== undefined && current[node.id] === undefined) {
            updates[node.id] = node.expanded;
          }
          if (node.children) {
            traverse(node.children);
          }
        }
      }
      traverse(nodeList);
      return Object.keys(updates).length > 0
        ? { ...current, ...updates }
        : current;
    });
  }

  onMount(() => {
    if (isRoot) {
      initExpandedState(nodes);
    }
  });

  // React to nodes changes
  $effect(() => {
    if (isRoot && nodes) {
      initExpandedState(nodes);
    }
  });

  function hasChildren(node: TreeNode): boolean {
    return !!node.children && node.children.length > 0;
  }

  function isExpanded(nodeId: string): boolean {
    return expandedState[nodeId] ?? false;
  }

  function toggleNode(node: TreeNode): void {
    if (!hasChildren(node)) return;
    expandedStore.update((current) => {
      const newExpanded = !current[node.id];
      ontoggle?.(node, newExpanded);
      return { ...current, [node.id]: newExpanded };
    });
  }

  function selectNode(node: TreeNode): void {
    selectedId = node.id;
    onselect?.(node);
  }

  function handleKeyDown(event: KeyboardEvent, node: TreeNode): void {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectNode(node);
    } else if (
      event.key === "ArrowRight" &&
      hasChildren(node) &&
      !isExpanded(node.id)
    ) {
      event.preventDefault();
      toggleNode(node);
    } else if (
      event.key === "ArrowLeft" &&
      hasChildren(node) &&
      isExpanded(node.id)
    ) {
      event.preventDefault();
      toggleNode(node);
    }
  }

  function handleArrowClick(event: MouseEvent, node: TreeNode): void {
    event.stopPropagation();
    toggleNode(node);
  }
</script>

<div class="tree" class:is-root={isRoot} role={isRoot ? "tree" : "group"}>
  {#each nodes as node (node.id)}
    <div class="tree-node">
      <div
        class="tree-item"
        class:selected={selectedId === node.id}
        style="padding-left: {_depth * indentSize + 4}px;"
        data-node-id={node.id}
        onclick={() => selectNode(node)}
        ondblclick={() => toggleNode(node)}
        onkeydown={(e) => handleKeyDown(e, node)}
        role="treeitem"
        tabindex="0"
        aria-expanded={hasChildren(node) ? isExpanded(node.id) : undefined}
        aria-selected={selectedId === node.id}
      >
        <span
          class="tree-arrow"
          class:has-children={hasChildren(node)}
          class:expanded={isExpanded(node.id)}
          onclick={(e) => handleArrowClick(e, node)}
          onkeydown={(e) => e.key === "Enter" && toggleNode(node)}
          role="button"
          tabindex="-1"
        >
          {#if hasChildren(node)}
            <img
              src={isExpanded(node.id) ? arrowDown : arrowRight}
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

      {#if hasChildren(node) && isExpanded(node.id)}
        <Tree
          nodes={node.children!}
          bind:selectedId
          {indentSize}
          {onselect}
          {ontoggle}
          _depth={_depth + 1}
          _expandedStore={expandedStore}
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
