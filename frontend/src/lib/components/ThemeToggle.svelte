<script lang="ts">
  /**
   * Theme Toggle Component (T155)
   * Allows users to switch between light, dark, and system themes
   */

  import { themePreference, setTheme, getThemeIcon, getThemeLabel, type Theme } from '$lib/stores/theme';

  let isOpen = false;

  const themes: Theme[] = ['light', 'dark', 'system'];

  function selectTheme(theme: Theme) {
    setTheme(theme);
    isOpen = false;
  }

  function toggleDropdown() {
    isOpen = !isOpen;
  }

  // Close dropdown when clicking outside
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.theme-toggle-dropdown')) {
      isOpen = false;
    }
  }
</script>

<svelte:window on:click={handleClickOutside} />

<div class="theme-toggle-dropdown relative">
  <button
    class="btn btn-ghost btn-sm btn-circle"
    on:click|stopPropagation={toggleDropdown}
    title="Change Theme"
    aria-label="Theme Selector"
  >
    <span class="text-xl">{getThemeIcon($themePreference)}</span>
  </button>

  {#if isOpen}
    <div
      class="absolute right-0 mt-2 w-48 bg-base-100 rounded-lg shadow-lg border border-base-300 z-50"
      on:click|stopPropagation
      on:keydown|stopPropagation
      role="menu"
    >
      <div class="py-2">
        {#each themes as theme}
          <button
            class="w-full px-4 py-2 text-left hover:bg-base-200 flex items-center justify-between transition-colors"
            class:bg-base-200={$themePreference === theme}
            class:font-bold={$themePreference === theme}
            on:click={() => selectTheme(theme)}
            role="menuitem"
          >
            <span class="flex items-center gap-2">
              <span class="text-xl">{getThemeIcon(theme)}</span>
              <span>{getThemeLabel(theme)}</span>
            </span>
            {#if $themePreference === theme}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-primary"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            {/if}
          </button>
        {/each}
      </div>

      <div class="border-t border-base-300 px-4 py-2 text-xs text-base-content/60">
        Syncs with system when set to System
      </div>
    </div>
  {/if}
</div>

<style>
  .theme-toggle-dropdown {
    position: relative;
  }

  /* Smooth transitions */
  button {
    transition: background-color 0.2s ease;
  }
</style>
