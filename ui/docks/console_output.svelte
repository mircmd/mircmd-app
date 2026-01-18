<!--
  @component ConsoleOutput

  Console output dock panel for displaying log messages.
  Wraps TextArea component with monospace font for readable log output.

  ## Features
  - Displays log messages in a scrollable text area
  - Monospace font for consistent formatting
  - Two-way binding for value manipulation

  ## Props
  - `value: string` - Console content, supports two-way binding (default: "")
-->
<script lang="ts">
  import TextArea from "../lib/text_area.svelte";

  interface Props {
    value?: string;
    onappend?: (text: string) => void;
    onclear?: () => void;
  }

  let { value = $bindable(""), onappend, onclear }: Props = $props();

  export function appendLine(text: string): void {
    if (onappend) {
      onappend(text);
    } else {
      value += (value ? "\n" : "") + text;
    }
  }

  export function clear(): void {
    if (onclear) {
      onclear();
    } else {
      value = "";
    }
  }
</script>

<TextArea bind:value monospace={false} />
