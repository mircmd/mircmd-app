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
    name: string;        // Display text
    type: string;        // Type of the node
    icon?: string;        // Optional icon URL
    children?: TreeNode[]; // Child nodes
    expanded?: boolean;   // Initial expanded state
  }
  ```
-->
<script lang="ts" module>
  export interface TreeNode {
    id: string;
    label: string;
    type: string;
    icon: string;
    children: TreeNode[];
    expanded: boolean;
    selected: boolean;
  }

  const DEFAULT_ROOT_NODE: TreeNode = {
    id: "00000000-0000-0000-0000-000000000000",
    label: "Root",
    type: "root",
    icon: "",
    children: [],
    expanded: true,
    selected: false,
  };
</script>

<script lang="ts">
  import { slide } from "svelte/transition";
  import arrowIcon from "../assets/icons/tree_arrow.svg";
  import fileIcon from "../assets/icons/tree_file.svg";
  import folderIcon from "../assets/icons/tree_folder.svg";

  interface Props {
    root_node?: TreeNode;
    indentSize?: number;
    showIcons?: boolean;
    oncontextmenu?: (event: MouseEvent, node: TreeNode | null) => void;
  }

  let {
    root_node: initialRootNode = DEFAULT_ROOT_NODE,
    indentSize: initialIndentSize = 23,
    showIcons: initialShowIcons = true,
    oncontextmenu,
  }: Props = $props();
  let root_node = $state(initialRootNode);
  let indentSize = $state(initialIndentSize);
  let showIcons = $state(initialShowIcons);

  export function getRootNode(): TreeNode {
    return root_node;
  }

  export function setRootNode(node: TreeNode) {
    root_node = node;
  }

  export function setIndentSize(size: number) {
    indentSize = size;
  }

  export function setShowIcons(value: boolean) {
    showIcons = value;
  }

  function contextMenuHandler(event: MouseEvent) {
    event.preventDefault();

    const target = event.target as HTMLElement;
    const treeItem = target.closest(".tree-row");
    if (!treeItem) {
      oncontextmenu?.(event, null);
      return;
    }

    const nodeId = treeItem.getAttribute("data-node-id");
    if (nodeId) {
      oncontextmenu?.(event, findNodeById(nodeId, root_node));
    } else {
      oncontextmenu?.(event, null);
    }
  }

  function nodeKeyDownHandler(event: KeyboardEvent, node: TreeNode) {
    if (event.key === " ") {
      toggleExpanded(node);
    }
  }

  function findNodeById(id: string, node: TreeNode): TreeNode | null {
    if (node.id === id) {
      return node;
    }
    for (const child of node.children ?? []) {
      const found = findNodeById(id, child);
      if (found) return found;
    }
    return null;
  }

  function deselectAllNodes(node: TreeNode) {
    for (const child of node.children) {
      deselectAllNodes(child);
      node.selected = false;
    }
    node.selected = false;
  }

  function selectNode(node: TreeNode) {
    deselectAllNodes(root_node);
    node.selected = true;
  }

  function toggleExpanded(node: TreeNode) {
    node.expanded = !node.expanded;
  }

  export function addNode(node: TreeNode, parent_id: string | null = null) {
    if (parent_id) {
      const parent_node = findNodeById(parent_id, root_node);
      if (parent_node) {
        parent_node.children.push(node);
      }
    } else {
      root_node.children.push(node);
    }
  }
</script>

<div class="tree" role="tree" tabindex="-1" oncontextmenu={contextMenuHandler}>
  {#snippet treeNode(nodes: TreeNode[], level: number)}
    <div class="tree-node-container" transition:slide={{ duration: 150 }}>
      {#each nodes as node (node.id)}
        <div class="tree-node">
          <div
            class="tree-row"
            class:selected={node.selected}
            style="padding-left: {level * indentSize}px"
            data-node-id={node.id}
            onclick={() => selectNode(node)}
            ondblclick={() => toggleExpanded(node)}
            onkeydown={(e) => nodeKeyDownHandler(e, node)}
            role="treeitem"
            tabindex="0"
            aria-selected={node.selected}
            aria-expanded={node.children.length > 0 ? node.expanded : false}
          >
            <span
              class="tree-arrow"
              onclick={() => toggleExpanded(node)}
              onkeydown={(e) => e.key === "Enter" && toggleExpanded(node)}
              role="button"
              tabindex="-1"
            >
              {#if node.children.length > 0}
                <img class="arrow-icon" class:transform-arrow={node.expanded} src={arrowIcon} alt="arrow" />
              {/if}
            </span>
            {#if showIcons}
              <img
                src={node.icon ? node.icon : node.children.length > 0 ? folderIcon : fileIcon}
                alt=""
                class="node-icon"
              />
            {/if}
            <span class="node-label">{node.label}</span>
          </div>
          {#if node.children.length > 0 && node.expanded}
            {@render treeNode(node.children, level + 1)}
          {/if}
        </div>
      {/each}
    </div>
  {/snippet}
  {#if root_node.children.length > 0}
    {@render treeNode(root_node.children, 0)}
  {/if}
</div>

<style>
  .tree {
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  .tree-node-container {
    overflow: hidden;
  }

  .tree-node {
    display: flex;
    flex-direction: column;
  }

  .tree-row {
    display: flex;
    align-items: center;
    height: 22px;
    padding-right: 8px;
    cursor: pointer;
    white-space: nowrap;
    border-radius: 3px;
    margin: 1px 4px;
  }
  .tree-row:hover {
    background-color: #e8e8e8;
  }

  .tree-row.selected {
    background-color: #d0e4ff;
  }

  .tree-row.selected:hover {
    background-color: #c0d8f8;
  }

  .node-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    margin-right: 5px;
    object-fit: contain;
  }

  .tree-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-right: 5px;
  }

  .arrow-icon {
    width: 16px;
    height: 16px;
    transform: rotateZ(0deg);
    transition: transform 0.15s;
  }

  .transform-arrow {
    transform: rotateZ(90deg);
  }
</style>
