<script lang="ts">
  import { onMount } from "svelte";
  import type { Writable } from "svelte/store";
  import { initializeTheme } from "$lib/stores/theme";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import { initializeNotifications } from "$lib/notifications";
  import { open } from "@tauri-apps/api/shell";

  export let currentRoute: Writable<string>;

  const routes = [
    { id: "dashboard", name: "Dashboard", icon: "📊" },
    { id: "rules", name: "Rules", icon: "⚙️" },
    { id: "large-files", name: "Large Files", icon: "📦" },
    { id: "old-files", name: "Old Files", icon: "🕒" },
    { id: "settings", name: "Settings", icon: "⚙️" },
  ];

  function navigateTo(routeId: string) {
    currentRoute.set(routeId);
  }

  async function openHelp() {
    // Open GitHub repository documentation
    await open("https://github.com/DanielTromp/Filefly-specify#readme");
  }

  // Initialize theme on mount (T155)
  // Initialize notifications on mount (T158)
  onMount(async () => {
    initializeTheme();
    await initializeNotifications();
  });
</script>

<div class="flex h-screen bg-base-200">
  <!-- Sidebar -->
  <aside class="w-64 bg-base-100 shadow-lg">
    <div class="p-4 flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-primary">FileFlow Manager</h1>
        <p class="text-sm text-base-content/60">Automated File Organization</p>
      </div>
      <!-- Theme Toggle (T155) -->
      <ThemeToggle />
    </div>

    <nav class="mt-4">
      <ul class="menu">
        {#each routes as route}
          <li>
            <button
              class="flex items-center gap-3 {$currentRoute === route.id ? 'active' : ''}"
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
        <button class="link link-primary text-xs" on:click={() => navigateTo("settings")}
          >Settings</button
        >
        •
        <button class="link link-primary text-xs" on:click={openHelp}>Help</button>
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
