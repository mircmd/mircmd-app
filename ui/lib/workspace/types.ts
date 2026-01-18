export interface DockItem {
  id: string;
  title: string;
  content: string;
}

export interface DockGroup {
  id: string;
  items: DockItem[];
  activeTabId: string;
  size: number;
}

export type DockPosition = "left" | "right" | "bottom";

export type DropZone = "center" | "before" | "after";

export interface WorkspaceState {
  left: DockGroup[];
  right: DockGroup[];
  bottom: DockGroup[];
}
