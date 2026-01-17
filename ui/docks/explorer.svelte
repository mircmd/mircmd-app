<script lang="ts">
  import { onMount } from "svelte";
  import Tree from "../lib/components/tree.svelte";
  import type { TreeNode } from "../lib/components/tree.svelte";
  import Menu from "../lib/components/menu.svelte";
  import type { MenuItem } from "../lib/components/menu.svelte";
  import { getProjectRootNode, type ProjectNode } from "../app";
  import { importFiles } from "../utils/project";
  // Import icons
  import iconMolecule from "../assets/icons/molecule.png";
  import iconAtomicCoordinates from "../assets/icons/atomic_coordinates.png";
  import iconAtomicCoordinatesGroup from "../assets/icons/atomic_coordinates_group.png";
  import iconUnex from "../assets/icons/unex.png";
  import iconUnknown from "../assets/icons/unknown.svg";
  import iconVolumeCube from "../assets/icons/volume_cube.png";

  let nodes: TreeNode[] = [];
  let selectedId: string | null = null;

  // Context menu state
  let contextMenuVisible: boolean = false;
  let contextMenuX: number = 0;
  let contextMenuY: number = 0;
  let contextMenuNode: TreeNode | null = null;

  // Map backend node kind to icon
  const kindToIcon: Record<string, string> = {
    "mircmd:chemistry:molecule": iconMolecule,
    "mircmd:chemistry:atomic_coordinates": iconAtomicCoordinates,
    "mircmd:chemistry:atomic_coordinates_group": iconAtomicCoordinatesGroup,
    "mircmd:chemistry:unex": iconUnex,
    "mircmd:chemistry:volume_cube": iconVolumeCube,
  };

  function getIconForKind(kind: string): string {
    return kindToIcon[kind] ?? iconUnknown;
  }

  function convertProjectNodeToTreeNode(node: ProjectNode): TreeNode {
    return {
      id: node.id,
      label: node.name,
      icon: getIconForKind(node.kind),
      expanded: false,
      children: node.children.map(convertProjectNodeToTreeNode),
    };
  }

  async function loadProjectNodes(): Promise<void> {
    const rootNode = await getProjectRootNode();
    nodes = rootNode.children.map(convertProjectNodeToTreeNode);
  }

  export function refresh(): void {
    loadProjectNodes();
  }

  onMount(() => {
    loadProjectNodes();
  });

  function handleSelect(event: CustomEvent<{ node: TreeNode }>) {
    selectedId = event.detail.node.id;
  }

  function handleToggle(
    event: CustomEvent<{ node: TreeNode; expanded: boolean }>
  ) {
    // Can be extended to handle toggle events
  }

  function handleContextMenu(event: MouseEvent): void {
    event.preventDefault();

    const target = event.target as HTMLElement;
    const treeItem = target.closest(".tree-item");
    if (!treeItem) return;

    const nodeId = findNodeIdFromElement(treeItem, nodes);
    if (!nodeId) return;

    contextMenuNode = findNodeById(nodeId, nodes);
    contextMenuX = event.clientX;
    contextMenuY = event.clientY;
    contextMenuVisible = true;
  }

  function findNodeIdFromElement(
    element: Element,
    nodeList: TreeNode[]
  ): string | null {
    const label = element.querySelector(".tree-label")?.textContent;
    if (!label) return null;

    function search(nodes: TreeNode[]): string | null {
      for (const node of nodes) {
        if (node.label === label) return node.id;
        if (node.children) {
          const found = search(node.children);
          if (found) return found;
        }
      }
      return null;
    }
    return search(nodeList);
  }

  function findNodeById(id: string, nodeList: TreeNode[]): TreeNode | null {
    for (const node of nodeList) {
      if (node.id === id) return node;
      if (node.children) {
        const found = findNodeById(id, node.children);
        if (found) return found;
      }
    }
    return null;
  }

  function handleMenuClose(): void {
    contextMenuVisible = false;
    contextMenuNode = null;
  }

  // Context menu items
  const contextMenuItems: MenuItem[] = [
    {
      id: "import_file",
      label: "Import files",
      action: () => {
        importFiles(contextMenuNode?.id ?? null);
      },
    },
    {
      id: "export",
      label: "Export",
      action: () => {
        // TODO: implement export action
      },
    },
    { id: "sep1", label: "", separator: true },
    {
      id: "open_with",
      label: "Open with...",
      children: [
        {
          id: "open_with_editor",
          label: "Editor",
          action: () => {
            // TODO: implement open with editor action
          },
        },
        {
          id: "open_with_viewer",
          label: "Viewer",
          action: () => {
            // TODO: implement open with viewer action
          },
        },
      ],
    },
  ];
</script>

<!-- svelte-ignore a11y_interactive_supports_focus -->
<div class="explorer-tree" on:contextmenu={handleContextMenu} role="tree">
  <Tree
    {nodes}
    {selectedId}
    on:select={handleSelect}
    on:toggle={handleToggle}
  />
</div>

<Menu
  items={contextMenuItems}
  x={contextMenuX}
  y={contextMenuY}
  bind:visible={contextMenuVisible}
  on:close={handleMenuClose}
/>

<style>
  .explorer-tree {
    width: 100%;
    height: 100%;
    background-color: #ffffff;
    overflow: hidden;
  }
</style>
