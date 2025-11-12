<script lang="ts">
  import SystemHealthDisplay from "$lib/components/SystemHealthDisplay.svelte";
  import MetricsDashboard from "$lib/components/MetricsDashboard.svelte";
  import OperationProgressDisplay from "$lib/components/OperationProgressDisplay.svelte";

  let activeTab: "health" | "metrics" | "progress" = "health";
</script>

<svelte:head>
  <title>Monitoring - FileFlow Manager</title>
</svelte:head>

<div class="container mx-auto p-6">
  <!-- Header -->
  <div class="mb-6">
    <h1 class="text-3xl font-bold">System Monitoring</h1>
    <p class="mt-2 text-base-content/70">
      Monitor system health, performance metrics, and operation progress
    </p>
  </div>

  <!-- Tabs -->
  <div class="tabs tabs-boxed mb-6">
    <button
      class="tab"
      class:tab-active={activeTab === "health"}
      on:click={() => (activeTab = "health")}
    >
      System Health
    </button>
    <button
      class="tab"
      class:tab-active={activeTab === "metrics"}
      on:click={() => (activeTab = "metrics")}
    >
      Metrics Dashboard
    </button>
    <button
      class="tab"
      class:tab-active={activeTab === "progress"}
      on:click={() => (activeTab = "progress")}
    >
      Operations Progress
    </button>
  </div>

  <!-- Content -->
  {#key activeTab}
    {#if activeTab === "health"}
      <SystemHealthDisplay />
    {:else if activeTab === "metrics"}
      <MetricsDashboard />
    {:else if activeTab === "progress"}
      <OperationProgressDisplay />
    {/if}
  {/key}
</div>
