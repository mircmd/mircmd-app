<!--
  @component Panel

  Panel widget with a title bar and content area.

  ## Layout Structure
  ```
  ┌─────────────────────────────────┐
  │           TITLE BAR             │
  ├─────────────────────────────────┤
  │                                 │
  │            CONTENT              │
  │                                 │
  └─────────────────────────────────┘
  ```
-->
<script lang="ts">
  import type { Component, Snippet } from "svelte";

  interface Props {
    title: string;
    showTitle?: boolean;
    /** Additional panel-specific title actions. */
    titleActions?: Snippet;
    content?: Snippet;
    component?: Component<any>;
    props?: Record<string, any>;
  }

  let {
    title,
    showTitle = $bindable(true),
    titleActions,
    content,
    component,
    props,
  }: Props = $props();

  export function setShowTitle(value: boolean) {
    showTitle = value;
  }
</script>

<div class="panel-widget">
  {#if showTitle}
    <div class="panel-title background" role="button" tabindex="0">
      <span class="title-text">{title}</span>
      {#if titleActions}
        <span class="title-actions">
          {@render titleActions()}
        </span>
      {/if}
    </div>
  {/if}

  <div class="panel-content background">
    {#if component}
      {@const Cmp = component}
      <Cmp {...props} />
    {:else if content}
      {@render content()}
    {:else}
      <p>No component or content found</p>
    {/if}
  </div>
</div>

<style>
  .panel-widget {
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
    position: relative;
    box-sizing: border-box;
  }

  .panel-title {
    display: flex;
    align-items: center;
    padding: 5px 10px;
    border-bottom: 1px solid #dadada;
    height: 22px;
    box-sizing: border-box;
    overflow: hidden;
    min-width: 0;
  }

  .title-text {
    font-size: 11px;
    color: #000000df;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
    flex: 1;
  }

  .title-actions {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    margin-left: 8px;
  }

  .panel-content {
    flex: 1;
    overflow: auto;
    min-height: 0;
    min-width: 0;
    display: flex;
  }

  .panel-content > :global(*) {
    flex: 1;
    width: 100%;
    height: 100%;
  }
</style>
