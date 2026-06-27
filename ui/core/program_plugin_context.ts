export interface ProgramPluginContext {
  host: HTMLElement;
  root: ShadowRoot;
  addStyles: (cssText: string) => void;
}

export function createProgramPluginContext(host: HTMLElement): ProgramPluginContext {
  const shadowRoot = host.attachShadow({ mode: 'open' });
  shadowRoot.innerHTML = "";

  return {
    host,
    root: shadowRoot,
    addStyles: (cssText) => {
      const style = document.createElement('style');
      style.textContent = cssText;
      shadowRoot.appendChild(style);
    }
  };
}
