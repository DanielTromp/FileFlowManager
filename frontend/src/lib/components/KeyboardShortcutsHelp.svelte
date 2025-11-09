<script lang="ts">
  /**
   * Keyboard Shortcuts Help Modal (T154)
   * Displays all available keyboard shortcuts to the user
   */

  import { onMount, onDestroy } from "svelte";
  import { formatShortcut, type ShortcutGroup } from "$lib/keyboardShortcuts";

  export let isOpen = false;
  export let onClose: () => void;
  export let shortcutGroups: ShortcutGroup[] = [];

  // Close on Escape key
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape" && isOpen) {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
  });
</script>

{#if isOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
    on:click={onClose}
    on:keydown={(e) => e.key === "Escape" && onClose()}
    role="button"
    tabindex="0"
  >
    <!-- Modal -->
    <div
      class="bg-base-100 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
      on:click|stopPropagation
      on:keydown|stopPropagation
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
    >
      <!-- Header -->
      <div
        class="sticky top-0 bg-base-100 border-b border-base-300 px-6 py-4 flex justify-between items-center"
      >
        <h2 id="shortcuts-title" class="text-2xl font-bold">⌨️ Keyboard Shortcuts</h2>
        <button class="btn btn-ghost btn-sm btn-circle" on:click={onClose} aria-label="Close">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="px-6 py-4 space-y-6">
        {#each shortcutGroups as group}
          <div>
            <h3 class="text-lg font-semibold mb-3 text-primary">{group.name}</h3>
            <div class="space-y-2">
              {#each group.shortcuts as shortcut}
                <div
                  class="flex justify-between items-center py-2 border-b border-base-200 last:border-0"
                >
                  <span class="text-base-content">{shortcut.description}</span>
                  <kbd class="kbd kbd-sm">{formatShortcut(shortcut)}</kbd>
                </div>
              {/each}
            </div>
          </div>
        {/each}

        <!-- Tips -->
        <div class="alert alert-info">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            class="stroke-current shrink-0 w-6 h-6"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
          <div>
            <h4 class="font-bold">Pro Tip</h4>
            <div class="text-xs">
              Press <kbd class="kbd kbd-xs">?</kbd> at any time to view this help dialog. Shortcuts are
              disabled when typing in input fields.
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="sticky bottom-0 bg-base-100 border-t border-base-300 px-6 py-4">
        <button class="btn btn-primary w-full" on:click={onClose}>Got it!</button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Ensure modal content is scrollable */
  .max-h-\[80vh\] {
    max-height: 80vh;
  }

  /* Keyboard key styling */
  .kbd {
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.875rem;
  }
</style>
