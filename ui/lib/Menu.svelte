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
  - `disabled?: boolean` - Whether the item is disabled and unclickable
  - `shortcut?: string` - Keyboard shortcut text to display
  - `checkable?: boolean` - Whether the item behaves as a checkbox
  - `checked?: boolean` - Whether the checkbox is checked
  - `action?: () => void` - Click handler
  - `children?: MenuItem[]` - Nested menu items
  - `separator?: boolean` - Render as separator line
-->
<script lang="ts" module>
  export interface MenuItem {
    label: string;
    icon?: string;
    disabled?: boolean;
    shortcut?: string;
    action?: (data: any) => void;
    children?: MenuItem[];
    checkable?: boolean;
    checked?: boolean;
    separator?: boolean;
  }
</script>

<script lang="ts">
  import arrowIcon from "../assets/icons/menu_arrow.svg";
  import { formatShortcut } from "../core/utils";
  import { onDestroy, onMount } from "svelte";

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
    if (item.disabled) return;
    if (hasChildren(item)) return;
    item.action?.(data);
    close();
  }

  function itemMouseEnterHandler(event: MouseEvent, index: number, level: number, item: MenuItem) {
    if (item.disabled) {
      selectedItems.splice(level, selectedItems.length);
      return;
    }
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    selectedItems.splice(level, selectedItems.length);
    selectedItems.push({ index, x: rect.x, y: rect.y - 7, w: rect.width });
  }

  function itemKeyDownHandler(event: KeyboardEvent, item: MenuItem) {
    if (item.disabled) return;
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
  {@const anyCheckable = menuItems.some((item) => item.checkable)}
  <div
    class="context-menu"
    style="left: {menuCoords[level]?.x}px; top: {menuCoords[level]?.y}px; z-index: {10000 + level};"
    use:adjustPosition={level}
    role="menu"
  >
    {#each menuItems as item, index (index)}
      {#if item.separator}
        <div class="menu-separator" role="separator"></div>
      {:else}
        <div
          class="menu-item"
          class:disabled={item.disabled}
          class:menu-item-hover={(selectedItems[level]?.index ?? -1) === index && !item.disabled}
          onclick={() => itemClickHandler(item)}
          onmouseenter={(e) => itemMouseEnterHandler(e, index, level, item)}
          onkeydown={(e) => itemKeyDownHandler(e, item)}
          role="menuitem"
          tabindex={item.disabled ? -1 : 0}
        >
          {#if anyCheckable}
            <div class="menu-item-checkbox-container">
              {#if item.checkable && item.checked}
                <svg class="checkmark-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 4L6 10L3 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              {/if}
            </div>
          {/if}
          <span class="menu-item-label">{item.label}</span>
          {#if item.shortcut}
            <span class="menu-item-shortcut">{formatShortcut(item.shortcut)}</span>
          {/if}
          {#if hasChildren(item)}
            <img src={arrowIcon} alt="" class="submenu-arrow" />
          {/if}
        </div>

        {#if (selectedItems[level]?.index ?? -1) === index && hasChildren(item) && !item.disabled}
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
    color: #1a1a1a;
    border-radius: 6px;
    height: 22px;
  }

  .menu-item:not(.disabled):hover,
  .menu-item-hover:not(.disabled) {
    background-color: #317ae7;
  }

  .menu-item:not(.disabled):hover .submenu-arrow,
  .menu-item-hover:not(.disabled) .submenu-arrow {
    filter: brightness(0) invert(1);
  }

  .menu-item:not(.disabled):hover .menu-item-label,
  .menu-item:not(.disabled):focus .menu-item-label,
  .menu-item-hover:not(.disabled) .menu-item-label {
    color: #ffffff;
  }

  .menu-item:not(.disabled):hover .menu-item-shortcut,
  .menu-item:not(.disabled):focus .menu-item-shortcut,
  .menu-item-hover:not(.disabled) .menu-item-shortcut {
    color: rgba(255, 255, 255, 0.7);
  }

  .menu-item:not(.disabled):focus {
    outline: none;
    background-color: #3b9dff;
    color: #ffffff;
  }

  .menu-item.disabled,
  .menu-item.disabled .menu-item-label {
    color: #8c8c8c;
    cursor: default;
  }

  .menu-item.disabled .submenu-arrow {
    opacity: 0.5;
  }

  .menu-item-label {
    flex: 1;
  }

  .menu-item-shortcut {
    color: #8c8c8c;
    margin-left: 16px;
  }

  .menu-item-checkbox-container {
    width: 16px;
    height: 16px;
    margin-right: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .checkmark-icon {
    width: 14px;
    height: 14px;
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
