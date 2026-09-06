<!--
  @component TabWidget

  Tab widget component for switching between content panels.
  Provides a tab bar with selectable tabs and associated content area.

  ## TODO
  - Option to stretch the TabBar to the full width of the container
  - Optional icon for the tab. Place it to the left of the tab name.
-->

<script lang="ts" module>
  let id_counter = 0;

  function generateId() {
    return "tab-" + (id_counter++).toString();
  }

  export type TabBarPosition = "top" | "left" | "right";
  export type TabBarAlignment = "center" | "start" | "end";
  export type TabItem = {
    id?: string;
    label: string;
    snippet?: Snippet;
    component?: Component<any>;
    props?: Record<string, any>;
  };
</script>

<script lang="ts">
  import type { Component, Snippet } from "svelte";
  import closeIcon from "../assets/icons/tab_close.svg";

  interface Props {
    tabs?: TabItem[];
    tabBarPosition?: TabBarPosition;
    tabBarAlignment?: TabBarAlignment;
    activeIndex?: number;
    showSingleTab?: boolean;
    keepAlive?: boolean;
    closeable?: boolean;
  }

  let {
    tabs: initialTabs = [],
    tabBarPosition: initialTabBarPosition = "top",
    tabBarAlignment: initialTabBarAlignment = "center",
    activeIndex: initialIndex = 0,
    showSingleTab = false,
    keepAlive = false,
    closeable: initialCloseable = false,
  }: Props = $props();

  let tabs = $state([...initialTabs].map((tab) => ({ ...tab, id: generateId() })));
  let activeIndex = $state(initialIndex);
  let tabBarPosition = $state(initialTabBarPosition);
  let tabBarAlignment = $state(initialTabBarAlignment);
  let closeable = $state(initialCloseable);

  let showTabBar = $derived(tabs.length > 1 || showSingleTab);
  let activeTab = $derived(tabs[activeIndex]);
  let isVertical = $derived(tabBarPosition === "left" || tabBarPosition === "right");

  export function addTab(tab: TabItem, setActive: boolean = false) {
    tabs.push({ ...tab, id: generateId() });
    if (setActive) {
      activeIndex = tabs.length - 1;
    }
  }

  export function setActiveTab(index: number) {
    if (tabs.length === 0) return;
    if (index < 0 || index >= tabs.length) return;
    activeIndex = index;
  }

  export function setNextActiveTab() {
    if (tabs.length === 0) return;
    if (activeIndex === tabs.length - 1) {
      activeIndex = 0;
    } else {
      activeIndex = activeIndex + 1;
    }
  }

  export function setPreviousActiveTab() {
    if (tabs.length === 0) return;
    if (activeIndex === 0) {
      activeIndex = tabs.length - 1;
    } else {
      activeIndex = activeIndex - 1;
    }
  }

  export function removeTab(index: number) {
    if (tabs.length === 0) return;
    if (index < 0 || index >= tabs.length) {
      return;
    }
    tabs.splice(index, 1);
    if (activeIndex >= index) {
      activeIndex = Math.max(0, activeIndex - 1);
    }
  }

  export function setTabBarPosition(position: TabBarPosition) {
    tabBarPosition = position;
  }

  export function setCloseable(value: boolean) {
    closeable = value;
  }
</script>

<div
  class="tabs-widget"
  class:vertical={isVertical}
  class:position-top={tabBarPosition === "top"}
  class:position-left={tabBarPosition === "left"}
  class:position-right={tabBarPosition === "right"}
>
  {#if showTabBar}
    <div
      class="tabs-bar"
      class:alignment-start={tabBarAlignment === "start"}
      class:alignment-end={tabBarAlignment === "end"}
      class:alignment-center={tabBarAlignment === "center"}
      role="tablist"
    >
      {#each tabs as tab, index (tab.id)}
        <button class="tabs-button" class:active={activeIndex === index} onclick={() => setActiveTab(index)} role="tab">
          <span class="tabs-title">{tab.label}</span>
          {#if closeable}
            <button
              class="tabs-close-button"
              onclick={(e) => {
                e.stopPropagation();
                removeTab(index);
              }}
              aria-label="Close tab"
            >
              <img src={closeIcon} alt="Close" />
            </button>
          {/if}
        </button>
      {/each}
    </div>
  {/if}

  <div class="tabs-content" role="tabpanel">
    {#if activeTab}
      {#if keepAlive}
        {#each tabs as tab, index (tab.id)}
          <div style:display={index === activeIndex ? "block" : "none"}>
            {#if tab.component}
              {@const Cmp = tab.component}
              <Cmp {...tab.props} />
            {:else if tab.snippet}
              {@render tab.snippet()}
            {:else}
              <p>No component or snippet found for tab {index}</p>
            {/if}
          </div>
        {/each}
      {:else if activeTab.component}
        {@const ActiveComponent = activeTab.component}
        <ActiveComponent {...activeTab.props} />
      {:else if activeTab.snippet}
        {@render activeTab.snippet()}
      {:else}
        <p>No component or snippet found</p>
      {/if}
    {:else}
      <p>No tabs found</p>
    {/if}
  </div>
</div>

<style>
  /* Container */
  .tabs-widget {
    --tab-border-color: #dadada;
    --tab-bg: #ffffff;
    --tab-active-bg: #317ae7;
    --tab-active-color: #ffffff;
    --tab-content-bg: #e8e8e8;

    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
  }

  .tabs-widget.vertical {
    flex-direction: row;
  }

  .tabs-widget.vertical.position-right {
    flex-direction: row-reverse;
  }

  /* Tab bar */
  .tabs-bar {
    display: flex;
    flex-shrink: 0;
    border-bottom: 1px solid var(--tab-border-color);
  }

  .tabs-bar.alignment-start {
    justify-content: flex-start;
  }

  .tabs-bar.alignment-center {
    justify-content: center;
  }

  .tabs-bar.alignment-end {
    justify-content: flex-end;
  }

  .tabs-widget.vertical .tabs-bar {
    flex-direction: column;
    border-bottom: none;
    border-right: 1px solid var(--tab-border-color);
  }

  .tabs-widget.vertical.position-right .tabs-bar {
    border-right: none;
    border-left: 1px solid var(--tab-border-color);
  }

  /* Tab button */
  .tabs-button {
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    min-width: 70px;
    height: 22px;
    padding: 0 10px;
    border: none;
    border-left: 1px solid var(--tab-border-color);
    border-radius: 0;
    color: inherit;
    font: inherit;
    background: var(--tab-bg);
    transition:
      background-color 0.15s,
      color 0.15s;
  }

  .tabs-button:first-child,
  .tabs-button.active,
  .tabs-button.active + .tabs-button {
    border-left-color: transparent;
  }

  .tabs-button:hover:not(.active) {
    background: color-mix(in srgb, var(--tab-active-bg) 15%, var(--tab-bg));
  }

  .tabs-button.active {
    color: var(--tab-active-color);
    background: var(--tab-active-bg);
  }

  .tabs-widget.vertical .tabs-button {
    flex-direction: column;
    min-width: unset;
    width: 22px;
    min-height: 70px;
    height: auto;
    padding: 10px 0;
    border-left: none;
    border-top: 1px solid var(--tab-border-color);
  }

  .tabs-widget.vertical.position-left .tabs-button {
    flex-direction: column-reverse;
  }

  .tabs-widget.vertical .tabs-button:first-child,
  .tabs-widget.vertical .tabs-button.active,
  .tabs-widget.vertical .tabs-button.active + .tabs-button {
    border-left: none;
    border-top-color: transparent;
  }

  /* Tab title */
  .tabs-title {
    white-space: nowrap;
    color: inherit;
  }

  .tabs-widget.vertical .tabs-title {
    writing-mode: vertical-rl;
    text-orientation: mixed;
  }

  .tabs-widget.vertical.position-left .tabs-title {
    transform: rotate(180deg);
  }

  /* Close button */
  .tabs-close-button {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    padding: 0;
    border: none;
    border-radius: 2px;
    background: transparent;
    opacity: 0.6;
  }

  .tabs-close-button:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.1);
  }

  .tabs-button.active .tabs-close-button:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .tabs-close-button img {
    width: 16px;
    height: 16px;
  }

  .tabs-button.active .tabs-close-button img {
    filter: invert(1);
  }

  /* Content */
  .tabs-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    background-color: var(--tab-content-bg);
  }

  .tabs-content > :global(*) {
    flex: 1;
    min-width: 0;
    min-height: 0;
  }
</style>
