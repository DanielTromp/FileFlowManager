<script lang="ts">
  import { createRule, updateRule } from '$lib/api';
  import type { Rule } from '$lib/types';

  export let isOpen = false;
  export let rule: Rule | null = null;
  export let onSave: () => void;
  export let onCancel: () => void;

  // Form state
  let name = '';
  let description = '';
  let enabled = true;
  let sourcePatterns = [''];
  let sourceDirectories = [''];
  let destination = '';
  let organizeByDate = false;
  let detectDuplicates = false;
  let recursiveSearch = true;
  let fileTypes = [''];
  let priority = 10;
  let excludePatterns = [''];
  let minSizeKb: number | null = null;
  let maxSizeKb: number | null = null;
  let minAgeDays: number | null = null;
  let maxAgeDays: number | null = null;

  // Validation state
  let errors: Record<string, string> = {};
  let showHints = false;
  let currentRuleId: string | null = null;

  // Initialize form when rule changes (only when it's a different rule)
  $: if (isOpen) {
    const ruleId = rule?.id || null;
    if (ruleId !== currentRuleId) {
      currentRuleId = ruleId;
      if (rule) {
        name = rule.name;
        description = rule.description;
        enabled = rule.enabled;
        sourcePatterns = [...rule.source_patterns];
        sourceDirectories = [...rule.source_directories];
        destination = rule.destination;
        organizeByDate = rule.organize_by_date;
        detectDuplicates = rule.detect_duplicates;
        recursiveSearch = rule.recursive_search;
        fileTypes = [...rule.file_types];
        priority = rule.priority;
        excludePatterns = rule.exclude_patterns.length > 0 ? [...rule.exclude_patterns] : [''];
        minSizeKb = rule.min_size_kb ?? null;
        maxSizeKb = rule.max_size_kb ?? null;
        minAgeDays = rule.min_age_days ?? null;
        maxAgeDays = rule.max_age_days ?? null;
      } else {
        // Reset to defaults for new rule
        name = '';
        description = '';
        enabled = true;
        sourcePatterns = [''];
        sourceDirectories = [''];
        destination = '';
        organizeByDate = false;
        detectDuplicates = false;
        recursiveSearch = true;
        fileTypes = [''];
        priority = 10;
        excludePatterns = [''];
        minSizeKb = null;
        maxSizeKb = null;
        minAgeDays = null;
        maxAgeDays = null;
      }
    }
  }

  function addItem(arr: string[]) {
    return [...arr, ''];
  }

  function removeItem(arr: string[], index: number) {
    return arr.filter((_, i) => i !== index);
  }

  function validateForm(): boolean {
    errors = {};

    if (!name.trim()) {
      errors.name = 'Name is required';
    } else if (name.length > 100) {
      errors.name = 'Name must be 100 characters or less';
    }

    if (!description.trim()) {
      errors.description = 'Description is required';
    } else if (description.length > 500) {
      errors.description = 'Description must be 500 characters or less';
    }

    const validSourcePatterns = sourcePatterns.filter(p => p.trim());
    if (validSourcePatterns.length === 0) {
      errors.sourcePatterns = 'At least one source pattern is required';
    }

    const validSourceDirs = sourceDirectories.filter(d => d.trim());
    if (validSourceDirs.length === 0) {
      errors.sourceDirectories = 'At least one source directory is required';
    }

    if (!destination.trim()) {
      errors.destination = 'Destination is required';
    }

    const validFileTypes = fileTypes.filter(t => t.trim());
    if (validFileTypes.length === 0) {
      errors.fileTypes = 'At least one file type is required';
    }

    if (priority < 1 || priority > 1000) {
      errors.priority = 'Priority must be between 1 and 1000';
    }

    if (minSizeKb !== null && minSizeKb < 0) {
      errors.minSizeKb = 'Minimum size cannot be negative';
    }

    if (maxSizeKb !== null && maxSizeKb < 0) {
      errors.maxSizeKb = 'Maximum size cannot be negative';
    }

    if (minSizeKb !== null && maxSizeKb !== null && maxSizeKb < minSizeKb) {
      errors.maxSizeKb = 'Maximum size must be greater than or equal to minimum size';
    }

    if (minAgeDays !== null && minAgeDays < 0) {
      errors.minAgeDays = 'Minimum age cannot be negative';
    }

    if (maxAgeDays !== null && maxAgeDays < 0) {
      errors.maxAgeDays = 'Maximum age cannot be negative';
    }

    return Object.keys(errors).length === 0;
  }

  async function handleSave() {
    if (!validateForm()) {
      return;
    }

    try {
      const ruleData = {
        name: name.trim(),
        description: description.trim(),
        enabled,
        source_patterns: sourcePatterns.filter(p => p.trim()),
        source_directories: sourceDirectories.filter(d => d.trim()),
        destination: destination.trim(),
        organize_by_date: organizeByDate,
        detect_duplicates: detectDuplicates,
        recursive_search: recursiveSearch,
        file_types: fileTypes.filter(t => t.trim()).map(t => t.startsWith('.') ? t.substring(1) : t),
        priority,
        exclude_patterns: excludePatterns.filter(p => p.trim()),
        min_size_kb: minSizeKb,
        max_size_kb: maxSizeKb,
        min_age_days: minAgeDays,
        max_age_days: maxAgeDays,
      };

      console.log('Saving rule with data:', ruleData);

      if (rule) {
        // Update existing rule
        console.log('Updating rule:', rule.id);
        const result = await updateRule({ rule_id: rule.id, updates: ruleData });
        console.log('Update result:', result);
      } else {
        // Create new rule
        console.log('Creating new rule');
        const result = await createRule({ rule: ruleData });
        console.log('Create result:', result);
      }

      onSave();
    } catch (err) {
      console.error('Failed to save rule:', err);
      console.error('Error details:', JSON.stringify(err, null, 2));

      // Try to extract a more useful error message
      let errorMessage = 'Failed to save rule';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err && typeof err === 'object') {
        errorMessage = JSON.stringify(err);
      }

      errors.general = errorMessage;
    }
  }

  function handleCancel() {
    errors = {};
    onCancel();
  }
</script>

{#if isOpen}
  <div class="modal modal-open">
    <div class="modal-box max-w-4xl max-h-[90vh] overflow-y-auto">
      <h3 class="font-bold text-2xl mb-4">
        {rule ? 'Edit Rule' : 'Create New Rule'}
      </h3>

      {#if errors.general}
        <div class="alert alert-error mb-4">
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
          <span>{errors.general}</span>
        </div>
      {/if}

      <form on:submit|preventDefault={handleSave} class="space-y-4">
        <!-- Basic Information -->
        <div class="form-control">
          <label class="label" for="name">
            <span class="label-text font-semibold">Rule Name *</span>
          </label>
          <input
            id="name"
            type="text"
            bind:value={name}
            class="input input-bordered"
            class:input-error={errors.name}
            placeholder="e.g., Screenshot Organization"
          />
          {#if errors.name}
            <label class="label">
              <span class="label-text-alt text-error">{errors.name}</span>
            </label>
          {/if}
        </div>

        <div class="form-control">
          <label class="label" for="description">
            <span class="label-text font-semibold">Description *</span>
          </label>
          <textarea
            id="description"
            bind:value={description}
            class="textarea textarea-bordered h-20"
            class:textarea-error={errors.description}
            placeholder="Describe what this rule does"
          />
          {#if errors.description}
            <label class="label">
              <span class="label-text-alt text-error">{errors.description}</span>
            </label>
          {/if}
        </div>

        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-2">
            <input type="checkbox" bind:checked={enabled} class="checkbox" />
            <span class="label-text">Enable this rule</span>
          </label>
        </div>

        <!-- Source Configuration -->
        <div class="divider">Source Configuration</div>

        <div class="form-control">
          <div class="flex justify-between items-center mb-2">
            <label class="label">
              <span class="label-text font-semibold">Source Patterns *</span>
            </label>
            <button
              type="button"
              class="btn btn-xs btn-ghost"
              on:click={() => showHints = !showHints}
            >
              {showHints ? 'Hide' : 'Show'} Hints
            </button>
          </div>
          {#if showHints}
            <div class="alert alert-info mb-2 text-sm">
              <span>
                <strong>Patterns:</strong> *.png, Screenshot*.png, *.{jpg,png}<br/>
                <strong>Env vars:</strong> ${'{'}DESKTOP{'}'}, ${'{'}DOWNLOADS{'}'}, ${'{'}HOME{'}'}<br/>
                <strong>Templates:</strong> {'{'}year{'}'}, {'{'}month{'}'}, {'{'}day{'}'}, {'{'}name{'}'}
              </span>
            </div>
          {/if}
          {#each sourcePatterns as pattern, i}
            <div class="flex gap-2 mb-2">
              <input
                type="text"
                bind:value={sourcePatterns[i]}
                class="input input-bordered flex-1"
                class:input-error={errors.sourcePatterns}
                placeholder="*.png or Screenshot*.png"
              />
              {#if sourcePatterns.length > 1}
                <button
                  type="button"
                  class="btn btn-square btn-ghost"
                  on:click={() => sourcePatterns = removeItem(sourcePatterns, i)}
                >
                  ✕
                </button>
              {/if}
            </div>
          {/each}
          <button
            type="button"
            class="btn btn-sm btn-ghost"
            on:click={() => sourcePatterns = addItem(sourcePatterns)}
          >
            + Add Pattern
          </button>
          {#if errors.sourcePatterns}
            <label class="label">
              <span class="label-text-alt text-error">{errors.sourcePatterns}</span>
            </label>
          {/if}
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">Source Directories *</span>
          </label>
          {#each sourceDirectories as dir, i}
            <div class="flex gap-2 mb-2">
              <input
                type="text"
                bind:value={sourceDirectories[i]}
                class="input input-bordered flex-1"
                class:input-error={errors.sourceDirectories}
                placeholder="${'{'}DESKTOP{'}'} or ~/Downloads"
              />
              {#if sourceDirectories.length > 1}
                <button
                  type="button"
                  class="btn btn-square btn-ghost"
                  on:click={() => sourceDirectories = removeItem(sourceDirectories, i)}
                >
                  ✕
                </button>
              {/if}
            </div>
          {/each}
          <button
            type="button"
            class="btn btn-sm btn-ghost"
            on:click={() => sourceDirectories = addItem(sourceDirectories)}
          >
            + Add Directory
          </button>
          {#if errors.sourceDirectories}
            <label class="label">
              <span class="label-text-alt text-error">{errors.sourceDirectories}</span>
            </label>
          {/if}
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">Exclude Patterns (Optional)</span>
          </label>
          {#each excludePatterns as pattern, i}
            <div class="flex gap-2 mb-2">
              <input
                type="text"
                bind:value={excludePatterns[i]}
                class="input input-bordered flex-1"
                placeholder="*_backup.png"
              />
              {#if excludePatterns.length > 1}
                <button
                  type="button"
                  class="btn btn-square btn-ghost"
                  on:click={() => excludePatterns = removeItem(excludePatterns, i)}
                >
                  ✕
                </button>
              {/if}
            </div>
          {/each}
          <button
            type="button"
            class="btn btn-sm btn-ghost"
            on:click={() => excludePatterns = addItem(excludePatterns)}
          >
            + Add Exclude Pattern
          </button>
        </div>

        <!-- Destination Configuration -->
        <div class="divider">Destination Configuration</div>

        <div class="form-control">
          <label class="label" for="destination">
            <span class="label-text font-semibold">Destination Directory *</span>
          </label>
          <input
            id="destination"
            type="text"
            bind:value={destination}
            class="input input-bordered"
            class:input-error={errors.destination}
            placeholder="~/Documents/Screenshots or ${'{'}HOME{'}'}/Screenshots"
          />
          {#if errors.destination}
            <label class="label">
              <span class="label-text-alt text-error">{errors.destination}</span>
            </label>
          {/if}
        </div>

        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-2">
            <input type="checkbox" bind:checked={organizeByDate} class="checkbox" />
            <span class="label-text">Organize by date (YYYY/MM/DD)</span>
          </label>
        </div>

        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-2">
            <input type="checkbox" bind:checked={detectDuplicates} class="checkbox" />
            <span class="label-text">Detect and skip duplicates</span>
          </label>
        </div>

        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-2">
            <input type="checkbox" bind:checked={recursiveSearch} class="checkbox" />
            <span class="label-text">Search in subdirectories (recursive)</span>
          </label>
        </div>

        <!-- File Type Configuration -->
        <div class="divider">File Type Configuration</div>

        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">File Types *</span>
          </label>
          {#each fileTypes as type, i}
            <div class="flex gap-2 mb-2">
              <input
                type="text"
                bind:value={fileTypes[i]}
                class="input input-bordered flex-1"
                class:input-error={errors.fileTypes}
                placeholder="iso, png, jpg (no dot needed)"
              />
              {#if fileTypes.length > 1}
                <button
                  type="button"
                  class="btn btn-square btn-ghost"
                  on:click={() => fileTypes = removeItem(fileTypes, i)}
                >
                  ✕
                </button>
              {/if}
            </div>
          {/each}
          <button
            type="button"
            class="btn btn-sm btn-ghost"
            on:click={() => fileTypes = addItem(fileTypes)}
          >
            + Add File Type
          </button>
          {#if errors.fileTypes}
            <label class="label">
              <span class="label-text-alt text-error">{errors.fileTypes}</span>
            </label>
          {/if}
        </div>

        <!-- Advanced Options -->
        <div class="divider">Advanced Options</div>

        <div class="form-control">
          <label class="label" for="priority">
            <span class="label-text font-semibold">Priority (1-1000)</span>
            <span class="label-text-alt">Lower numbers run first</span>
          </label>
          <input
            id="priority"
            type="number"
            bind:value={priority}
            min="1"
            max="1000"
            class="input input-bordered"
            class:input-error={errors.priority}
          />
          {#if errors.priority}
            <label class="label">
              <span class="label-text-alt text-error">{errors.priority}</span>
            </label>
          {/if}
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="form-control">
            <label class="label" for="minSizeKb">
              <span class="label-text">Min Size (KB)</span>
            </label>
            <input
              id="minSizeKb"
              type="number"
              bind:value={minSizeKb}
              min="0"
              class="input input-bordered"
              class:input-error={errors.minSizeKb}
              placeholder="Optional"
            />
            {#if errors.minSizeKb}
              <label class="label">
                <span class="label-text-alt text-error">{errors.minSizeKb}</span>
              </label>
            {/if}
          </div>

          <div class="form-control">
            <label class="label" for="maxSizeKb">
              <span class="label-text">Max Size (KB)</span>
            </label>
            <input
              id="maxSizeKb"
              type="number"
              bind:value={maxSizeKb}
              min="0"
              class="input input-bordered"
              class:input-error={errors.maxSizeKb}
              placeholder="Optional"
            />
            {#if errors.maxSizeKb}
              <label class="label">
                <span class="label-text-alt text-error">{errors.maxSizeKb}</span>
              </label>
            {/if}
          </div>

          <div class="form-control">
            <label class="label" for="minAgeDays">
              <span class="label-text">Min Age (Days)</span>
            </label>
            <input
              id="minAgeDays"
              type="number"
              bind:value={minAgeDays}
              min="0"
              class="input input-bordered"
              class:input-error={errors.minAgeDays}
              placeholder="Optional"
            />
            {#if errors.minAgeDays}
              <label class="label">
                <span class="label-text-alt text-error">{errors.minAgeDays}</span>
              </label>
            {/if}
          </div>

          <div class="form-control">
            <label class="label" for="maxAgeDays">
              <span class="label-text">Max Age (Days)</span>
            </label>
            <input
              id="maxAgeDays"
              type="number"
              bind:value={maxAgeDays}
              min="0"
              class="input input-bordered"
              class:input-error={errors.maxAgeDays}
              placeholder="Optional"
            />
            {#if errors.maxAgeDays}
              <label class="label">
                <span class="label-text-alt text-error">{errors.maxAgeDays}</span>
              </label>
            {/if}
          </div>
        </div>

        <!-- Actions -->
        <div class="modal-action">
          <button type="button" class="btn btn-ghost" on:click={handleCancel}>
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            {rule ? 'Update Rule' : 'Create Rule'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
