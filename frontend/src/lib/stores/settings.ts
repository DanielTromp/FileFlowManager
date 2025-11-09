/**
 * Settings state management store
 */

import { writable, derived } from 'svelte/store';
import type { Configuration } from '$lib/types';

export interface SettingsState {
  configuration: Configuration | null;
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  configuration: null,
  loading: false,
  error: null,
};

export const settingsStore = writable<SettingsState>(initialState);

// Derived stores
export const configuration = derived(
  settingsStore,
  ($settings) => $settings.configuration
);
export const settingsLoading = derived(
  settingsStore,
  ($settings) => $settings.loading
);

// Actions
export const settingsActions = {
  setConfiguration(config: Configuration) {
    settingsStore.update((state) => ({
      ...state,
      configuration: config,
      loading: false,
      error: null,
    }));
  },

  updateConfiguration(updates: Partial<Configuration>) {
    settingsStore.update((state) => ({
      ...state,
      configuration: state.configuration
        ? { ...state.configuration, ...updates }
        : null,
    }));
  },

  setLoading(loading: boolean) {
    settingsStore.update((state) => ({
      ...state,
      loading,
    }));
  },

  setError(error: string | null) {
    settingsStore.update((state) => ({
      ...state,
      error,
      loading: false,
    }));
  },
};
