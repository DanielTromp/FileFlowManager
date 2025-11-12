<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getAllOperationsProgress, cancelOperation } from "$lib/api";
  import type { AllOperationsProgress, OperationProgressStatus } from "$lib/types";

  let operationsProgress: AllOperationsProgress | null = null;
  let loading = true;
  let error: string | null = null;
  let autoRefresh = false;
  let refreshInterval: number | null = null;
  let cancellingOps = new Set<string>();

  onMount(() => {
    loadProgress();
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  async function loadProgress() {
    loading = true;
    error = null;
    try {
      operationsProgress = await getAllOperationsProgress();
    } catch (e: any) {
      error = e.message || "Failed to load operation progress";
      console.error("Failed to load operation progress:", e);
    } finally {
      loading = false;
    }
  }

  function startAutoRefresh() {
    refreshInterval = window.setInterval(() => {
      loadProgress();
    }, 2000); // Refresh every 2 seconds for real-time updates
  }

  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }

  function getStatusColor(status: OperationProgressStatus): string {
    switch (status) {
      case "completed":
        return "badge-success";
      case "running":
        return "badge-info";
      case "paused":
        return "badge-warning";
      case "cancelled":
      case "failed":
        return "badge-error";
      case "pending":
      default:
        return "badge-ghost";
    }
  }

  function getStatusIcon(status: OperationProgressStatus): string {
    switch (status) {
      case "completed":
        return "✓";
      case "running":
        return "▶";
      case "paused":
        return "⏸";
      case "cancelled":
        return "⏹";
      case "failed":
        return "✗";
      case "pending":
      default:
        return "⏱";
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs.toFixed(0)}s`;
  }

  function formatRate(rate: number): string {
    if (rate >= 1000) {
      return `${(rate / 1000).toFixed(2)}K/s`;
    }
    return `${rate.toFixed(1)}/s`;
  }

  async function handleCancel(opId: string) {
    cancellingOps.add(opId);
    cancellingOps = cancellingOps; // Trigger reactivity
    try {
      await cancelOperation(opId);
      // Refresh progress to show cancelled status
      await loadProgress();
    } catch (e: any) {
      console.error("Failed to cancel operation:", e);
      error = `Failed to cancel operation: ${e.message || e}`;
    } finally {
      cancellingOps.delete(opId);
      cancellingOps = cancellingOps; // Trigger reactivity
    }
  }
</script>

<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <div class="flex items-center justify-between">
      <h2 class="card-title">Operation Progress</h2>
      <div class="flex gap-2">
        <div class="form-control">
          <label class="label cursor-pointer gap-2">
            <span class="label-text text-xs">Auto-refresh</span>
            <input
              type="checkbox"
              class="toggle toggle-sm toggle-primary"
              checked={autoRefresh}
              on:change={toggleAutoRefresh}
            />
          </label>
        </div>
        <button class="btn btn-sm btn-circle" on:click={loadProgress} disabled={loading}>
          <span class:animate-spin={loading}>↻</span>
        </button>
      </div>
    </div>

    {#if loading && !operationsProgress}
      <div class="flex justify-center py-8">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    {:else if error}
      <div class="alert alert-error">
        <span>{error}</span>
      </div>
    {:else if operationsProgress}
      {#if Object.keys(operationsProgress.operations).length === 0}
        <div class="py-8 text-center">
          <p class="text-base-content/60">No operations in progress</p>
        </div>
      {:else}
        <div class="space-y-4">
          {#each Object.entries(operationsProgress.operations) as [opId, progress]}
            <div class="rounded-lg border border-base-300 p-4">
              <!-- Header -->
              <div class="mb-3 flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <div class="badge {getStatusColor(progress.status)} gap-1">
                      <span>{getStatusIcon(progress.status)}</span>
                      <span class="uppercase">{progress.status}</span>
                    </div>
                    <span class="text-sm font-mono text-base-content/60"
                      >{opId.substring(0, 8)}</span
                    >
                  </div>
                  {#if progress.current_item}
                    <p
                      class="mt-2 truncate text-sm text-base-content/70"
                      title={progress.current_item}
                    >
                      {progress.current_item}
                    </p>
                  {/if}
                </div>
                {#if progress.status === "running"}
                  <button
                    class="btn btn-sm btn-error btn-outline gap-2"
                    on:click={() => handleCancel(opId)}
                    disabled={cancellingOps.has(opId)}
                  >
                    {#if cancellingOps.has(opId)}
                      <span class="loading loading-spinner loading-xs"></span>
                      Cancelling...
                    {:else}
                      ⏹ Cancel
                    {/if}
                  </button>
                {/if}
              </div>

              <!-- Progress Bar -->
              {#if progress.status === "running" || progress.status === "paused"}
                <div class="mb-3">
                  <div class="mb-1 flex justify-between text-sm">
                    <span>{progress.completed_items} / {progress.total_items} items</span>
                    <span class="font-bold">{progress.percentage.toFixed(1)}%</span>
                  </div>
                  <progress
                    class="progress progress-primary w-full"
                    value={progress.percentage}
                    max="100"
                  />
                </div>
              {/if}

              <!-- Stats Grid -->
              <div class="grid grid-cols-3 gap-2 text-sm">
                <div class="rounded bg-base-200 p-2">
                  <div class="text-xs text-base-content/60">Elapsed</div>
                  <div class="font-mono font-bold">{formatDuration(progress.elapsed_time)}</div>
                </div>
                {#if progress.estimated_remaining !== null && progress.estimated_remaining !== undefined}
                  <div class="rounded bg-base-200 p-2">
                    <div class="text-xs text-base-content/60">Remaining</div>
                    <div class="font-mono font-bold">
                      {formatDuration(progress.estimated_remaining)}
                    </div>
                  </div>
                {/if}
                <div class="rounded bg-base-200 p-2">
                  <div class="text-xs text-base-content/60">Rate</div>
                  <div class="font-mono font-bold">{formatRate(progress.items_per_second)}</div>
                </div>
              </div>

              <!-- Error Message -->
              {#if progress.error_message}
                <div class="mt-3 rounded bg-error/10 p-2 text-sm text-error">
                  {progress.error_message}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}

      <!-- Last Updated -->
      <div class="mt-4 text-center text-xs text-base-content/50">
        Last updated: {new Date(operationsProgress.timestamp * 1000).toLocaleTimeString()}
      </div>
    {/if}
  </div>
</div>
