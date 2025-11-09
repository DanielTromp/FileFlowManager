<script lang="ts">
  /**
   * Error Alert Component (T138)
   * Displays actionable error messages with appropriate styling and suggestions
   */

  export let error: {
    code: string;
    message: string;
    details?: any;
  } | null = null;
  export let onDismiss: (() => void) | null = null;

  // Map error codes to user-friendly messages and actions (T138)
  const errorMessages: Record<string, { title: string; action?: string }> = {
    SCAN_FAILED: {
      title: "Scan Failed",
      action: "Check file permissions and try again",
    },
    INVALID_RULE_ID: {
      title: "Invalid Rule",
      action: "Please select a valid rule from the list",
    },
    PERMISSION_DENIED: {
      title: "Permission Denied",
      action:
        "Grant read/write permissions to FileFlow or run with administrator privileges",
    },
    CONFIG_INVALID: {
      title: "Configuration Error",
      action: "Check your configuration file for syntax errors",
    },
    EXECUTION_FAILED: {
      title: "Operation Failed",
      action: "Review the error details and try again",
    },
    INVALID_OPERATION_ID: {
      title: "Invalid Operation",
      action: "Refresh the scan results and try again",
    },
    DELETION_NOT_CONFIRMED: {
      title: "Deletion Not Confirmed",
      action: "Check the confirmation checkbox before deleting files",
    },
    DISK_SPACE_INSUFFICIENT: {
      title: "Insufficient Disk Space",
      action: "Free up disk space and try again",
    },
    RULE_NOT_FOUND: {
      title: "Rule Not Found",
      action: "The rule may have been deleted. Refresh the rules list",
    },
    VALIDATION_FAILED: {
      title: "Validation Error",
      action: "Check the form inputs and fix any validation errors",
    },
    CONFIG_WRITE_FAILED: {
      title: "Cannot Save Configuration",
      action: "Ensure you have write permissions for the config directory",
    },
    DUPLICATE_RULE_NAME: {
      title: "Duplicate Rule",
      action: "Choose a different name for your rule",
    },
    INVALID_THRESHOLD: {
      title: "Invalid Threshold",
      action: "Threshold must be a positive number",
    },
    NO_FILES_SPECIFIED: {
      title: "No Files Selected",
      action: "Select at least one file to proceed",
    },
    DATABASE_ERROR: {
      title: "Database Error",
      action: "Check database integrity or restart the application",
    },
    CONFIG_READ_FAILED: {
      title: "Cannot Read Configuration",
      action: "Check if the config file exists and is readable",
    },
    EXPORT_FAILED: {
      title: "Export Failed",
      action: "Check destination path and write permissions",
    },
    IMPORT_FAILED: {
      title: "Import Failed",
      action: "Ensure the file exists and is a valid FileFlow configuration",
    },
    FILE_NOT_FOUND: {
      title: "File Not Found",
      action: "Check that the file exists at the specified path",
    },
    DETECTION_FAILED: {
      title: "Detection Failed",
      action: "Screenshot location detection failed. Set the path manually",
    },
    UNKNOWN_ERROR: {
      title: "Unexpected Error",
      action: "Please try again or contact support if the issue persists",
    },
  };

  $: errorInfo = error ? errorMessages[error.code] || errorMessages.UNKNOWN_ERROR : null;
  $: hasDetails = error && error.details && Object.keys(error.details).length > 0;
</script>

{#if error}
  <div class="alert alert-error shadow-lg mb-4" role="alert">
    <div>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="stroke-current flex-shrink-0 h-6 w-6"
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
      <div>
        <h3 class="font-bold">{errorInfo?.title || "Error"}</h3>
        <div class="text-sm">{error.message}</div>
        {#if errorInfo?.action}
          <div class="text-sm mt-1 opacity-80">
            <span class="font-semibold">Action:</span>
            {errorInfo.action}
          </div>
        {/if}
        {#if hasDetails}
          <details class="mt-2 text-xs">
            <summary class="cursor-pointer">Technical Details</summary>
            <pre class="mt-1 p-2 bg-base-300 rounded overflow-x-auto">{JSON.stringify(
                error.details,
                null,
                2
              )}</pre>
          </details>
        {/if}
      </div>
    </div>
    {#if onDismiss}
      <div class="flex-none">
        <button class="btn btn-sm btn-ghost" on:click={onDismiss}>Dismiss</button>
      </div>
    {/if}
  </div>
{/if}

<style>
  /* Ensure error messages are readable */
  .alert-error {
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  pre {
    white-space: pre-wrap;
    word-wrap: break-word;
  }
</style>
