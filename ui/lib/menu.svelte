<!--
  @component Menu

  Context menu component with support for nested submenus.

  ## Features
  - Nested submenus with automatic positioning
  - Separator items for visual grouping
  - Action handlers for menu items
  - Keyboard navigation (Escape to close)
  - Click outside to close
  - Automatic viewport boundary adjustment

  ## Props
  - `items: MenuItem[]` - Array of menu items to display
  - `x: number` - Horizontal position in pixels
  - `y: number` - Vertical position in pixels
  - `close: () => void` - Callback when menu closes

  ## MenuItem Interface
  - `id: string` - Unique identifier
  - `label: string` - Display text
  - `icon?: string` - Icon URL
  - `action?: () => void` - Click handler
  - `children?: MenuItem[]` - Nested menu items
  - `separator?: boolean` - Render as separator line
-->
<script lang="ts" module>
  export interface MenuItem {
    label: string;
    icon?: string;
    action?: (data: any) => void;
    children?: MenuItem[];
    separator?: boolean;
  }
</script>

<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import arrowIcon from "../assets/icons/menu_arrow.svg";

  interface Props {
    items: MenuItem[];
    posX: number;
    posY: number;
    close: () => void;
    data?: any;
  }

  let { items = [], posX = 0, posY = 0, close, data = null }: Props = $props();

  let menuCoords = $state<{ x: number; y: number }[]>([]);
  let selectedItems = $state<{ index: number; x: number; y: number; w: number }[]>([]);

  function hasChildren(item: MenuItem): boolean {
    return Boolean(item.children && item.children.length > 0);
  }

  function itemClickHandler(item: MenuItem) {
    if (hasChildren(item)) return;
    item.action?.(data);
    close();
  }

  function itemMouseEnterHandler(event: MouseEvent, index: number, level: number) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    selectedItems.splice(level, selectedItems.length);
    selectedItems.push({ index, x: rect.x, y: rect.y - 7, w: rect.width });
  }

  function itemKeyDownHandler(event: KeyboardEvent, item: MenuItem) {
    if (event.key === "Enter") {
      itemClickHandler(item);
    }
  }

  function clickOutsideHandler(event: MouseEvent): void {
    const target = event.target as Node;
    const all_menus = document.querySelectorAll(".context-menu");
    const clicked_inside = Array.from(all_menus).some((menu) => menu.contains(target));

    if (!clicked_inside) {
      close();
    }
  }

  function keyDownHandler(event: KeyboardEvent): void {
    if (event.key === "Escape") {
      close();
    }
  }

  function adjustPosition(node: HTMLElement, level: number): { destroy: () => void } {
    const rect = node.getBoundingClientRect();
    const viewport_width = window.innerWidth;
    const viewport_height = window.innerHeight;

    let coords =
      level > 0
        ? { x: selectedItems[level - 1]!.x + selectedItems[level - 1]!.w, y: selectedItems[level - 1]!.y }
        : { x: posX, y: posY };

    if (coords.x + rect.width > viewport_width) {
      coords.x = level > 0 ? coords.x - (rect.width + selectedItems[level - 1]!.w) : coords.x - rect.width;
    }

    coords.y = coords.y - Math.max(0, coords.y + rect.height - viewport_height);

    menuCoords.push(coords);

    return {
      destroy: () => {
        menuCoords.splice(level, menuCoords.length);
      },
    };
  }

  onMount(() => {
    document.addEventListener("click", clickOutsideHandler);
    document.addEventListener("keydown", keyDownHandler);
  });

  onDestroy(() => {
    document.removeEventListener("click", clickOutsideHandler);
    document.removeEventListener("keydown", keyDownHandler);
  });
</script>

{#snippet menu(menuItems: MenuItem[], level: number)}
  <div
    class="context-menu"
    style="left: {menuCoords[level]?.x}px; top: {menuCoords[level]?.y}px; z-index: {10000 + level};"
    use:adjustPosition={level}
    role="menu"
  >
    {#each menuItems as item, index}
      {#if item.separator}
        <div class="menu-separator" role="separator"></div>
      {:else}
        <div
          class="menu-item"
          class:menu-item-hover={(selectedItems[level]?.index ?? -1) === index}
          onclick={() => itemClickHandler(item)}
          onmouseenter={(e) => itemMouseEnterHandler(e, index, level)}
          onkeydown={(e) => itemKeyDownHandler(e, item)}
          role="menuitem"
          tabindex="0"
        >
          <span class="menu-item-label">{item.label}</span>
          {#if hasChildren(item)}
            <img src={arrowIcon} alt="" class="submenu-arrow" />
          {/if}
        </div>

        {#if (selectedItems[level]?.index ?? -1) === index && hasChildren(item)}
          {@render menu(item.children ?? [], level + 1)}
        {/if}
      {/if}
    {/each}
  </div>
{/snippet}

{@render menu(items, 0)}

<style>
  .context-menu {
    width: auto;
    height: auto;
    position: fixed;
    min-width: 160px;
    background-color: #ececec;
    border: 1px solid #b0b0b0;
    border-radius: 8px;
    padding: 6px;
    box-shadow: 0 0 12px rgba(0, 0, 0, 0.35);
  }

  .menu-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 8px;
    cursor: pointer;
    color: #1a1a1a;
    border-radius: 6px;
    height: 22px;
  }

  .menu-item:hover,
  .menu-item-hover {
    background-color: #317ae7;
  }

  .menu-item:hover .submenu-arrow,
  .menu-item-hover .submenu-arrow {
    filter: brightness(0) invert(1);
  }

  .menu-item:hover .menu-item-label,
  .menu-item:focus .menu-item-label,
  .menu-item-hover .menu-item-label {
    color: #ffffff;
  }

  .menu-item:focus {
    outline: none;
    background-color: #3b9dff;
    color: #ffffff;
  }

  .menu-item-label {
    flex: 1;
  }

  .submenu-arrow {
    width: 20px;
    height: 20px;
    margin-right: -6px;
  }

  .menu-separator {
    height: 1px;
    background-color: #c0c0c0;
    margin: 4px 8px;
  }
</style>
