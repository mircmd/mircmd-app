import { invoke } from '@tauri-apps/api/core';
import { isDesktop } from '../app';

export const open = {
  about: () => isDesktop && invoke('open_dialog', { window: 'About' }),
};
