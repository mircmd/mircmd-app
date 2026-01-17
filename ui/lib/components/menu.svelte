<script lang="ts" context="module">
  export interface MenuItem {
    id: string;
    label: string;
    action?: () => void;
    children?: MenuItem[];
    separator?: boolean;
  }
</script>

<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from "svelte";
  import arrowRightIcon from "../../assets/icons/arrow_right.svg";

  export let items: MenuItem[] = [];
  export let x: number = 0;
  export let y: number = 0;
  export let visible: boolean = false;
  export let isSubmenu: boolean = false;

  const dispatch = createEventDispatcher<{
    close: void;
  }>();

  let menuElement: HTMLElement;
  let activeSubmenuId: string | null = null;
  let submenuX: number = 0;
  let submenuY: number = 0;

  function handleItemClick(item: MenuItem): void {
    if (item.separator) return;
    if (item.children && item.children.length > 0) return;

    if (item.action) {
      item.action();
    }
    closeMenu();
  }

  function handleItemMouseEnter(event: MouseEvent, item: MenuItem): void {
    if (item.separator) {
      activeSubmenuId = null;
      return;
    }

    if (item.children && item.children.length > 0) {
      const target = event.currentTarget as HTMLElement;
      const rect = target.getBoundingClientRect();
      submenuX = rect.right;
      submenuY = rect.top;
      activeSubmenuId = item.id;
    } else {
      activeSubmenuId = null;
    }
  }

  function closeMenu(): void {
    visible = false;
    activeSubmenuId = null;
    dispatch("close");
  }

  function handleClickOutside(event: MouseEvent): void {
    if (!visible || isSubmenu) return;

    const target = event.target as Node;
    const allMenus = document.querySelectorAll(".context-menu");
    let clickedInsideMenu = false;

    allMenus.forEach((menu) => {
      if (menu.contains(target)) {
        clickedInsideMenu = true;
      }
    });

    if (!clickedInsideMenu) {
      closeMenu();
    }
  }

  function handleKeyDown(event: KeyboardEvent): void {
    if (event.key === "Escape") {
      closeMenu();
    }
  }

  onMount(() => {
    if (!isSubmenu) {
      document.addEventListener("click", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
  });

  onDestroy(() => {
    if (!isSubmenu) {
      document.removeEventListener("click", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    }
  });

  function adjustPosition(node: HTMLElement): { destroy: () => void } {
    const rect = node.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (rect.right > viewportWidth) {
      if (isSubmenu) {
        x =
          x -
          rect.width -
          (menuElement?.parentElement?.getBoundingClientRect().width || 0);
      } else {
        x = viewportWidth - rect.width - 8;
      }
    }

    if (rect.bottom > viewportHeight) {
      y = viewportHeight - rect.height - 8;
    }

    return { destroy: () => {} };
  }
</script>

{#if visible}
  <div
    class="context-menu"
    class:submenu={isSubmenu}
    style="left: {x}px; top: {y}px;"
    bind:this={menuElement}
    use:adjustPosition
    role="menu"
  >
    {#each items as item (item.id)}
      {#if item.separator}
        <div class="menu-separator"></div>
      {:else}
        <div
          class="menu-item"
          class:has-submenu={item.children && item.children.length > 0}
          on:click={() => handleItemClick(item)}
          on:mouseenter={(e) => handleItemMouseEnter(e, item)}
          on:keydown={(e) => e.key === "Enter" && handleItemClick(item)}
          role="menuitem"
          tabindex="0"
        >
          <span class="menu-item-label">{item.label}</span>
          {#if item.children && item.children.length > 0}
            <img src={arrowRightIcon} alt="" class="submenu-arrow" />
          {/if}
        </div>

        {#if item.children && item.children.length > 0 && activeSubmenuId === item.id}
          <svelte:self
            items={item.children}
            x={submenuX}
            y={submenuY}
            visible={true}
            isSubmenu={true}
            on:close={closeMenu}
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
