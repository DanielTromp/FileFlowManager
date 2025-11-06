<script lang="ts">
  import { onMount } from 'svelte';
  import { getOldFiles, deleteFiles } from '../lib/api';
  import type { FileMetadata } from '../lib/types';
  import { confirm } from '@tauri-apps/api/dialog';
  import { notifyDeletionComplete } from '../lib/notifications';

  // State
  let threshold = 365; // days (T108) - default to 1 year for better performance
  let selectedFileTypes: string[] = []; // T109
  let oldFiles: FileMetadata[] = [];
  let allFiles: FileMetadata[] = []; // Store all files for pagination
  let selectedFiles = new Set<string>();
  let isLoading = false;
  let error = '';
  let totalSize = 0;
  let selectedSize = 0;

  // Pagination
  let currentPage = 1;
  let filesPerPage = 100;
  let totalPages = 1;

  // Common file types for filtering (T109)
  const commonFileTypes = [
    { label: 'Documents', extensions: ['pdf', 'doc', 'docx', 'txt'] },
    { label: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp'] },
    { label: 'Videos', extensions: ['mp4', 'avi', 'mov', 'mkv'] },
    { label: 'Archives', extensions: ['zip', 'rar', 'tar', 'gz'] },
    { label: 'Code', extensions: ['py', 'js', 'ts', 'java', 'cpp', 'c'] },
  ];

  // Auto-load on mount
  onMount(() => {
    loadOldFiles();
  });

  async function loadOldFiles() {
    isLoading = true;
    error = '';

    try {
      const fileTypes = selectedFileTypes.length > 0 ? selectedFileTypes : undefined;
      const files = await getOldFiles(threshold, fileTypes);
      allFiles = files;
      totalPages = Math.ceil(allFiles.length / filesPerPage);
      currentPage = 1; // Reset to first page
      updateDisplayedFiles();
      calculateTotalSize();
    } catch (err) {
      console.error('Failed to load old files:', err);
      error = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }

  function updateDisplayedFiles() {
    const startIndex = (currentPage - 1) * filesPerPage;
    const endIndex = startIndex + filesPerPage;
    oldFiles = allFiles.slice(startIndex, endIndex);
  }

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
      updateDisplayedFiles();
      selectedFiles.clear(); // Clear selection when changing pages
      selectedFiles = selectedFiles;
    }
  }

  function nextPage() {
    goToPage(currentPage + 1);
  }

  function prevPage() {
    goToPage(currentPage - 1);
  }

  function calculateTotalSize() {
    totalSize = allFiles.reduce((sum, file) => sum + file.size_bytes, 0);
  }

  function calculateSelectedSize() {
    selectedSize = oldFiles
      .filter(file => selectedFiles.has(file.path))
      .reduce((sum, file) => sum + file.size_bytes, 0);
  }

  function toggleFile(path: string) {
    if (selectedFiles.has(path)) {
      selectedFiles.delete(path);
    } else {
      selectedFiles.add(path);
    }
    selectedFiles = selectedFiles; // Trigger reactivity
    calculateSelectedSize();
  }

  function toggleAll() {
    // Check if all files on current page are selected
    const allCurrentPageSelected = oldFiles.every(file => selectedFiles.has(file.path));

    if (allCurrentPageSelected) {
      // Deselect all files on current page
      oldFiles.forEach(file => selectedFiles.delete(file.path));
    } else {
      // Select all files on current page
      oldFiles.forEach(file => selectedFiles.add(file.path));
    }
    selectedFiles = selectedFiles; // Trigger reactivity
    calculateSelectedSize();
  }

  async function handleDelete() {
    if (selectedFiles.size === 0) {
      return;
    }

    const confirmed = await confirm(
      `Are you sure you want to delete ${selectedFiles.size} file(s)?\n\n` +
      `This will free ${formatSize(selectedSize)}.\n\n` +
      `This action cannot be undone!`,
      { title: 'Confirm Deletion', type: 'warning' }
    );

    if (!confirmed) {
      return;
    }

    isLoading = true;
    error = '';

    try {
      const result = await deleteFiles(Array.from(selectedFiles), true);

      // Send notification (T158)
      await notifyDeletionComplete(result.deleted_count, result.space_freed_mb);

      // Show result
      alert(
        `Deletion complete:\n\n` +
        `✓ Deleted: ${result.deleted_count} files\n` +
        `✗ Failed: ${result.failed_count} files\n` +
        `💾 Space freed: ${result.space_freed_mb.toFixed(2)} MB`
      );

      // Clear selection and reload
      selectedFiles.clear();
      selectedFiles = selectedFiles;
      await loadOldFiles();
    } catch (err) {
      console.error('Failed to delete files:', err);
      error = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }

  function formatSize(bytes: number): string {
    const mb = bytes / (1024 * 1024);
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  }

  function formatAge(ageInDays: number | null): string {
    if (ageInDays === null) return 'N/A';
    if (ageInDays < 1) return '< 1 day';
    if (ageInDays < 30) return `${Math.floor(ageInDays)} days`;
    if (ageInDays < 365) return `${Math.floor(ageInDays / 30)} months`;
    return `${(ageInDays / 365).toFixed(1)} years`;
  }

  function toggleFileType(extensions: string[]) {
    // Toggle selection: if all are selected, deselect; otherwise select all
    const allSelected = extensions.every(ext => selectedFileTypes.includes(ext));

    if (allSelected) {
      // Remove all these extensions
      selectedFileTypes = selectedFileTypes.filter(ext => !extensions.includes(ext));
    } else {
      // Add all these extensions (avoiding duplicates)
      const newTypes = extensions.filter(ext => !selectedFileTypes.includes(ext));
      selectedFileTypes = [...selectedFileTypes, ...newTypes];
    }

    loadOldFiles();
  }

  // Debounce timer
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;

  // Reactive update when threshold changes (T108)
  $: if (threshold > 0) {
    // Clear previous timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    // Debounce the update - increased to 1s for better performance with large file lists
    debounceTimer = setTimeout(() => {
      loadOldFiles();
    }, 1000);
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-bold">Old Files</h1>
      <p class="text-base-content/60 mt-1">
        Find and manage files older than a specified threshold
      </p>
    </div>

    <button
      class="btn btn-primary"
      on:click={loadOldFiles}
      disabled={isLoading}
    >
      {isLoading ? 'Scanning...' : 'Refresh'}
    </button>
  </div>

  <!-- Threshold Slider (T108) -->
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Age Threshold</h2>
      <div class="form-control">
        <label class="label">
          <span class="label-text">Find files older than:</span>
          <span class="label-text-alt font-bold">{threshold} days ({(threshold / 30).toFixed(1)} months)</span>
        </label>
        <input
          type="range"
          min="30"
          max="365"
          step="10"
          bind:value={threshold}
          class="range range-primary"
        />
        <div class="w-full flex justify-between text-xs px-2 mt-1">
          <span>30 days</span>
          <span>90 days</span>
          <span>180 days</span>
          <span>1 year</span>
        </div>
      </div>
    </div>
  </div>

  <!-- File Type Filter (T109) -->
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">File Type Filter</h2>
      <div class="flex flex-wrap gap-2">
        {#each commonFileTypes as fileType}
          <button
            class="btn btn-sm"
            class:btn-primary={fileType.extensions.some(ext => selectedFileTypes.includes(ext))}
            class:btn-outline={!fileType.extensions.some(ext => selectedFileTypes.includes(ext))}
            on:click={() => toggleFileType(fileType.extensions)}
          >
            {fileType.label}
          </button>
        {/each}
        {#if selectedFileTypes.length > 0}
          <button
            class="btn btn-sm btn-ghost"
            on:click={() => { selectedFileTypes = []; loadOldFiles(); }}
          >
            Clear All
          </button>
        {/if}
      </div>
      {#if selectedFileTypes.length > 0}
        <p class="text-sm text-base-content/60 mt-2">
          Filtering: {selectedFileTypes.join(', ')}
        </p>
      {/if}
    </div>
  </div>

  {#if error}
    <div class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{error}</span>
    </div>
  {/if}

  <!-- Summary -->
  {#if !isLoading && allFiles.length > 0}
    <div class="stats shadow w-full">
      <div class="stat">
        <div class="stat-title">Total Files</div>
        <div class="stat-value text-primary">{allFiles.length}</div>
        <div class="stat-desc">Showing {oldFiles.length} on page {currentPage} of {totalPages}</div>
      </div>

      <div class="stat">
        <div class="stat-title">Total Size</div>
        <div class="stat-value text-secondary">{formatSize(totalSize)}</div>
        <div class="stat-desc">{(totalSize / (1024 * 1024 * 1024)).toFixed(2)} GB</div>
      </div>

      <div class="stat">
        <div class="stat-title">Selected Files</div>
        <div class="stat-value text-accent">{selectedFiles.size}</div>
        <div class="stat-desc">
          {selectedFiles.size > 0 ? formatSize(selectedSize) : 'None selected'}
        </div>
      </div>

      <div class="stat">
        <div class="stat-title">Average Age</div>
        <div class="stat-value text-info">
          {allFiles.length > 0 ? formatAge(allFiles.reduce((sum, f) => sum + (f.age_days || 0), 0) / allFiles.length) : 'N/A'}
        </div>
        <div class="stat-desc">Across all files</div>
      </div>
    </div>
  {/if}

  <!-- File List (T110) -->
  {#if isLoading}
    <div class="flex justify-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else if allFiles.length === 0}
    <div class="alert alert-info">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <span>No files found older than {threshold} days</span>
    </div>
  {:else}
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">Files ({oldFiles.length})</h2>

          <!-- Delete Selected Button (T111) -->
          <div class="flex gap-2">
            <button
              class="btn btn-sm btn-outline"
              on:click={toggleAll}
            >
              {oldFiles.every(file => selectedFiles.has(file.path)) ? 'Deselect Page' : 'Select Page'}
            </button>
            <button
              class="btn btn-sm btn-error"
              on:click={handleDelete}
              disabled={selectedFiles.size === 0}
            >
              Delete Selected ({selectedFiles.size})
            </button>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    class="checkbox"
                    checked={oldFiles.length > 0 && oldFiles.every(file => selectedFiles.has(file.path))}
                    on:change={toggleAll}
                  />
                </th>
                <th>Filename</th>
                <th>Path</th>
                <th>Age</th>
                <th>Size</th>
              </tr>
            </thead>
            <tbody>
              {#each oldFiles as file}
                <tr>
                  <td>
                    <input
                      type="checkbox"
                      class="checkbox"
                      checked={selectedFiles.has(file.path)}
                      on:change={() => toggleFile(file.path)}
                    />
                  </td>
                  <td class="font-medium">{file.filename}</td>
                  <td class="text-sm text-base-content/60 max-w-xs truncate" title={file.path}>
                    {file.path.replace(file.filename, '')}
                  </td>
                  <td class="font-mono text-warning">{formatAge(file.age_days)}</td>
                  <td class="text-sm">{formatSize(file.size_bytes)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Pagination Controls -->
        {#if totalPages > 1}
          <div class="flex justify-center items-center gap-2 mt-4">
            <button
              class="btn btn-sm"
              on:click={prevPage}
              disabled={currentPage === 1}
            >
              « Previous
            </button>

            <span class="text-sm">
              Page {currentPage} of {totalPages}
            </span>

            <button
              class="btn btn-sm"
              on:click={nextPage}
              disabled={currentPage === totalPages}
            >
              Next »
            </button>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
