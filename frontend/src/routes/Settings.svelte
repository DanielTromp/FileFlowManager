<script lang="ts">
  import { onMount } from 'svelte';
  import { open, save } from '@tauri-apps/api/dialog';
  import { exportConfiguration, importConfiguration, getConfiguration } from '../lib/api';
  import type { Configuration } from '../lib/types';

  // State
  let config: Configuration | null = null;
  let isLoading = false;
  let error = '';
  let successMessage = '';
  let mergeMode = false;

  // Load configuration on mount
  onMount(async () => {
    await loadConfiguration();
  });

  async function loadConfiguration() {
    isLoading = true;
    error = '';

    try {
      config = await getConfiguration();
    } catch (err) {
      console.error('Failed to load configuration:', err);
      error = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }

  async function handleExport() {
    error = '';
    successMessage = '';

    try {
      // Open save dialog
      const filePath = await save({
        title: 'Export Configuration',
        defaultPath: 'fileflow-config.toml',
        filters: [
          { name: 'TOML Files', extensions: ['toml'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });

      if (!filePath) {
        return; // User cancelled
      }

      isLoading = true;
      await exportConfiguration(filePath);
      successMessage = `Configuration exported successfully to: ${filePath}`;
    } catch (err) {
      console.error('Failed to export configuration:', err);
      error = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }

  async function handleImport() {
    error = '';
    successMessage = '';

    try {
      // Open file dialog
      const filePath = await open({
        title: 'Import Configuration',
        multiple: false,
        filters: [
          { name: 'TOML Files', extensions: ['toml'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });

      if (!filePath || typeof filePath !== 'string') {
        return; // User cancelled
      }

      isLoading = true;
      await importConfiguration(filePath, mergeMode);

      const mode = mergeMode ? 'merged' : 'replaced';
      successMessage = `Configuration ${mode} successfully from: ${filePath}`;

      // Reload configuration to show updated values
      await loadConfiguration();
    } catch (err) {
      console.error('Failed to import configuration:', err);
      error = err instanceof Error ? err.message : String(err);
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-bold">Settings</h1>
      <p class="text-base-content/60 mt-1">
        Manage your FileFlow Manager configuration
      </p>
    </div>

    <button
      class="btn btn-primary btn-sm"
      on:click={loadConfiguration}
      disabled={isLoading}
    >
      {#if isLoading}
        <span class="loading loading-spinner loading-xs"></span>
        Loading...
      {:else}
        Refresh
      {/if}
    </button>
  </div>

  <!-- Success Message -->
  {#if successMessage}
    <div class="alert alert-success">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{successMessage}</span>
    </div>
  {/if}

  <!-- Error Message -->
  {#if error}
    <div class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{error}</span>
    </div>
  {/if}

  <!-- Export/Import Configuration -->
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Configuration Portability</h2>
      <p class="text-base-content/60">
        Export your configuration to share across devices or create backups. Import configurations to restore settings or merge rules from other sources.
      </p>

      <div class="divider"></div>

      <!-- Export Section -->
      <div class="space-y-4">
        <div>
          <h3 class="text-lg font-semibold mb-2">Export Configuration</h3>
          <p class="text-sm text-base-content/60 mb-4">
            Save your current configuration (rules, settings, paths) to a TOML file.
          </p>
          <button
            class="btn btn-primary"
            on:click={handleExport}
            disabled={isLoading || !config}
          >
            {#if isLoading}
              <span class="loading loading-spinner loading-sm"></span>
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            {/if}
            Export Configuration
          </button>
        </div>

        <div class="divider"></div>

        <!-- Import Section -->
        <div>
          <h3 class="text-lg font-semibold mb-2">Import Configuration</h3>
          <p class="text-sm text-base-content/60 mb-4">
            Load configuration from a TOML file. Choose whether to replace your current configuration or merge rules.
          </p>

          <!-- Import Mode Toggle -->
          <div class="form-control mb-4">
            <label class="label cursor-pointer justify-start gap-3">
              <input
                type="checkbox"
                class="toggle toggle-primary"
                bind:checked={mergeMode}
              />
              <div>
                <span class="label-text font-semibold">
                  {mergeMode ? 'Merge Mode' : 'Replace Mode'}
                </span>
                <p class="text-xs text-base-content/60 mt-1">
                  {#if mergeMode}
                    Keep existing rules and add new ones from the imported file
                  {:else}
                    Replace all current settings and rules with imported configuration
                  {/if}
                </p>
              </div>
            </label>
          </div>

          <button
            class="btn btn-secondary"
            on:click={handleImport}
            disabled={isLoading}
          >
            {#if isLoading}
              <span class="loading loading-spinner loading-sm"></span>
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            {/if}
            Import Configuration
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Configuration Preview -->
  {#if config && !isLoading}
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">Current Configuration</h2>

        <div class="stats stats-vertical lg:stats-horizontal shadow w-full mt-4">
          <div class="stat">
            <div class="stat-title">Total Rules</div>
            <div class="stat-value text-primary">{config.rules?.length || 0}</div>
            <div class="stat-desc">Active organization rules</div>
          </div>

          <div class="stat">
            <div class="stat-title">Active Rules</div>
            <div class="stat-value text-secondary">
              {config.rules?.filter(r => r.enabled).length || 0}
            </div>
            <div class="stat-desc">Currently running</div>
          </div>

          <div class="stat">
            <div class="stat-title">Source Directories</div>
            <div class="stat-value text-accent">
              {config.rules?.reduce((sum, r) => sum + (r.source_directories?.length || 0), 0) || 0}
            </div>
            <div class="stat-desc">Monitored locations</div>
          </div>
        </div>

        <!-- General Settings Preview -->
        <div class="mt-6">
          <h3 class="text-lg font-semibold mb-3">General Settings</h3>
          <div class="overflow-x-auto">
            <table class="table table-zebra table-sm">
              <tbody>
                <tr>
                  <td class="font-semibold">Log Level</td>
                  <td>{config.general_settings?.log_level || 'INFO'}</td>
                </tr>
                <tr>
                  <td class="font-semibold">Auto Run on Startup</td>
                  <td>
                    {#if config.general_settings?.auto_run_on_startup}
                      <span class="badge badge-success">Enabled</span>
                    {:else}
                      <span class="badge badge-ghost">Disabled</span>
                    {/if}
                  </td>
                </tr>
                <tr>
                  <td class="font-semibold">Notifications</td>
                  <td>
                    {#if config.general_settings?.enable_notifications}
                      <span class="badge badge-success">Enabled</span>
                    {:else}
                      <span class="badge badge-ghost">Disabled</span>
                    {/if}
                  </td>
                </tr>
                <tr>
                  <td class="font-semibold">Cache</td>
                  <td>
                    {#if config.general_settings?.cache_enabled}
                      <span class="badge badge-success">Enabled</span>
                    {:else}
                      <span class="badge badge-ghost">Disabled</span>
                    {/if}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Rules Preview -->
        {#if config.rules && config.rules.length > 0}
          <div class="mt-6">
            <h3 class="text-lg font-semibold mb-3">Rules</h3>
            <div class="space-y-2">
              {#each config.rules as rule}
                <div class="flex items-center justify-between p-3 bg-base-200 rounded-lg">
                  <div class="flex items-center gap-3">
                    <div class="badge {rule.enabled ? 'badge-success' : 'badge-ghost'}">
                      {rule.enabled ? 'Active' : 'Inactive'}
                    </div>
                    <span class="font-medium">{rule.name}</span>
                  </div>
                  <div class="text-sm text-base-content/60">
                    {rule.file_types?.length || 0} file types
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>
  {:else if isLoading}
    <div class="flex justify-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {/if}
</div>
