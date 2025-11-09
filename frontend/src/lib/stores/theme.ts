/**
 * Theme Management Store (T155)
 *
 * Manages dark/light mode with system preference detection and persistence.
 */

import { writable, derived } from 'svelte/store';

export type Theme = 'light' | 'dark' | 'system';

// Get initial theme from localStorage or default to 'system'
function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'system';

  const stored = localStorage.getItem('fileflow-theme');
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored;
  }

  return 'system';
}

// Detect system theme preference
function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

// Create the theme preference store
export const themePreference = writable<Theme>(getInitialTheme());

// Create a derived store for the actual theme being used
export const activeTheme = derived(themePreference, ($pref) => {
  if ($pref === 'system') {
    return getSystemTheme();
  }
  return $pref;
});

// Apply theme to document
export function applyTheme(theme: 'light' | 'dark') {
  if (typeof window === 'undefined') return;

  document.documentElement.setAttribute('data-theme', theme);

  // Also set color-scheme for native browser elements
  document.documentElement.style.colorScheme = theme;
}

// Set theme preference
export function setTheme(theme: Theme) {
  if (typeof window === 'undefined') return;

  themePreference.set(theme);
  localStorage.setItem('fileflow-theme', theme);

  // Apply the theme
  const actualTheme = theme === 'system' ? getSystemTheme() : theme;
  applyTheme(actualTheme);
}

// Initialize theme on app load
export function initializeTheme() {
  if (typeof window === 'undefined') return;

  const pref = getInitialTheme();
  const actualTheme = pref === 'system' ? getSystemTheme() : pref;

  applyTheme(actualTheme);

  // Listen for system theme changes when using 'system' preference
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', (e) => {
    themePreference.subscribe((pref) => {
      if (pref === 'system') {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    })();
  });
}

// Helper to get theme icon
export function getThemeIcon(theme: Theme): string {
  switch (theme) {
    case 'light':
      return '☀️';
    case 'dark':
      return '🌙';
    case 'system':
      return '💻';
  }
}

// Helper to get theme label
export function getThemeLabel(theme: Theme): string {
  switch (theme) {
    case 'light':
      return 'Light';
    case 'dark':
      return 'Dark';
    case 'system':
      return 'System';
  }
}
