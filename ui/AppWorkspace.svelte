<!--
  @component AppWorkspace

  Host adapter over lib Workspace: binds WorkspacePreferences dock sizes
  and owns Layout instances for left/right/bottom docks.
-->
<script lang="ts">
  import type { Snippet } from "svelte";

  import Workspace from "./lib/Workspace.svelte";
  import type { DockArea } from "./lib/Workspace.svelte";
  import Layout from "./lib/Layout.svelte";
  import type { LayoutItemHandle, LayoutWidgetInput } from "./lib/Layout.svelte";
  import type { WorkspacePreferences } from "./core/workspace_state.svelte";

  interface Props {
    centralContent: Snippet;
    workspacePreferences: WorkspacePreferences;
  }

  let { centralContent, workspacePreferences }: Props = $props();

  let leftLayout: ReturnType<typeof Layout> = $state()!;
  let rightLayout: ReturnType<typeof Layout> = $state()!;
  let bottomLayout: ReturnType<typeof Layout> = $state()!;
  let leftEmpty = $state(true);
  let rightEmpty = $state(true);
  let bottomEmpty = $state(true);

  export function addWidgetToDock(area: DockArea, content: LayoutWidgetInput): LayoutItemHandle {
    if (area === "left") return leftLayout.addWidget(content);
    if (area === "right") return rightLayout.addWidget(content);
    return bottomLayout.addWidget(content);
  }
</script>

<Workspace
  {centralContent}
  dockSizes={workspacePreferences.dockSizes}
  onDockSizeChange={(area, size) => workspacePreferences.setDockSize(area, size)}
  {leftEmpty}
  {rightEmpty}
  {bottomEmpty}
>
  {#snippet left()}
    <Layout bind:this={leftLayout} bind:isEmpty={leftEmpty} orientation="vertical" />
  {/snippet}
  {#snippet right()}
    <Layout bind:this={rightLayout} bind:isEmpty={rightEmpty} orientation="vertical" />
  {/snippet}
  {#snippet bottom()}
    <Layout bind:this={bottomLayout} bind:isEmpty={bottomEmpty} orientation="horizontal" />
  {/snippet}
</Workspace>
