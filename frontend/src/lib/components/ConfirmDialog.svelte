<script lang="ts">
  export let isOpen: boolean = false;
  export let title: string = "Confirm Action";
  export let message: string = "Are you sure?";
  export let confirmText: string = "Confirm";
  export let cancelText: string = "Cancel";
  export let onConfirm: () => void = () => {};
  export let onCancel: () => void = () => {};
  export let dangerous: boolean = false;

  function handleConfirm() {
    onConfirm();
    isOpen = false;
  }

  function handleCancel() {
    onCancel();
    isOpen = false;
  }
</script>

{#if isOpen}
  <div class="modal modal-open">
    <div class="modal-box">
      <h3 class="text-lg font-bold">{title}</h3>
      <p class="py-4">{message}</p>
      <div class="modal-action">
        <button class="btn" on:click={handleCancel}>
          {cancelText}
        </button>
        <button class="btn {dangerous ? 'btn-error' : 'btn-primary'}" on:click={handleConfirm}>
          {confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}
