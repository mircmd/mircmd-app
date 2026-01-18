<!--
  @component Explorer

  Node explorer dock panel that displays project structure as a hierarchical tree.
  Based on the Tree component, it provides navigation and interaction with loaded nodes.

  ## Features
  - Displays project nodes in a tree structure with icons
  - Context menu on right-click with actions:
    - Import files into selected node (or root if none selected)
    - Export node data
    - Open node with available browser plugins
  - Automatic loading of icon plugins for node visualization
  - Dynamic plugin discovery for "Open with..." submenu

  ## Public API
  - `refresh()` - Reloads project nodes from the core
-->
<script lang="ts">
  import { onMount } from "svelte";

  import { getProjectRootNode, type ProjectNode } from "../app";
  import Menu from "../lib/menu.svelte";
  import type { MenuItem } from "../lib/menu.svelte";
  import Tree from "../lib/tree.svelte";
  import type { TreeNode } from "../lib/tree.svelte";
  import { getWindowManager } from "../lib/window_manager/window_manager_context";
  import { loadBrowserPlugin, loadIconPlugin } from "../utils/browser_plugins";
  import { icon_store } from "../utils/icon_store";
  import {
    getPlugins,
    PluginTarget,
    PluginType,
    type PluginInfo,
  } from "../utils/plugins";
  import { getNodeData, importFiles } from "../utils/project";

  let nodes: TreeNode[] = $state([]);
  let selectedId: string | null = $state(null);
  let programPlugins: PluginInfo[] = $state([]);

  let contextMenuVisible: boolean = $state(false);
  let contextMenuX: number = $state(0);
  let contextMenuY: number = $state(0);
  let contextMenuNode: TreeNode | null = $state(null);

  function convertToTreeNode(node: ProjectNode): TreeNode {
    return {
      id: node.id,
      label: node.name,
      icon: icon_store.get_icon(node.kind),
      expanded: false,
      children: node.children.map(convertToTreeNode),
    };
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

  async function loadPlugins(): Promise<void> {
    const allPlugins = await getPlugins();

    programPlugins = allPlugins.filter(
      (p) =>
        p.manifest.target === PluginTarget.Ui &&
        p.manifest.type === PluginType.Program
    );

    const iconPlugins = allPlugins.filter(
      (p) =>
        p.manifest.target === PluginTarget.Ui &&
        p.manifest.type === PluginType.Icons
    );

    for (const pluginInfo of iconPlugins) {
      try {
        const plugin = await loadIconPlugin(pluginInfo.path);
        icon_store.add_icons(plugin.icons());
      } catch (e) {
        console.error(`Failed to load icon plugin ${pluginInfo.path}:`, e);
      }
    }
    icon_store.set_loaded(true);
  }

  async function loadProjectNodes(): Promise<void> {
    const rootNode = await getProjectRootNode();
    nodes = rootNode.children.map(convertToTreeNode);
  }

  async function openWithPlugin(pluginInfo: PluginInfo): Promise<void> {
    if (!contextMenuNode) return;

    const { id, label, icon } = contextMenuNode;
    const data = await getNodeData(id);
    const plugin = await loadBrowserPlugin(pluginInfo.path);
    const html = plugin.render(data);

    getWindowManager().addWindow(label, pluginInfo.path, html, icon);
  }

  function buildOpenWithSubmenu(): MenuItem[] {
    return programPlugins.map((pluginInfo) => ({
      id: `open_with_${pluginInfo.manifest.metadata.id}`,
      label: pluginInfo.manifest.metadata.name,
      action: () => openWithPlugin(pluginInfo),
    }));
  }

  function handleSelect(event: CustomEvent<{ node: TreeNode }>): void {
    selectedId = event.detail.node.id;
  }

  function handleContextMenu(event: MouseEvent): void {
    event.preventDefault();

    const target = event.target as HTMLElement;
    const treeItem = target.closest(".tree-item");
    if (!treeItem) return;

    const nodeId = treeItem.getAttribute("data-node-id");
    if (!nodeId) return;

    contextMenuNode = findNodeById(nodeId, nodes);
    contextMenuX = event.clientX;
    contextMenuY = event.clientY;
    contextMenuVisible = true;
  }

  function handleMenuClose(): void {
    contextMenuVisible = false;
    contextMenuNode = null;
  }

  export function refresh(): void {
    loadProjectNodes();
  }

  onMount(() => {
    loadPlugins().then(loadProjectNodes);
  });

  let contextMenuItems: MenuItem[] = $derived([
    {
      id: "import_file",
      label: "Import files",
      action: () => importFiles(contextMenuNode?.id ?? null),
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
      children: buildOpenWithSubmenu(),
    },
  ]);
</script>

<div
  class="explorer-tree"
  oncontextmenu={handleContextMenu}
  role="tree"
  tabindex="-1"
>
  <Tree {nodes} {selectedId} on:select={handleSelect} />
</div>

<Menu
  items={contextMenuItems}
  x={contextMenuX}
  y={contextMenuY}
  bind:visible={contextMenuVisible}
  onclose={handleMenuClose}
/>

<style>
  .explorer-tree {
    width: 100%;
    height: 100%;
    background-color: #ffffff;
    overflow: hidden;
  }
</style>
