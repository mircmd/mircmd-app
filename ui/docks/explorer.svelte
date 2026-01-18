<script lang="ts">
  import { onMount } from "svelte";
  import Menu from "../lib/components/menu.svelte";
  import type { MenuItem } from "../lib/components/menu.svelte";
  import Tree from "../lib/components/tree.svelte";
  import type { TreeNode } from "../lib/components/tree.svelte";
  import { getProjectRootNode, type ProjectNode } from "../app";
  import { loadBrowserPlugin, loadIconPlugin } from "../utils/browser_plugins";
  import { icon_store } from "../utils/icon_store";
  import {
    getPlugins,
    PluginTarget,
    PluginType,
    type PluginInfo,
  } from "../utils/plugins";
  import { getNodeData, importFiles } from "../utils/project";
  import { window_store } from "../utils/window_store";

  let nodes: TreeNode[] = $state([]);
  let selectedId: string | null = $state(null);

  // Context menu state
  let contextMenuVisible: boolean = $state(false);
  let contextMenuX: number = $state(0);
  let contextMenuY: number = $state(0);
  let contextMenuNode: TreeNode | null = $state(null);

  // Available program plugins
  let programPlugins: PluginInfo[] = $state([]);

  function getIconForKind(kind: string): string {
    return icon_store.get_icon(kind);
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

  async function loadProgramPlugins(): Promise<void> {
    const allPlugins = await getPlugins();
    programPlugins = allPlugins.filter(
      (p) =>
        p.manifest.target === PluginTarget.Ui &&
        p.manifest.type === PluginType.Program
    );
  }

  async function loadIconPlugins(): Promise<void> {
    const allPlugins = await getPlugins();
    const iconPlugins = allPlugins.filter(
      (p) =>
        p.manifest.target === PluginTarget.Ui &&
        p.manifest.type === PluginType.Icons
    );

    for (const pluginInfo of iconPlugins) {
      try {
        const plugin = await loadIconPlugin(pluginInfo.path);
        const icons = plugin.icons();
        icon_store.add_icons(icons);
      } catch (e) {
        console.error(`Failed to load icon plugin ${pluginInfo.path}:`, e);
      }
    }
    icon_store.set_loaded(true);
  }

  export function refresh(): void {
    loadProjectNodes();
  }

  onMount(() => {
    loadIconPlugins().then(() => {
      loadProjectNodes();
    });
    loadProgramPlugins();
  });

  async function openWithPlugin(pluginInfo: PluginInfo): Promise<void> {
    if (!contextMenuNode) return;

    const node_id = contextMenuNode.id;
    const node_label = contextMenuNode.label;
    const node_icon = contextMenuNode.icon;
    const data = await getNodeData(node_id);
    const plugin = await loadBrowserPlugin(pluginInfo.path);
    const html = plugin.render(data);

    window_store.add_window(node_label, pluginInfo.path, html, node_icon);
  }

  function buildOpenWithSubmenu(): MenuItem[] {
    return programPlugins.map((pluginInfo) => ({
      id: `open_with_${pluginInfo.manifest.metadata.id}`,
      label: pluginInfo.manifest.metadata.name,
      action: () => openWithPlugin(pluginInfo),
    }));
  }

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

  // Context menu items (reactive to update open_with submenu)
  let contextMenuItems: MenuItem[] = $derived([
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
      children: buildOpenWithSubmenu(),
    },
  ]);
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
