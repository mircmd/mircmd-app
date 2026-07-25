<!--
  @component Explorer

  Node explorer that displays project structure as a hierarchical tree.
  Based on the Tree component, it provides navigation and interaction with loaded nodes.

  ## Features
  - Displays project nodes in a tree structure with icons
-->
<script lang="ts" module>
  import fileIcon from "./assets/icons/tree_file.svg";
  import { pluginManager } from "./core/plugins";

  const CONTEXT_MENU_COMMON_ITEMS: MenuItem[] = [
    {
      label: "Import Files",
      action: (_: any) => {
        importFiles(null);
      },
    },
  ];

  function convertToTreeNode(node: ProjectNode): TreeNode {
    return {
      id: node.id,
      label: node.name,
      type: node.type,
      icon: pluginManager.icons.get(node.type) || fileIcon,
      expanded: false,
      selected: false,
      children: node.children.map(convertToTreeNode),
    };
  }
</script>

<script lang="ts">
  import { onMount } from "svelte";
  import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

  import { getProjectRootNode, importFiles, log } from "./core/commands";
  import type { ProjectNode } from "./core/types";
  import Tree, { type TreeNode } from "./lib/Tree.svelte";
  import type { MenuItem } from "./lib/Menu.svelte";
  import Panel from "./lib/Panel.svelte";
  import { getContextMenu } from "./core/context_menu.svelte";
  import type { ProgramManager } from "./core/program_manager.svelte";

  interface Props {
    programManager: ProgramManager;
  }

  const contextMenu = getContextMenu();

  let { programManager }: Props = $props();

  let treeRef: ReturnType<typeof Tree> = $state()!;

  async function loadRootNode() {
    const rootNode = await getProjectRootNode();
    treeRef.setRootNode(convertToTreeNode(rootNode));
  }

  function contextMenuHandler(event: MouseEvent, node: TreeNode | null) {
    contextMenu.open({
      event,
      items: node ? buildNodeContextMenu(node) : CONTEXT_MENU_COMMON_ITEMS,
      data: node ?? treeRef.getRootNode(),
    });
  }

  function buildProgramsContextMenu(node: TreeNode): MenuItem[] {
    const programs = pluginManager.programs.get(node.type);
    if (!programs) return [];

    const menuItems: MenuItem[] = [];
    for (const descriptor of programs) {
      menuItems.push({
        label: descriptor.metadata.name,
        action: (target: TreeNode) => {
          void programManager
            .openProgram({
              nodeId: target.id,
              nodeName: target.label,
              nodeType: target.type,
              icon: target.icon,
              descriptor,
            })
            .catch((error) => {
              log.error(`Failed to open program ${descriptor.key}: ${error}`);
            });
        },
      });
    }
    return menuItems;
  }

  function buildNodeContextMenu(node: TreeNode): MenuItem[] {
    const menuItems: MenuItem[] = [];
    menuItems.push({
      label: "Import Files",
      action: (target: TreeNode) => {
        importFiles(target.id);
      },
    });

    const openWithItems = buildProgramsContextMenu(node);
    if (openWithItems.length > 0) {
      menuItems.push({ label: "", separator: true });
      menuItems.push({
        label: "Open With...",
        children: openWithItems,
      });
    }
    return menuItems;
  }

  const appWebview = getCurrentWebviewWindow();
  appWebview.listen<{ parent_node_id: string | null; node: ProjectNode }>("explorer_add_node", (event) => {
    treeRef.addNode(convertToTreeNode(event.payload.node), event.payload.parent_node_id);
  });

  onMount(async () => {
    await loadRootNode();
  });
</script>

<Panel title="Explorer">
  {#snippet content()}
    <Tree bind:this={treeRef} oncontextmenu={contextMenuHandler} />
  {/snippet}
</Panel>
