<script lang="ts">
  import { writable } from 'svelte/store';
  import Layout from './routes/+layout.svelte';
  import Dashboard from './routes/Dashboard.svelte';
  import Rules from './routes/Rules.svelte';

  // Create a store for the current route
  export const currentRoute = writable('dashboard');
</script>

<Layout {currentRoute}>
  {#if $currentRoute === 'dashboard'}
    <Dashboard />
  {:else if $currentRoute === 'rules'}
    <Rules />
  {:else if $currentRoute === 'large-files'}
    <div class="text-center py-12">
      <h2 class="text-2xl font-bold">Large Files</h2>
      <p class="text-base-content/60 mt-2">Coming soon in Phase 5</p>
    </div>
  {:else if $currentRoute === 'old-files'}
    <div class="text-center py-12">
      <h2 class="text-2xl font-bold">Old Files</h2>
      <p class="text-base-content/60 mt-2">Coming soon in Phase 5</p>
    </div>
  {:else}
    <Dashboard />
  {/if}
</Layout>
