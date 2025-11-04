<script lang="ts">
  import { writable } from 'svelte/store';
  import Layout from './routes/+layout.svelte';
  import Dashboard from './routes/Dashboard.svelte';
  import Rules from './routes/Rules.svelte';
  import LargeFiles from './routes/LargeFiles.svelte';
  import OldFiles from './routes/OldFiles.svelte';
  import Settings from './routes/Settings.svelte';

  // Create a store for the current route
  export const currentRoute = writable('dashboard');
</script>

<Layout {currentRoute}>
  {#if $currentRoute === 'dashboard'}
    <Dashboard />
  {:else if $currentRoute === 'rules'}
    <Rules />
  {:else if $currentRoute === 'large-files'}
    <LargeFiles />
  {:else if $currentRoute === 'old-files'}
    <OldFiles />
  {:else if $currentRoute === 'settings'}
    <Settings />
  {:else}
    <Dashboard />
  {/if}
</Layout>
