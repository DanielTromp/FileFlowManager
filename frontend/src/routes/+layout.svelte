<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';

  let currentRoute = 'dashboard';

  const routes = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'rules', name: 'Rules', icon: '⚙️' },
    { id: 'large-files', name: 'Large Files', icon: '📦' },
    { id: 'old-files', name: 'Old Files', icon: '🕒' },
  ];

  onMount(() => {
    // Detect current route from URL
    if (typeof window !== 'undefined') {
      const path = window.location.pathname;
      const route = routes.find((r) => path.includes(r.id));
      if (route) currentRoute = route.id;
    }
  });

  function navigateTo(routeId: string) {
    currentRoute = routeId;
    // In a real SvelteKit app, we'd use goto() from $app/navigation
    // For now, this is a placeholder
  }
</script>

<div class="flex h-screen bg-base-200">
  <!-- Sidebar -->
  <aside class="w-64 bg-base-100 shadow-lg">
    <div class="p-4">
      <h1 class="text-2xl font-bold text-primary">FileFlow Manager</h1>
      <p class="text-sm text-base-content/60">Automated File Organization</p>
    </div>

    <nav class="mt-4">
      <ul class="menu">
        {#each routes as route}
          <li>
            <button
              class="flex items-center gap-3 {currentRoute === route.id ? 'active' : ''}"
              on:click={() => navigateTo(route.id)}
            >
              <span class="text-xl">{route.icon}</span>
              <span>{route.name}</span>
            </button>
          </li>
        {/each}
      </ul>
    </nav>

    <div class="absolute bottom-0 w-64 p-4 border-t border-base-300">
      <div class="text-xs text-base-content/60">
        <div>FileFlow Manager v0.1.0</div>
        <div class="mt-1">
          <button class="link link-primary text-xs">Settings</button> •
          <button class="link link-primary text-xs">Help</button>
        </div>
      </div>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="flex-1 overflow-auto">
    <div class="container mx-auto p-6">
      <slot />
    </div>
  </main>
</div>
