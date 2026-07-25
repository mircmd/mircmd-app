export enum Language {
  System = 'system',
  English = 'english',
  Russian = 'russian',
}

export interface Window {
  pos: [number, number];
  size: [number, number];
}

export enum DockPosition {
  Left = 'left',
  Right = 'right',
  Bottom = 'bottom',
}

export interface Dock {
  visible: boolean;
  size: number;
}

export interface Docks {
  left: Dock;
  right: Dock;
  bottom: Dock;
}

export interface Panel {
  id: string;
  dock_position: DockPosition;
  visible: boolean;
}

export interface Workspace {
  docks: Docks;
  panels: Panel[];
}

export interface AppState {
  language: Language;
  window: Window;
  workspace: Workspace;
}
