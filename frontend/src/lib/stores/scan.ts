/**
 * Scan state management store
 */

import { writable, derived } from 'svelte/store';
import type { ScanResult } from '$lib/types';

export interface ScanState {
  isScanning: boolean;
  lastScanResult: ScanResult | null;
  error: string | null;
}

const initialState: ScanState = {
  isScanning: false,
  lastScanResult: null,
  error: null,
};

export const scanStore = writable<ScanState>(initialState);

// Derived stores
export const isScanning = derived(scanStore, ($scan) => $scan.isScanning);
export const lastScanResult = derived(scanStore, ($scan) => $scan.lastScanResult);
export const scanError = derived(scanStore, ($scan) => $scan.error);

// Actions
export const scanActions = {
  startScan() {
    scanStore.update((state) => ({
      ...state,
      isScanning: true,
      error: null,
    }));
  },

  completeScan(result: ScanResult) {
    scanStore.update((state) => ({
      ...state,
      isScanning: false,
      lastScanResult: result,
      error: null,
    }));
  },

  failScan(error: string) {
    scanStore.update((state) => ({
      ...state,
      isScanning: false,
      error,
    }));
  },

  clearScan() {
    scanStore.set(initialState);
  },
};
