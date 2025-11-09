<script lang="ts">
  import { onMount } from "svelte";
  import { getLargeFiles, deleteFiles } from "$lib/api";
  import type { FileMetadata } from "$lib/types";
  import { confirm } from "@tauri-apps/api/dialog";
  import { notifyDeletionComplete } from "$lib/notifications";

  // State
  let threshold = 100; // MB
  let largeFiles: FileMetadata[] = [];
  let selectedFiles = new Set<string>();
  let isLoading = false;
  let error = "";
  let totalSize = 0;
  let selectedSize = 0;

  // Auto-load on mount
  onMount(() => {
    loadLargeFiles();
  });

  async function loadLargeFiles() {
    isLoading = true;
    error = "";

    try {
      const files = await getLargeFiles(threshold);
      largeFiles = files;
      calculateTotalSize();
    } catch (err) {
      console.error("Failed to load large files:", err);
      error = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }

  function calculateTotalSize() {
    totalSize = largeFiles.reduce((sum, file) => sum + file.size_bytes, 0);
  }

  function calculateSelectedSize() {
    selectedSize = largeFiles
      .filter((file) => selectedFiles.has(file.path))
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
    if (selectedFiles.size === largeFiles.length) {
      selectedFiles.clear();
    } else {
      largeFiles.forEach((file) => selectedFiles.add(file.path));
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
      { title: "Confirm Deletion", type: "warning" }
    );

    if (!confirmed) {
      return;
    }

    isLoading = true;
    error = "";

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
      await loadLargeFiles();
    } catch (err) {
      console.error("Failed to delete files:", err);
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
    if (ageInDays === null) return "N/A";
    if (ageInDays < 1) return "< 1 day";
    if (ageInDays < 30) return `${Math.floor(ageInDays)} days`;
    if (ageInDays < 365) return `${Math.floor(ageInDays / 30)} months`;
    return `${(ageInDays / 365).toFixed(1)} years`;
  }

  // Debounce timer
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;

  // Reactive update when threshold changes
  $: if (threshold > 0) {
    // Clear previous timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    // Debounce the update
    debounceTimer = setTimeout(() => {
      loadLargeFiles();
    }, 500);
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-bold">Large Files</h1>
      <p class="text-base-content/60 mt-1">
        Find and manage files larger than a specified threshold
      </p>
    </div>

    <button class="btn btn-primary" on:click={loadLargeFiles} disabled={isLoading}>
      {#if isLoading}
        <span class="loading loading-spinner loading-sm"></span>
        Scanning...
      {:else}
        Refresh
      {/if}
    </button>
  </div>

  <!-- Threshold Slider (T091) -->
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Size Threshold</h2>
      <div class="form-control">
        <label class="label">
          <span class="label-text">Find files larger than:</span>
          <span class="label-text-alt font-bold">{threshold} MB</span>
        </label>
        <input
          type="range"
          min="10"
          max="1000"
          step="10"
          bind:value={threshold}
          class="range range-primary"
        />
        <div class="w-full flex justify-between text-xs px-2 mt-1">
          <span>10 MB</span>
          <span>250 MB</span>
          <span>500 MB</span>
          <span>1000 MB</span>
        </div>
      </div>
    </div>
  </div>

  {#if error}
    <div class="alert alert-error">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="stroke-current shrink-0 h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>{error}</span>
    </div>
  {/if}

  <!-- Summary (T094) -->
  {#if !isLoading && largeFiles.length > 0}
    <div class="stats shadow w-full">
      <div class="stat">
        <div class="stat-title">Total Files</div>
        <div class="stat-value text-primary">{largeFiles.length}</div>
        <div class="stat-desc">Files found > {threshold} MB</div>
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
          {selectedFiles.size > 0 ? formatSize(selectedSize) : "None selected"}
        </div>
      </div>
    </div>
  {/if}

  <!-- File List (T092) -->
  {#if isLoading}
    <div class="flex justify-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else if largeFiles.length === 0}
    <div class="alert alert-info">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        class="stroke-current shrink-0 w-6 h-6"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        ></path>
      </svg>
      <span>No files found larger than {threshold} MB</span>
    </div>
  {:else}
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title">Files ({largeFiles.length})</h2>

          <!-- Delete Selected Button (T093) -->
          <div class="flex gap-2">
            <button class="btn btn-sm btn-outline" on:click={toggleAll}>
              {selectedFiles.size === largeFiles.length ? "Deselect All" : "Select All"}
            </button>
            <button
              class="btn btn-sm btn-error"
              on:click={handleDelete}
              disabled={selectedFiles.size === 0 || isLoading}
            >
              {#if isLoading}
                <span class="loading loading-spinner loading-xs"></span>
              {/if}
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
                    checked={selectedFiles.size === largeFiles.length && largeFiles.length > 0}
                    on:change={toggleAll}
                  />
                </th>
                <th>Filename</th>
                <th>Path</th>
                <th>Size</th>
                <th>Age</th>
              </tr>
            </thead>
            <tbody>
              {#each largeFiles as file}
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
                    {file.path.replace(file.filename, "")}
                  </td>
                  <td class="font-mono text-warning">{formatSize(file.size_bytes)}</td>
                  <td class="text-sm">{formatAge(file.age_days)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  {/if}
</div>
