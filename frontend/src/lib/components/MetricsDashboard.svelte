<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getSystemMetrics, getCacheStatistics } from "$lib/api";
  import type { SystemMetrics, CacheStatistics } from "$lib/types";

  let metrics: SystemMetrics | null = null;
  let cacheStats: CacheStatistics | null = null;
  let loading = true;
  let error: string | null = null;
  let autoRefresh = false;
  let refreshInterval: number | null = null;

  onMount(() => {
    loadData();
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  async function loadData() {
    loading = true;
    error = null;
    try {
      [metrics, cacheStats] = await Promise.all([getSystemMetrics(), getCacheStatistics()]);
    } catch (e: any) {
      error = e.message || "Failed to load metrics";
      console.error("Failed to load metrics:", e);
    } finally {
      loading = false;
    }
  }

  function startAutoRefresh() {
    refreshInterval = window.setInterval(() => {
      loadData();
    }, 15000); // Refresh every 15 seconds
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

  function formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(2) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(2) + "K";
    }
    return num.toFixed(0);
  }

  function formatPercentage(rate: number): string {
    return (rate * 100).toFixed(2) + "%";
  }

  function getCacheHealthColor(hitRate: number): string {
    if (hitRate >= 0.8) return "text-success";
    if (hitRate >= 0.5) return "text-warning";
    return "text-error";
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold">Metrics Dashboard</h2>
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
      <button class="btn btn-sm btn-circle" on:click={loadData} disabled={loading}>
        <span class:animate-spin={loading}>↻</span>
      </button>
    </div>
  </div>

  {#if loading && !metrics}
    <div class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else if error}
    <div class="alert alert-error">
      <span>{error}</span>
    </div>
  {:else if metrics && cacheStats}
    <!-- Cache Statistics -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h3 class="card-title">Cache Performance</h3>
        {#if Object.keys(cacheStats.caches || {}).length === 0}
          <p class="text-base-content/60">No cache statistics available</p>
        {:else}
          <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {#each Object.entries(cacheStats.caches || {}) as [name, stats]}
              <div class="rounded-lg border border-base-300 p-4">
                <h4 class="mb-3 font-semibold capitalize">{name.replace(/_/g, " ")}</h4>

                <!-- Hit Rate -->
                <div class="mb-4">
                  <div class="mb-1 flex justify-between text-sm">
                    <span>Hit Rate</span>
                    <span class="font-bold {getCacheHealthColor(stats.hit_rate)}"
                      >{formatPercentage(stats.hit_rate)}</span
                    >
                  </div>
                  <progress
                    class="progress progress-primary w-full"
                    value={stats.hit_rate * 100}
                    max="100"
                  />
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div class="rounded bg-base-200 p-2">
                    <div class="text-xs text-base-content/60">Hits</div>
                    <div class="font-bold">{formatNumber(stats.hits)}</div>
                  </div>
                  <div class="rounded bg-base-200 p-2">
                    <div class="text-xs text-base-content/60">Misses</div>
                    <div class="font-bold">{formatNumber(stats.misses)}</div>
                  </div>
                  <div class="rounded bg-base-200 p-2">
                    <div class="text-xs text-base-content/60">Size</div>
                    <div class="font-bold">{stats.size}/{stats.capacity}</div>
                  </div>
                  <div class="rounded bg-base-200 p-2">
                    <div class="text-xs text-base-content/60">Evictions</div>
                    <div class="font-bold">{formatNumber(stats.evictions)}</div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- System Metrics -->
    <div class="grid gap-6 md:grid-cols-2">
      <!-- Counters -->
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h3 class="card-title">Counters</h3>
          {#if Object.keys(metrics.counters || {}).length === 0}
            <p class="text-base-content/60">No counters recorded</p>
          {:else}
            <div class="max-h-64 space-y-2 overflow-y-auto">
              {#each Object.entries(metrics.counters || {}).slice(0, 10) as [name, value]}
                <div class="flex justify-between rounded bg-base-200 p-3">
                  <span class="text-sm">{name}</span>
                  <span class="font-mono font-bold">{formatNumber(value)}</span>
                </div>
              {/each}
              {#if Object.keys(metrics.counters || {}).length > 10}
                <p class="text-center text-xs text-base-content/50">
                  +{Object.keys(metrics.counters || {}).length - 10} more
                </p>
              {/if}
            </div>
          {/if}
        </div>
      </div>

      <!-- Gauges -->
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h3 class="card-title">Gauges</h3>
          {#if Object.keys(metrics.gauges || {}).length === 0}
            <p class="text-base-content/60">No gauges recorded</p>
          {:else}
            <div class="max-h-64 space-y-2 overflow-y-auto">
              {#each Object.entries(metrics.gauges || {}).slice(0, 10) as [name, value]}
                <div class="flex justify-between rounded bg-base-200 p-3">
                  <span class="text-sm">{name}</span>
                  <span class="font-mono font-bold">{value.toFixed(2)}</span>
                </div>
              {/each}
              {#if Object.keys(metrics.gauges || {}).length > 10}
                <p class="text-center text-xs text-base-content/50">
                  +{Object.keys(metrics.gauges || {}).length - 10} more
                </p>
              {/if}
            </div>
          {/if}
        </div>
      </div>

      <!-- Timers -->
      <div class="card bg-base-100 shadow-xl md:col-span-2">
        <div class="card-body">
          <h3 class="card-title">Operation Timers</h3>
          {#if Object.keys(metrics.timers || {}).length === 0}
            <p class="text-base-content/60">No timing data recorded</p>
          {:else}
            <div class="overflow-x-auto">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Operation</th>
                    <th>Count</th>
                    <th>Mean</th>
                    <th>P50</th>
                    <th>P95</th>
                    <th>P99</th>
                    <th>Min/Max</th>
                  </tr>
                </thead>
                <tbody>
                  {#each Object.entries(metrics.timers || {}).slice(0, 10) as [name, timer]}
                    <tr>
                      <td class="font-medium">{name}</td>
                      <td>{timer.count}</td>
                      <td class="font-mono">{(timer.mean * 1000).toFixed(2)}ms</td>
                      <td class="font-mono">{(timer.p50 * 1000).toFixed(2)}ms</td>
                      <td class="font-mono">{(timer.p95 * 1000).toFixed(2)}ms</td>
                      <td class="font-mono">{(timer.p99 * 1000).toFixed(2)}ms</td>
                      <td class="font-mono text-xs"
                        >{(timer.min * 1000).toFixed(1)}/{(timer.max * 1000).toFixed(1)}ms</td
                      >
                    </tr>
                  {/each}
                </tbody>
              </table>
              {#if Object.keys(metrics.timers || {}).length > 10}
                <p class="mt-2 text-center text-xs text-base-content/50">
                  +{Object.keys(metrics.timers || {}).length - 10} more operations
                </p>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Last Updated -->
    <div class="text-center text-xs text-base-content/50">
      Last updated: {new Date(cacheStats.timestamp * 1000).toLocaleTimeString()}
    </div>
  {/if}
</div>
