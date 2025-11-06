<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { scanFiles, getOperationHistory } from '../lib/api';
  import { scanStore, scanActions } from '../lib/stores/scan';
  import ProgressBar from '../lib/components/ProgressBar.svelte';
  import ConfirmDialog from '../lib/components/ConfirmDialog.svelte';
  import KeyboardShortcutsHelp from '../lib/components/KeyboardShortcutsHelp.svelte';
  import { registerShortcuts, type ShortcutGroup } from '../lib/keyboardShortcuts';
  import { notifyScanComplete, notifyExecutionComplete } from '../lib/notifications';

  let showConfirmExecute = false;
  let showShortcutsHelp = false;
  let lastScanTime: string | null = null;
  let activeRuleCount = 0;
  let operationHistory: any[] = [];
  let loadingHistory = false;
  let cleanupShortcuts: (() => void) | null = null;

  // Define keyboard shortcuts for this page (T154)
  const shortcutGroups: ShortcutGroup[] = [
    {
      name: 'Actions',
      shortcuts: [
        {
          key: 's',
          meta: true,
          description: 'Start Dry Run Scan',
          handler: handleDryRunScan,
        },
        {
          key: 'r',
          meta: true,
          description: 'Refresh History',
          handler: loadOperationHistory,
        },
        {
          key: 'e',
          meta: true,
          shift: true,
          description: 'Execute Operations',
          handler: () => {
            if (lastResult && !isScanning) {
              showConfirmExecute = true;
            }
          },
        },
      ],
    },
    {
      name: 'Help',
      shortcuts: [
        {
          key: '?',
          shift: true,
          description: 'Show Keyboard Shortcuts',
          handler: () => (showShortcutsHelp = true),
        },
      ],
    },
  ];

  onMount(async () => {
    // Initialize
    lastScanTime = new Date().toLocaleString();
    await loadOperationHistory();

    // Register keyboard shortcuts (T154)
    const allShortcuts = shortcutGroups.flatMap((group) => group.shortcuts);
    cleanupShortcuts = registerShortcuts(allShortcuts);
  });

  onDestroy(() => {
    // Cleanup keyboard shortcuts
    if (cleanupShortcuts) {
      cleanupShortcuts();
    }
  });

  async function loadOperationHistory() {
    loadingHistory = true;
    try {
      operationHistory = await getOperationHistory({ limit: 20, include_dry_runs: false });
    } catch (error) {
      console.error('Failed to load operation history:', error);
    } finally {
      loadingHistory = false;
    }
  }

  async function handleDryRunScan() {
    scanActions.startScan();
    try {
      console.log('Starting scan with dry_run=true');
      const result = await scanFiles({ dry_run: true });
      console.log('Scan result:', result);
      scanActions.completeScan(result);
      lastScanTime = new Date().toLocaleString();

      // Send notification (T158)
      await notifyScanComplete(result.files_matched, result.planned_operations.length);
    } catch (error) {
      console.error('Scan error:', error);
      const errorMsg = error instanceof Error ? error.message : String(error);
      scanActions.failScan(`Scan failed: ${errorMsg}`);
    }
  }

  async function handleExecute() {
    if (!$scanStore.lastScanResult) return;

    scanActions.startScan();
    try {
      const operationIds = $scanStore.lastScanResult.planned_operations.map((op) => op.id);
      const result = await scanFiles({ dry_run: false });
      scanActions.completeScan(result);
      showConfirmExecute = false;

      // Send notification (T158)
      const successCount = result.planned_operations.filter(op => !op.error_message).length;
      const failedCount = result.planned_operations.filter(op => op.error_message).length;
      const spaceFree = result.estimated_space_freed_mb || 0;
      await notifyExecutionComplete(successCount, failedCount, spaceFree);

      // Refresh operation history after execution
      await loadOperationHistory();
    } catch (error) {
      scanActions.failScan(error instanceof Error ? error.message : 'Execution failed');
    }
  }

  $: lastResult = $scanStore.lastScanResult;
  $: isScanning = $scanStore.isScanning;
  $: scanError = $scanStore.error;
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex justify-between items-start">
    <div>
      <h1 class="text-3xl font-bold">Dashboard</h1>
      <p class="text-base-content/60 mt-1">Scan and organize your files</p>
    </div>
    <!-- Keyboard Shortcuts Help Button (T154) -->
    <button
      class="btn btn-ghost btn-sm"
      on:click={() => (showShortcutsHelp = true)}
      title="Keyboard Shortcuts (Shift+?)"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span class="ml-1">Help</span>
    </button>
  </div>

  <!-- Status Cards -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="stats shadow">
      <div class="stat">
        <div class="stat-title">Last Scan</div>
        <div class="stat-value text-2xl">{lastScanTime || 'Never'}</div>
        <div class="stat-desc">Most recent scan time</div>
      </div>
    </div>

    <div class="stats shadow">
      <div class="stat">
        <div class="stat-title">Active Rules</div>
        <div class="stat-value text-2xl">{activeRuleCount}</div>
        <div class="stat-desc">Currently enabled</div>
      </div>
    </div>

    <div class="stats shadow">
      <div class="stat">
        <div class="stat-title">Files Matched</div>
        <div class="stat-value text-2xl">
          {lastResult?.files_matched || 0}
        </div>
        <div class="stat-desc">In last scan</div>
      </div>
    </div>
  </div>

  <!-- Actions -->
  <div class="card bg-base-100 shadow-lg">
    <div class="card-body">
      <h2 class="card-title">Quick Actions</h2>

      <div class="flex gap-4">
        <button
          class="btn btn-primary"
          on:click={handleDryRunScan}
          disabled={isScanning}
        >
          {isScanning ? 'Scanning...' : 'Dry Run Scan'}
        </button>

        <button
          class="btn btn-success"
          on:click={() => (showConfirmExecute = true)}
          disabled={!lastResult || isScanning}
        >
          Execute Operations
        </button>
      </div>

      {#if isScanning}
        <ProgressBar progress={50} label="Scanning files..." />
      {/if}

      {#if scanError}
        <div class="alert alert-error">
          <span>{scanError}</span>
        </div>
      {/if}
    </div>
  </div>

  <!-- Scan Results -->
  {#if lastResult}
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <h2 class="card-title">Scan Results</h2>

        <div class="stats stats-vertical lg:stats-horizontal shadow">
          <div class="stat">
            <div class="stat-title">Files Scanned</div>
            <div class="stat-value">{lastResult.total_files_scanned}</div>
          </div>

          <div class="stat">
            <div class="stat-title">Planned Operations</div>
            <div class="stat-value">{lastResult.planned_operations.length}</div>
          </div>

          <div class="stat">
            <div class="stat-title">Duplicates Found</div>
            <div class="stat-value">{lastResult.duplicate_pairs.length}</div>
          </div>

          <div class="stat">
            <div class="stat-title">Space to Free</div>
            <div class="stat-value text-success">
              {lastResult.estimated_space_freed_mb?.toFixed(1) || 0} MB
            </div>
          </div>
        </div>

        {#if lastResult.planned_operations.length > 0}
          <div class="mt-4">
            <h3 class="font-semibold mb-2">Planned Operations (first 10):</h3>
            <div class="overflow-x-auto">
              <table class="table table-zebra table-sm">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>File</th>
                    <th>Destination</th>
                  </tr>
                </thead>
                <tbody>
                  {#each lastResult.planned_operations.slice(0, 10) as operation}
                    <tr>
                      <td>
                        <span
                          class="badge {operation.operation_type === 'move'
                            ? 'badge-success'
                            : operation.operation_type === 'delete'
                              ? 'badge-error'
                              : 'badge-warning'}"
                        >
                          {operation.operation_type.toUpperCase()}
                        </span>
                      </td>
                      <td class="text-sm">{operation.source_path.split('/').pop()}</td>
                      <td class="text-sm text-base-content/60">
                        {operation.destination_path || 'N/A'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Operation History -->
  <div class="card bg-base-100 shadow-lg">
    <div class="card-body">
      <div class="flex justify-between items-center mb-2">
        <h2 class="card-title">Recent Operations</h2>
        <button class="btn btn-sm btn-ghost" on:click={loadOperationHistory}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {#if loadingHistory}
        <div class="flex justify-center py-8">
          <span class="loading loading-spinner loading-lg"></span>
        </div>
      {:else if operationHistory.length === 0}
        <div class="text-center py-8 text-base-content/60">
          <p>No operations executed yet</p>
          <p class="text-sm mt-1">Run a scan and execute operations to see history here</p>
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="table table-zebra table-sm">
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>File</th>
                <th>Destination</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {#each operationHistory as operation}
                <tr>
                  <td class="text-xs">
                    {new Date(operation.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <span
                      class="badge badge-sm {operation.operation_type === 'move'
                        ? 'badge-success'
                        : operation.operation_type === 'delete'
                          ? 'badge-error'
                          : 'badge-warning'}"
                    >
                      {operation.operation_type}
                    </span>
                  </td>
                  <td class="text-sm max-w-xs truncate" title={operation.source_path}>
                    {operation.source_path.split('/').pop()}
                  </td>
                  <td class="text-sm text-base-content/60 max-w-xs truncate" title={operation.destination_path}>
                    {operation.destination_path || 'N/A'}
                  </td>
                  <td>
                    {#if operation.success}
                      <span class="text-success">✓</span>
                    {:else}
                      <span class="text-error" title={operation.error_message}>✗</span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Execute Confirmation Dialog -->
<ConfirmDialog
  bind:isOpen={showConfirmExecute}
  title="Execute File Operations"
  message="This will move/delete {lastResult?.planned_operations.length || 0} files. This action cannot be undone. Continue?"
  confirmText="Execute"
  dangerous={true}
  onConfirm={handleExecute}
/>

<!-- Keyboard Shortcuts Help Modal (T154) -->
<KeyboardShortcutsHelp
  bind:isOpen={showShortcutsHelp}
  {shortcutGroups}
  onClose={() => (showShortcutsHelp = false)}
/>
