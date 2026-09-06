<!--
  @component CollapsibleSection

  Host accordion section for Control Panel blocks.
  Does not know about plugin controls.
-->
<script lang="ts">
  import type { Snippet } from "svelte";

  import arrowIcon from "../assets/icons/collapsible_section_arrow.svg";

  interface Props {
    id: string;
    title: string;
    expanded?: boolean;
    onExpandedChange?: (expanded: boolean) => void;
    children?: Snippet;
  }

  let { id, title, expanded = true, onExpandedChange, children }: Props = $props();

  function toggle(): void {
    onExpandedChange?.(!expanded);
  }
</script>

<section class="collapsible-section" data-block-id={id}>
  <button
    type="button"
    class="collapsible-header"
    aria-expanded={expanded}
    aria-controls={`section-body-${id}`}
    id={`section-header-${id}`}
    onclick={toggle}
  >
    <img class="arrow-icon" class:transform-arrow={expanded} src={arrowIcon} alt="arrow" />
    <span class="header-title">{title}</span>
  </button>

  <div
    id={`section-body-${id}`}
    class="collapsible-body"
    class:expanded
    role="region"
    aria-labelledby={`section-header-${id}`}
    inert={!expanded}
  >
    <div class="collapsible-body-clip">
      <div class="collapsible-body-inner">
        {#if children}
          {@render children()}
        {/if}
      </div>
    </div>
  </div>
</section>

<style>
  .collapsible-section {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .collapsible-header {
    display: flex;
    align-items: center;
    gap: 0px;
    margin: 0;
    max-height: 20px;
    min-height: 20px;
    padding-left: 2px;
    border: none;
    background: #D0D0D0;
    text-align: left;
    cursor: pointer;
    font-size: 12px;
    color: #222;
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

  .header-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .collapsible-body {
    display: grid;
    grid-template-rows: 0fr;
    transition: grid-template-rows 0.15s ease;
    overflow: hidden;
  }

  .collapsible-body.expanded {
    grid-template-rows: 1fr;
  }

  .collapsible-body-clip {
    overflow: hidden;
    min-height: 0;
    min-width: 0;
  }

  .collapsible-body-inner {
    padding: 8px;
    min-width: 0;
  }
</style>
