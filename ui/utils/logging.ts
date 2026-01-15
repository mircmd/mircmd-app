import { invoke } from '@tauri-apps/api/core';
import { isDesktop } from '../app';

const log = {
  info: (message: string) =>
    isDesktop ? invoke('log', { level: 'info', message }) : console.info(message),
  warn: (message: string) =>
    isDesktop ? invoke('log', { level: 'warn', message }) : console.warn(message),
  error: (message: string) =>
    isDesktop ? invoke('log', { level: 'error', message }) : console.error(message),
  debug: (message: string) =>
    isDesktop ? invoke('log', { level: 'debug', message }) : console.debug(message),
  trace: (message: string) =>
    isDesktop ? invoke('log', { level: 'trace', message }) : console.trace(message),
};

export default log;
