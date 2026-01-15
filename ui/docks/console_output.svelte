<script lang="ts">
  import TextArea from "../lib/components/text_area.svelte";

  let textArea: TextArea;

  export function appendLine(text: string): void {
    textArea?.appendLine(text);
  }

  export function clear(): void {
    textArea?.clear();
  }
</script>

<TextArea bind:this={textArea} monospace={false} />
