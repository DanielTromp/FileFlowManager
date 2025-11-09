<script lang="ts">
  import type { FileMetadata } from '$lib/types';

  export let files: FileMetadata[] = [];
  export let selectedFiles: Set<string> = new Set();
  export let onToggleSelection: (filePath: string) => void = () => {};
  export let showCheckboxes: boolean = true;
  export let emptyMessage: string = 'No files found';

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  }
</script>

{#if files.length === 0}
  <div class="text-center py-8 text-base-content/60">
    {emptyMessage}
  </div>
{:else}
  <div class="overflow-x-auto">
    <table class="table table-zebra w-full">
      <thead>
        <tr>
          {#if showCheckboxes}
            <th>
              <input
                type="checkbox"
                class="checkbox"
                checked={files.length > 0 && files.every((f) => selectedFiles.has(f.path))}
                on:change={() => {
                  if (files.every((f) => selectedFiles.has(f.path))) {
                    files.forEach((f) => onToggleSelection(f.path));
                  } else {
                    files.forEach((f) => {
                      if (!selectedFiles.has(f.path)) onToggleSelection(f.path);
                    });
                  }
                }}
              />
            </th>
          {/if}
          <th>Name</th>
          <th>Size</th>
          <th>Modified</th>
          <th>Path</th>
        </tr>
      </thead>
      <tbody>
        {#each files as file}
          <tr>
            {#if showCheckboxes}
              <td>
                <input
                  type="checkbox"
                  class="checkbox"
                  checked={selectedFiles.has(file.path)}
                  on:change={() => onToggleSelection(file.path)}
                />
              </td>
            {/if}
            <td class="font-medium">{file.filename}</td>
            <td>{formatSize(file.size_bytes)}</td>
            <td>{formatDate(file.modified_at)}</td>
            <td class="text-sm text-base-content/60 max-w-xs truncate" title={file.path}>
              {file.path}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
