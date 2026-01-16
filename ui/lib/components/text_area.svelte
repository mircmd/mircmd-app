<!--
  @component TextArea

  Read-only text area component for displaying text content.
  Provides a scrollable text display area with optional monospace font support.

  ## Features
  - Read-only text display
  - Vertical scrolling for overflow content
  - Optional monospace font for code/logs display
  - Programmatic API for text manipulation

  ## Props
  - `monospace: boolean` - Use monospace font (default: false)
  - `value: string` - Text content (default: "")

  ## API Methods (exported functions)
  - `appendLine(text: string): void` - Append a new line of text
  - `clear(): void` - Clear all text content
  - `getText(): string` - Get current text content

  ## Usage Example
  ```svelte
  <script>
    let textArea;
  </script>

  <TextArea bind:this={textArea} monospace />

  <button on:click={() => textArea.appendLine("New log entry")}>Add Line</button>
  ```
-->
<script lang="ts" context="module">
  export interface TextAreaApi {
    appendLine: (text: string) => void;
    clear: () => void;
    getText: () => string;
  }
</script>

<script lang="ts">
  export let monospace: boolean = false;
  export let value: string = "";

  export function appendLine(text: string): void {
    if (value.length > 0) {
      value += "\n" + text;
    } else {
      value = text;
    }
  }

  export function clear(): void {
    value = "";
  }

  export function getText(): string {
    return value;
  }
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
