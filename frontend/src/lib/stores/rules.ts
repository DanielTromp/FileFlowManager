/**
 * Rules state management store with caching
 */

import { writable, derived, get } from 'svelte/store';
import type { Rule } from '$lib/types';
import { getRules } from '$lib/api';

export interface RulesState {
  rules: Rule[];
  loading: boolean;
  error: string | null;
  lastFetched: number | null; // timestamp of last fetch
}

const initialState: RulesState = {
  rules: [],
  loading: false,
  error: null,
  lastFetched: null,
};

export const rulesStore = writable<RulesState>(initialState);

// Derived stores
export const rules = derived(rulesStore, ($rules) => $rules.rules);
export const enabledRules = derived(rulesStore, ($rules) =>
  $rules.rules.filter((r) => r.enabled)
);
export const rulesLoading = derived(rulesStore, ($rules) => $rules.loading);

// Cache duration in milliseconds (5 minutes)
const CACHE_DURATION = 5 * 60 * 1000;

// Actions
export const rulesActions = {
  /**
   * Load rules from backend, using cache if available and valid
   */
  async loadRules(forceRefresh = false): Promise<void> {
    const state = get(rulesStore);

    // Use cache if available and not forcing refresh
    if (!forceRefresh && state.lastFetched && state.rules.length > 0) {
      const cacheAge = Date.now() - state.lastFetched;
      if (cacheAge < CACHE_DURATION) {
        console.log('[RulesStore] Using cached rules (age:', Math.round(cacheAge / 1000), 'seconds)');
        return;
      }
    }

    rulesStore.update((s) => ({ ...s, loading: true, error: null }));

    try {
      console.log('[RulesStore] Fetching rules from backend');
      const fetchedRules = await getRules();

      // Sort by priority
      fetchedRules.sort((a, b) => a.priority - b.priority);

      rulesStore.update((s) => ({
        ...s,
        rules: fetchedRules,
        loading: false,
        error: null,
        lastFetched: Date.now(),
      }));
    } catch (err) {
      console.error('[RulesStore] Failed to load rules:', err);
      const errorMsg = err instanceof Error ? err.message : 'Failed to load rules';
      rulesStore.update((s) => ({
        ...s,
        loading: false,
        error: errorMsg,
      }));
      throw err;
    }
  },

  /**
   * Invalidate the cache and reload rules
   */
  async refresh(): Promise<void> {
    return this.loadRules(true);
  },

  /**
   * Clear the cache without reloading
   */
  invalidateCache() {
    rulesStore.update((s) => ({
      ...s,
      lastFetched: null,
    }));
  },

  setRules(rules: Rule[]) {
    rulesStore.update((state) => ({
      ...state,
      rules,
      loading: false,
      error: null,
      lastFetched: Date.now(),
    }));
  },

  addRule(rule: Rule) {
    rulesStore.update((state) => ({
      ...state,
      rules: [...state.rules, rule].sort((a, b) => a.priority - b.priority),
      lastFetched: Date.now(),
    }));
  },

  updateRule(ruleId: string, updates: Partial<Rule>) {
    rulesStore.update((state) => ({
      ...state,
      rules: state.rules.map((r) => (r.id === ruleId ? { ...r, ...updates } : r)),
      lastFetched: Date.now(),
    }));
  },

  deleteRule(ruleId: string) {
    rulesStore.update((state) => ({
      ...state,
      rules: state.rules.filter((r) => r.id !== ruleId),
      lastFetched: Date.now(),
    }));
  },

  setLoading(loading: boolean) {
    rulesStore.update((state) => ({
      ...state,
      loading,
    }));
  },

  setError(error: string | null) {
    rulesStore.update((state) => ({
      ...state,
      error,
      loading: false,
    }));
  },
};
