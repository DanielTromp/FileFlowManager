<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getHealthStatus } from "$lib/api";
  import type { SystemHealthStatus, HealthStatus } from "$lib/types";

  let healthStatus: SystemHealthStatus | null = null;
  let loading = true;
  let error: string | null = null;
  let autoRefresh = false;
  let refreshInterval: number | null = null;

  onMount(() => {
    console.log("[SystemHealthDisplay] Mounted");
    loadHealthStatus();
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  async function loadHealthStatus() {
    console.log("[SystemHealthDisplay] loadHealthStatus called");
    loading = true;
    error = null;
    try {
      console.log("[SystemHealthDisplay] Calling getHealthStatus...");
      healthStatus = await getHealthStatus();
      console.log("[SystemHealthDisplay] Got health status:", healthStatus);
      console.log("[SystemHealthDisplay] JSON.stringify:", JSON.stringify(healthStatus, null, 2));
      console.log("[SystemHealthDisplay] healthStatus.checks:", healthStatus?.checks);
      console.log("[SystemHealthDisplay] typeof healthStatus.checks:", typeof healthStatus?.checks);
      console.log("[SystemHealthDisplay] Object.keys:", Object.keys(healthStatus || {}));
    } catch (e: any) {
      error = e.message || "Failed to load health status";
      console.error("[SystemHealthDisplay] Failed to load health status:", e);
    } finally {
      loading = false;
      console.log("[SystemHealthDisplay] Loading complete, loading =", loading);
    }
  }

  function startAutoRefresh() {
    refreshInterval = window.setInterval(() => {
      loadHealthStatus();
    }, 10000); // Refresh every 10 seconds
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

  function getStatusColor(status: HealthStatus): string {
    switch (status) {
      case "healthy":
        return "badge-success";
      case "degraded":
        return "badge-warning";
      case "unhealthy":
        return "badge-error";
      default:
        return "badge-ghost";
    }
  }

  function getStatusIcon(status: HealthStatus): string {
    switch (status) {
      case "healthy":
        return "✓";
      case "degraded":
        return "⚠";
      case "unhealthy":
        return "✗";
      default:
        return "?";
    }
  }
</script>

<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <div class="flex items-center justify-between">
      <h2 class="card-title">System Health</h2>
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
        <button class="btn btn-sm btn-circle" on:click={loadHealthStatus} disabled={loading}>
          <span class:animate-spin={loading}>↻</span>
        </button>
      </div>
    </div>

    {#if loading && !healthStatus}
      <div class="flex justify-center py-8">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    {:else if error}
      <div class="alert alert-error">
        <span>{error}</span>
      </div>
    {:else if healthStatus}
      <!-- Overall Status -->
      <div class="alert alert-{getStatusColor(healthStatus.overall_status).replace('badge-', '')}">
        <div class="flex w-full items-center justify-between">
          <span class="font-bold">Overall Status</span>
          <div class="badge {getStatusColor(healthStatus.overall_status)} badge-lg gap-2">
            <span>{getStatusIcon(healthStatus.overall_status)}</span>
            <span class="uppercase">{healthStatus.overall_status}</span>
          </div>
        </div>
      </div>

      <!-- Individual Checks -->
      <div class="mt-4 space-y-3">
        {#each Object.entries(healthStatus.checks || {}) as [name, check]}
          <div class="rounded-lg border border-base-300 p-4">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <div class="badge {getStatusColor(check.status)} gap-1">
                    <span>{getStatusIcon(check.status)}</span>
                    <span class="uppercase">{check.status}</span>
                  </div>
                  <h3 class="font-semibold capitalize">{name.replace(/_/g, " ")}</h3>
                </div>
                <p class="mt-2 text-sm text-base-content/70">{check.message}</p>
                {#if check.latency_ms !== undefined}
                  <p class="mt-1 text-xs text-base-content/50">
                    Latency: {check.latency_ms.toFixed(2)}ms
                  </p>
                {/if}
              </div>
            </div>

            {#if check.details && Object.keys(check.details).length > 0}
              <div class="mt-3 rounded bg-base-200 p-3">
                <p class="mb-2 text-xs font-semibold text-base-content/70">Details:</p>
                <div class="space-y-1">
                  {#each Object.entries(check.details) as [key, value]}
                    <div class="flex justify-between text-xs">
                      <span class="text-base-content/60">{key}:</span>
                      <span class="font-mono text-base-content/80">{value}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- Last Updated -->
      <div class="mt-4 text-center text-xs text-base-content/50">
        Last updated: {new Date(healthStatus.timestamp * 1000).toLocaleTimeString()}
      </div>
    {/if}
  </div>
</div>
