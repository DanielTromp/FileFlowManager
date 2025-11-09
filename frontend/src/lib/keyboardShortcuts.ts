/**
 * Keyboard Shortcuts Utility (T154)
 *
 * Provides a centralized system for managing keyboard shortcuts across the application.
 * Supports macOS (Cmd) and Windows/Linux (Ctrl) modifiers.
 */

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean; // Cmd on macOS
  alt?: boolean;
  shift?: boolean;
  description: string;
  handler: () => void;
}

export interface ShortcutGroup {
  name: string;
  shortcuts: KeyboardShortcut[];
}

/**
 * Check if a keyboard event matches a shortcut definition
 */
export function matchesShortcut(
  event: KeyboardEvent,
  shortcut: KeyboardShortcut
): boolean {
  // Check main key
  if (event.key.toLowerCase() !== shortcut.key.toLowerCase()) {
    return false;
  }

  // Check modifiers
  if (shortcut.ctrl && !event.ctrlKey) return false;
  if (!shortcut.ctrl && event.ctrlKey) return false;

  if (shortcut.meta && !event.metaKey) return false;
  if (!shortcut.meta && event.metaKey) return false;

  if (shortcut.alt && !event.altKey) return false;
  if (!shortcut.alt && event.altKey) return false;

  if (shortcut.shift && !event.shiftKey) return false;
  if (!shortcut.shift && event.shiftKey) return false;

  return true;
}

/**
 * Format shortcut for display
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const parts: string[] = [];

  if (shortcut.ctrl) parts.push(isMac ? '⌃' : 'Ctrl');
  if (shortcut.meta) parts.push(isMac ? '⌘' : 'Cmd');
  if (shortcut.alt) parts.push(isMac ? '⌥' : 'Alt');
  if (shortcut.shift) parts.push(isMac ? '⇧' : 'Shift');

  // Capitalize key
  parts.push(shortcut.key.toUpperCase());

  return parts.join(isMac ? '' : '+');
}

/**
 * Register keyboard shortcuts with cleanup
 */
export function registerShortcuts(
  shortcuts: KeyboardShortcut[]
): () => void {
  const handler = (event: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return;
    }

    for (const shortcut of shortcuts) {
      if (matchesShortcut(event, shortcut)) {
        event.preventDefault();
        event.stopPropagation();
        shortcut.handler();
        break;
      }
    }
  };

  window.addEventListener('keydown', handler);

  // Return cleanup function
  return () => {
    window.removeEventListener('keydown', handler);
  };
}

/**
 * Common application shortcuts
 */
export const COMMON_SHORTCUTS = {
  // Navigation
  DASHBOARD: { key: '1', meta: true, description: 'Go to Dashboard' },
  RULES: { key: '2', meta: true, description: 'Go to Rules' },
  LARGE_FILES: { key: '3', meta: true, description: 'Go to Large Files' },
  OLD_FILES: { key: '4', meta: true, description: 'Go to Old Files' },
  SETTINGS: { key: '5', meta: true, description: 'Go to Settings' },

  // Actions
  SCAN: { key: 's', meta: true, description: 'Start Scan' },
  REFRESH: { key: 'r', meta: true, description: 'Refresh Data' },
  EXECUTE: { key: 'e', meta: true, shift: true, description: 'Execute Operations' },
  NEW_RULE: { key: 'n', meta: true, description: 'Create New Rule' },

  // UI
  HELP: { key: '?', shift: true, description: 'Show Keyboard Shortcuts' },
  ESCAPE: { key: 'Escape', description: 'Cancel/Close' },
};

/**
 * Svelte action for keyboard shortcuts
 *
 * Usage:
 * <div use:shortcuts={myShortcuts}>
 */
export function shortcuts(
  _node: HTMLElement,
  shortcutList: KeyboardShortcut[]
) {
  const cleanup = registerShortcuts(shortcutList);

  return {
    destroy() {
      cleanup();
    },
    update(newShortcuts: KeyboardShortcut[]) {
      cleanup();
      registerShortcuts(newShortcuts);
    },
  };
}
