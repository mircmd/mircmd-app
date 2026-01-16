<script lang="ts">
  import { onMount } from "svelte";
  import Tree from "../lib/components/tree.svelte";
  import type { TreeNode } from "../lib/components/tree.svelte";
  import { getProjectRootNode, type ProjectNode } from "../app";

  // Import icons
  import iconMolecule from "../assets/icons/molecule.png";
  import iconAtomicCoordinates from "../assets/icons/atomic_coordinates.png";
  import iconAtomicCoordinatesGroup from "../assets/icons/atomic_coordinates_group.png";
  import iconUnex from "../assets/icons/unex.png";
  import iconUnknown from "../assets/icons/unknown.svg";
  import iconVolumeCube from "../assets/icons/volume_cube.png";

  let nodes: TreeNode[] = [];
  let selectedId: string | null = null;

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
</script>

<div class="explorer-tree">
  <Tree
    {nodes}
    {selectedId}
    on:select={handleSelect}
    on:toggle={handleToggle}
  />
</div>

<style>
  .explorer-tree {
    width: 100%;
    height: 100%;
    background-color: #ffffff;
    overflow: hidden;
  }
</style>
