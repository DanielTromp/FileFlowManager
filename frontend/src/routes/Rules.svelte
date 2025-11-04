<script lang="ts">
  import { onMount } from 'svelte';
  import { ask } from '@tauri-apps/api/dialog';
  import { getRules, toggleRule, deleteRule } from '../lib/api';
  import type { Rule } from '../lib/types';

  let rules: Rule[] = [];
  let loading = false;
  let error: string | null = null;

  onMount(async () => {
    await loadRules();
  });

  async function loadRules() {
    loading = true;
    error = null;
    try {
      rules = await getRules();
      // Sort by priority
      rules.sort((a, b) => a.priority - b.priority);
    } catch (err) {
      console.error('Failed to load rules:', err);
      error = err instanceof Error ? err.message : 'Failed to load rules';
    } finally {
      loading = false;
    }
  }

  async function handleToggle(ruleId: string, currentEnabled: boolean) {
    try {
      console.log('Toggling rule:', ruleId, 'from', currentEnabled, 'to', !currentEnabled);
      const result = await toggleRule(ruleId, !currentEnabled);
      console.log('Toggle result:', result);
      await loadRules(); // Reload to reflect changes
    } catch (err) {
      console.error('Failed to toggle rule:', err);
      const errorMsg = err instanceof Error ? err.message : String(err);
      error = `Failed to toggle rule: ${errorMsg}`;
    }
  }

  async function handleDelete(ruleId: string, ruleName: string) {
    const confirmed = await ask(`Are you sure you want to delete the rule "${ruleName}"?`, {
      title: 'Delete Rule',
      type: 'warning'
    });

    if (!confirmed) {
      console.log('Delete cancelled by user');
      return;
    }

    try {
      console.log('Deleting rule:', ruleId);
      const result = await deleteRule(ruleId);
      console.log('Delete result:', result);
      await loadRules(); // Reload to reflect changes
    } catch (err) {
      console.error('Failed to delete rule:', err);
      const errorMsg = err instanceof Error ? err.message : String(err);
      error = `Failed to delete rule: ${errorMsg}`;
    }
  }

  function handleEdit(rule: Rule) {
    // TODO: Implement rule editor dialog
    alert(`Edit functionality for rule "${rule.name}" is not yet implemented.\n\nYou can use the CLI to edit rules:\n  fileflow rules update ${rule.id}`);
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-bold">Rules Configuration</h1>
      <p class="text-base-content/60 mt-1">Manage file organization rules</p>
    </div>
    <button class="btn btn-primary">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 mr-2"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 4v16m8-8H4"
        />
      </svg>
      Add New Rule
    </button>
  </div>

  <!-- Error Display -->
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

  <!-- Loading State -->
  {#if loading}
    <div class="flex justify-center py-12">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else if rules.length === 0}
    <!-- Empty State -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body text-center py-12">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-16 w-16 mx-auto text-base-content/40 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <h3 class="text-xl font-bold">No Rules Configured</h3>
        <p class="text-base-content/60 mt-2">
          Get started by creating your first file organization rule
        </p>
        <button class="btn btn-primary mt-4">Create First Rule</button>
      </div>
    </div>
  {:else}
    <!-- Rules List -->
    <div class="space-y-4">
      {#each rules as rule (rule.id)}
        <div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow">
          <div class="card-body">
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="flex items-center gap-3">
                  <h3 class="card-title">{rule.name}</h3>
                  <div class="badge badge-outline">Priority: {rule.priority}</div>
                  {#if rule.enabled}
                    <div class="badge badge-success">Enabled</div>
                  {:else}
                    <div class="badge badge-ghost">Disabled</div>
                  {/if}
                </div>
                <p class="text-sm text-base-content/60 mt-2">ID: {rule.id}</p>
              </div>

              <div class="flex gap-2">
                <label class="swap swap-flip">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    on:change={() => handleToggle(rule.id, rule.enabled)}
                  />
                  <div class="swap-on btn btn-sm btn-success">ON</div>
                  <div class="swap-off btn btn-sm btn-ghost">OFF</div>
                </label>

                <button class="btn btn-sm btn-ghost" title="Edit" on:click={() => handleEdit(rule)}>
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
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </button>

                <button
                  class="btn btn-sm btn-ghost btn-error"
                  title="Delete"
                  on:click={() => handleDelete(rule.id, rule.name)}
                >
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
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <div class="divider my-2"></div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 class="font-semibold mb-1">Source</h4>
                <p class="text-base-content/70">
                  <span class="font-mono text-xs">
                    {rule.source_directories.join(', ')}
                  </span>
                </p>
                <p class="text-base-content/70 mt-1">
                  Patterns: {rule.source_patterns.join(', ')}
                </p>
                {#if rule.exclude_patterns.length > 0}
                  <p class="text-base-content/70 mt-1">
                    Exclude: {rule.exclude_patterns.join(', ')}
                  </p>
                {/if}
              </div>

              <div>
                <h4 class="font-semibold mb-1">Destination</h4>
                <p class="text-base-content/70">
                  <span class="font-mono text-xs">{rule.destination}</span>
                </p>
                {#if rule.organize_by_date}
                  <p class="text-base-content/70 mt-1">
                    📅 Organize by date (YYYY/MM/DD)
                  </p>
                {/if}
                {#if rule.detect_duplicates}
                  <p class="text-base-content/70 mt-1">🔍 Detect duplicates</p>
                {/if}
              </div>
            </div>

            {#if rule.min_size_kb || rule.max_size_kb || rule.min_age_days || rule.max_age_days}
              <div class="mt-2 flex flex-wrap gap-2">
                {#if rule.min_size_kb}
                  <div class="badge badge-outline">Min: {rule.min_size_kb} KB</div>
                {/if}
                {#if rule.max_size_kb}
                  <div class="badge badge-outline">Max: {rule.max_size_kb} KB</div>
                {/if}
                {#if rule.min_age_days}
                  <div class="badge badge-outline">
                    Min age: {rule.min_age_days} days
                  </div>
                {/if}
                {#if rule.max_age_days}
                  <div class="badge badge-outline">
                    Max age: {rule.max_age_days} days
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
