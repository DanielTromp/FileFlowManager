/**
 * Files state management store (large files, old files)
 */

import { writable } from 'svelte/store';
import type { FileMetadata } from '$lib/types';

export interface FilesState {
  largeFiles: FileMetadata[];
  oldFiles: FileMetadata[];
  selectedFiles: Set<string>;
  loading: boolean;
}

const initialState: FilesState = {
  largeFiles: [],
  oldFiles: [],
  selectedFiles: new Set(),
  loading: false,
};

export const filesStore = writable<FilesState>(initialState);

// Actions
export const filesActions = {
  setLargeFiles(files: FileMetadata[]) {
    filesStore.update((state) => ({
      ...state,
      largeFiles: files,
      loading: false,
    }));
  },

  setOldFiles(files: FileMetadata[]) {
    filesStore.update((state) => ({
      ...state,
      oldFiles: files,
      loading: false,
    }));
  },

  toggleFileSelection(filePath: string) {
    filesStore.update((state) => {
      const selected = new Set(state.selectedFiles);
      if (selected.has(filePath)) {
        selected.delete(filePath);
      } else {
        selected.add(filePath);
      }
      return { ...state, selectedFiles: selected };
    });
  },

  selectAll(files: FileMetadata[]) {
    filesStore.update((state) => ({
      ...state,
      selectedFiles: new Set(files.map((f) => f.path)),
    }));
  },

  clearSelection() {
    filesStore.update((state) => ({
      ...state,
      selectedFiles: new Set(),
    }));
  },

  setLoading(loading: boolean) {
    filesStore.update((state) => ({
      ...state,
      loading,
    }));
  },
};
