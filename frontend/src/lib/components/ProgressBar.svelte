<script lang="ts">
  export let progress: number = 0; // 0-100
  export let label: string = "";
  export let showPercentage: boolean = true;

  $: clampedProgress = Math.min(100, Math.max(0, progress));
</script>

<div class="w-full">
  {#if label}
    <div class="mb-2 flex justify-between text-sm">
      <span>{label}</span>
      {#if showPercentage}
        <span class="font-semibold">{clampedProgress.toFixed(0)}%</span>
      {/if}
    </div>
  {/if}
  <progress class="progress progress-primary w-full" value={clampedProgress} max="100" />
</div>
