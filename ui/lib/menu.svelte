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
  - `visible: boolean` - Controls menu visibility
  - `is_submenu: boolean` - Internal flag for nested menus
  - `onclose: () => void` - Callback when menu closes

  ## MenuItem Interface
  - `id: string` - Unique identifier
  - `label: string` - Display text
  - `action?: () => void` - Click handler
  - `children?: MenuItem[]` - Nested menu items
  - `separator?: boolean` - Render as separator line
-->
<script lang="ts" module>
  export interface MenuItem {
    id: string;
    label: string;
    action?: () => void;
    children?: MenuItem[];
    separator?: boolean;
  }
</script>

<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import arrowRightIcon from "../assets/icons/arrow_right.svg";
  import Menu from "./menu.svelte";

  interface Props {
    items: MenuItem[];
    x: number;
    y: number;
    visible: boolean;
    is_submenu?: boolean;
    onclose?: () => void;
  }

  let {
    items = [],
    x = $bindable(0),
    y = $bindable(0),
    visible = $bindable(false),
    is_submenu = false,
    onclose,
  }: Props = $props();

  let menu_element: HTMLElement | undefined = $state();
  let active_submenu_id: string | null = $state(null);
  let submenu_x = $state(0);
  let submenu_y = $state(0);

  function has_children(item: MenuItem): boolean {
    return Boolean(item.children && item.children.length > 0);
  }

  function close_menu(): void {
    visible = false;
    active_submenu_id = null;
    onclose?.();
  }

  function handle_item_click(item: MenuItem): void {
    if (item.separator || has_children(item)) {
      return;
    }
    item.action?.();
    close_menu();
  }

  function handle_item_mouse_enter(event: MouseEvent, item: MenuItem): void {
    if (item.separator) {
      active_submenu_id = null;
      return;
    }

    if (has_children(item)) {
      const target = event.currentTarget as HTMLElement;
      const rect = target.getBoundingClientRect();
      submenu_x = rect.right;
      submenu_y = rect.top;
      active_submenu_id = item.id;
    } else {
      active_submenu_id = null;
    }
  }

  function handle_click_outside(event: MouseEvent): void {
    if (!visible || is_submenu) {
      return;
    }

    const target = event.target as Node;
    const all_menus = document.querySelectorAll(".context-menu");
    const clicked_inside = Array.from(all_menus).some((menu) =>
      menu.contains(target)
    );

    if (!clicked_inside) {
      close_menu();
    }
  }

  function handle_key_down(event: KeyboardEvent): void {
    if (event.key === "Escape") {
      close_menu();
    }
  }

  function adjust_position(node: HTMLElement): { destroy: () => void } {
    const rect = node.getBoundingClientRect();
    const viewport_width = window.innerWidth;
    const viewport_height = window.innerHeight;
    const margin = 8;

    if (rect.right > viewport_width) {
      if (is_submenu) {
        const parent_width =
          menu_element?.parentElement?.getBoundingClientRect().width || 0;
        x = x - rect.width - parent_width;
      } else {
        x = viewport_width - rect.width - margin;
      }
    }

    if (rect.bottom > viewport_height) {
      y = viewport_height - rect.height - margin;
    }

    return { destroy: () => {} };
  }

  onMount(() => {
    if (!is_submenu) {
      document.addEventListener("click", handle_click_outside);
      document.addEventListener("keydown", handle_key_down);
    }
  });

  onDestroy(() => {
    if (!is_submenu) {
      document.removeEventListener("click", handle_click_outside);
      document.removeEventListener("keydown", handle_key_down);
    }
  });
</script>

{#if visible}
  <div
    class="context-menu"
    class:submenu={is_submenu}
    style="left: {x}px; top: {y}px;"
    bind:this={menu_element}
    use:adjust_position
    role="menu"
  >
    {#each items as item (item.id)}
      {#if item.separator}
        <div class="menu-separator" role="separator"></div>
      {:else}
        <div
          class="menu-item"
          class:has-submenu={has_children(item)}
          onclick={() => handle_item_click(item)}
          onmouseenter={(e) => handle_item_mouse_enter(e, item)}
          onkeydown={(e) => e.key === "Enter" && handle_item_click(item)}
          role="menuitem"
          tabindex="0"
        >
          <span class="menu-item-label">{item.label}</span>
          {#if has_children(item)}
            <img src={arrowRightIcon} alt="" class="submenu-arrow" />
          {/if}
        </div>

        {#if has_children(item) && active_submenu_id === item.id}
          <Menu
            items={item.children ?? []}
            x={submenu_x}
            y={submenu_y}
            visible={true}
            is_submenu={true}
            onclose={close_menu}
          />
        {/if}
      {/if}
    {/each}
  </div>
{/if}

<style>
  .context-menu {
    position: fixed;
    min-width: 160px;
    background-color: #ececec;
    border: 1px solid #b0b0b0;
    border-radius: 8px;
    padding: 6px;
    box-shadow: 0 0 12px rgba(0, 0, 0, 0.35);
    z-index: 10000;
    user-select: none;
  }

  .context-menu.submenu {
    z-index: 10001;
  }

  .menu-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    cursor: pointer;
    color: #1a1a1a;
    border-radius: 6px;
    font-size: 13px;
  }

  .menu-item:hover {
    background-color: #317ae7;
    color: #ffffff;
  }

  .menu-item:hover .submenu-arrow {
    filter: brightness(0) invert(1);
  }

  .menu-item:hover .menu-item-label {
    color: #ffffff;
  }

  .menu-item:focus {
    outline: none;
    background-color: #3b9dff;
    color: #ffffff;
  }

  .menu-item:focus .menu-item-label {
    color: #ffffff;
  }

  .menu-item-label {
    flex: 1;
  }

  .submenu-arrow {
    width: 10px;
    height: 10px;
    margin-left: 8px;
  }

  .menu-separator {
    height: 1px;
    background-color: #c0c0c0;
    margin: 4px 8px;
  }
</style>
