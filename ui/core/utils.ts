const MAC_MODIFIER_MAP: Record<string, string> = {
  control: "⌃",
  ctrl: "⌘",
  cmd: "⌘",
  command: "⌘",
  meta: "⌘",
  shift: "⇧",
  alt: "⌥",
  opt: "⌥",
  option: "⌥",
};

const MAC_KEY_MAP: Record<string, string> = {
  up: "↑",
  down: "↓",
  left: "←",
  right: "→",
};

const OTHER_KEY_MAP: Record<string, string> = {
  ctrl: "Ctrl",
  control: "Ctrl",
  shift: "Shift",
  alt: "Alt",
  opt: "Alt",
  option: "Alt",
  cmd: "Win",
  command: "Win",
  meta: "Win",
  up: "Up",
  down: "Down",
  left: "Left",
  right: "Right",
};

/**
 * Checks if the current environment is macOS or iOS.
 */
function isMacPlatform(): boolean {
  return typeof navigator !== "undefined" && /Mac|iPod|iPhone|iPad/i.test(navigator.userAgent);
}

/**
 * Parses a shortcut string into its constituent part names, taking care of edge cases.
 */
function parseShortcutParts(shortcut: string): string[] {
  let mainPart = shortcut;
  let lastKey = "";

  if (shortcut.length > 1 && (shortcut.endsWith("+") || shortcut.endsWith("-"))) {
    lastKey = shortcut.slice(-1);
    mainPart = shortcut.slice(0, -2);
  }

  const parts = mainPart.split(/[+-]/).map((part) => part.trim()).filter(Boolean);
  if (lastKey) {
    parts.push(lastKey);
  }
  return parts;
}

/**
 * Formats parsed shortcut parts with macOS symbols and guidelines.
 */
function formatMacShortcut(parts: string[]): string {
  const modifiers: string[] = [];
  const keys: string[] = [];

  parts.forEach((part) => {
    const lower = part.toLowerCase();
    if (lower in MAC_MODIFIER_MAP) {
      modifiers.push(MAC_MODIFIER_MAP[lower]!);
    } else if (lower in MAC_KEY_MAP) {
      keys.push(MAC_KEY_MAP[lower]!);
    } else {
      keys.push(part.charAt(0).toUpperCase() + part.slice(1));
    }
  });

  // Sort modifiers in standard Apple order: Control (⌃) -> Option (⌥) -> Shift (⇧) -> Command (⌘)
  modifiers.sort((a, b) => {
    const weights: Record<string, number> = { "⌃": 1, "⌥": 2, "⇧": 3, "⌘": 4 };
    return (weights[a] || 0) - (weights[b] || 0);
  });

  return [...modifiers, ...keys].join("");
}

/**
 * Formats parsed shortcut parts for non-macOS platforms.
 */
function formatOtherShortcut(parts: string[]): string {
  return parts
    .map((part) => {
      const lower = part.toLowerCase();
      if (lower in OTHER_KEY_MAP) {
        return OTHER_KEY_MAP[lower]!;
      }
      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join("+");
}

/**
 * Formats a keyboard shortcut string for display based on the operating system.
 * On macOS, modifiers are replaced with their standard Apple symbols (⌥, ⇧, ⌘)
 * and the '+' separators are removed, conforming to Human Interface Guidelines.
 * On other platforms, the shortcut is normalized to Title Case with '+' separators.
 */
export function formatShortcut(shortcut: string): string {
  if (!shortcut) return "";

  const parts = parseShortcutParts(shortcut);
  if (isMacPlatform()) {
    return formatMacShortcut(parts);
  }
  return formatOtherShortcut(parts);
}
