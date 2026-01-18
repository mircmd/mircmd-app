<!--
  @component TextArea

  Read-only text area component for displaying text content.
  Provides a scrollable text display area with optional monospace font support.

  ## Features
  - Read-only text display
  - Vertical scrolling for overflow content
  - Optional monospace font for code/logs display
  - Two-way binding for value

  ## Props
  - `monospace: boolean` - Use monospace font (default: false)
  - `value: string` - Text content, supports two-way binding (default: "")

  ## Usage Example
  ```svelte
  <script>
    let logContent = $state("");

    function appendLog(text: string) {
      logContent += (logContent ? "\n" : "") + text;
    }

    function clearLog() {
      logContent = "";
    }
  </script>

  <TextArea bind:value={logContent} monospace />
  <button onclick={() => appendLog("New entry")}>Add</button>
  <button onclick={clearLog}>Clear</button>
  ```
-->
<script lang="ts">
  interface Props {
    monospace?: boolean;
    value?: string;
  }

  let { monospace = false, value = $bindable("") }: Props = $props();
</script>

<textarea class="text-area" class:monospace bind:value readonly></textarea>

<style>
  .text-area {
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 4px;
    margin: 0;
    border: none;
    outline: none;
    resize: none;
    overflow-x: hidden;
    overflow-y: auto;
    background-color: #ffffff;
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
    color: inherit;
  }

  .text-area.monospace {
    font-family: ui-monospace, "SF Mono", "Cascadia Code", "Segoe UI Mono",
      Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  }
</style>
