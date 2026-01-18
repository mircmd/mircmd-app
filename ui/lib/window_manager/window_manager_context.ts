export interface PluginWindowData {
  pluginPath: string;
  htmlContent: string;
}

export interface WindowManagerContext {
  addWindow: (
    title: string,
    pluginPath: string,
    htmlContent: string,
    icon?: string
  ) => void;
  removeWindow: (id: string) => void;
}

let registeredContext: WindowManagerContext | null = null;

export function registerWindowManager(context: WindowManagerContext): void {
  registeredContext = context;
}

export function unregisterWindowManager(): void {
  registeredContext = null;
}

export function getWindowManager(): WindowManagerContext {
  if (!registeredContext) {
    throw new Error("WindowManager not registered");
  }
  return registeredContext;
}
