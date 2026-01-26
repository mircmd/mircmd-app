<!--
  @component ConsoleOutput

  Read-only text area component for displaying text content.
  Provides a scrollable text display area with optional monospace font support and optional show levels.

  ## Features
  - Read-only text display
  - Vertical scrolling for overflow content
  - Optional monospace font for code/logs display
  - Optional show levels

  ## Props
  - `monospace: boolean` - Use monospace font (default: true)
  - `showLevels: boolean` - Show levels (default: true)

  ## Usage Example
  ```svelte
  <script>
    let consoleOutputRef: ReturnType<typeof ConsoleOutput>;
  </script>

  <button onclick={() => consoleOutputRef?.appendLine("Info message", "info")}>Add message</button>
  <button onclick={() => consoleOutputRef?.appendLine("Warning message", "warning")}>Add message</button>
  <button onclick={() => consoleOutputRef?.appendLine("Error message", "error")}>Add message</button>
  <button onclick={() => consoleOutputRef?.appendLine("Debug message", "debug")}>Add message</button>
  <button onclick={() => consoleOutputRef?.toggleMonospace()}>Toggle monospace</button>
  <button onclick={() => consoleOutputRef?.toggleShowLevels()}>Toggle show levels</button>

  <ConsoleOutput bind:this={consoleOutputRef} />
  ```
-->
<script lang="ts">
  import { onMount } from "svelte";
  import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

  import Panel from "./lib/Panel.svelte";
  import { getStartupMessages } from "./core/commands";
  import type { LogMessage } from "./core/types";

  interface Props {
    monospace?: boolean;
    showLevels?: boolean;
  }

  let { monospace = true, showLevels = true }: Props = $props();
  let lines = $state<{ text: string; level: string }[]>([]);

  export function appendLine(text: string, level: string) {
    lines.push({ text, level });
  }

  export function clear() {
    lines = [];
  }

  export function toggleMonospace() {
    monospace = !monospace;
  }

  export function toggleShowLevels() {
    showLevels = !showLevels;
  }

  const appWebview = getCurrentWebviewWindow();
  appWebview.listen<LogMessage>("console_output_append_line", (event) => {
    lines.push({ text: event.payload.message, level: event.payload.level });
  });

  onMount(async () => {
    const startupMessages = await getStartupMessages();
    for (const message of startupMessages) {
      appendLine(message.message, message.level);
    }
  });
</script>

<Panel title="Console output">
  {#snippet content()}
    <div class="text-area">
      {#each lines as line}
        <p class="line">
          {#if showLevels}
            <span class={["level", line.level.toLowerCase()]} class:monospace>{line.level.toUpperCase()}</span>
          {/if}<span class="enable-selection" class:monospace>{line.text}</span>
        </p>
      {/each}
    </div>
  {/snippet}
</Panel>

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

  .line {
    padding: 0;
    margin: 0;
  }

  .level {
    display: inline-block;
    width: 65px;
    font-weight: 600;
    text-align: right;
    margin-right: 4px;
  }

  .debug {
    color: #808080;
  }

  .info {
    color: #008000;
  }

  .warning {
    color: #ffa500;
  }

  .error {
    color: #ff0000;
  }
</style>
