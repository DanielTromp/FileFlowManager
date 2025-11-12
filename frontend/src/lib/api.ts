/**
 * Tauri API wrapper functions for FileFlow Manager.
 *
 * Provides typed wrappers around Tauri invoke commands.
 */

import { invoke } from "@tauri-apps/api";
import type {
  AllOperationsProgress,
  CacheStatistics,
  Configuration,
  CreateRuleRequest,
  ExecuteOperationsRequest,
  FileMetadata,
  MetricsExport,
  OperationProgress,
  Rule,
  ScanFilesRequest,
  ScanResult,
  SystemHealthStatus,
  SystemMetrics,
  UpdateRuleRequest,
} from "./types";

/**
 * Scan files according to active rules
 */
export async function scanFiles(request: ScanFilesRequest): Promise<ScanResult> {
  console.log("[API] scanFiles called with:", request);
  const params = {
    request: {
      dry_run: request.dry_run,
      rule_ids: request.rule_ids || null,
    },
  };
  console.log("[API] Calling Tauri with params:", params);
  return await invoke<ScanResult>("scan_files", params);
}

/**
 * Execute planned file operations
 */
export async function executeOperations(request: ExecuteOperationsRequest): Promise<ScanResult> {
  return await invoke<ScanResult>("execute_operations", { ...request });
}

/**
 * Cancel an ongoing operation
 */
export async function cancelOperation(operationId: string): Promise<void> {
  return await invoke("cancel_operation", { operationId });
}

/**
 * Get all configured rules
 */
export async function getRules(): Promise<Rule[]> {
  return await invoke<Rule[]>("get_rules");
}

/**
 * Create a new rule
 */
export async function createRule(request: CreateRuleRequest): Promise<Rule> {
  return await invoke<Rule>("create_rule", { ruleData: request.rule });
}

/**
 * Update an existing rule
 */
export async function updateRule(request: UpdateRuleRequest): Promise<Rule> {
  return await invoke<Rule>("update_rule", { ruleId: request.rule_id, ruleData: request.updates });
}

/**
 * Delete a rule
 */
export async function deleteRule(ruleId: string): Promise<void> {
  return await invoke("delete_rule", { ruleId });
}

/**
 * Toggle a rule's enabled status
 */
export async function toggleRule(ruleId: string, enabled: boolean): Promise<Rule> {
  return await invoke<Rule>("toggle_rule", { ruleId, enabled });
}

/**
 * Get large files exceeding threshold
 */
export async function getLargeFiles(thresholdMb?: number, limit?: number): Promise<FileMetadata[]> {
  return await invoke<FileMetadata[]>("get_large_files", {
    thresholdMb,
    limit,
  });
}

/**
 * Get old files exceeding age threshold
 */
export async function getOldFiles(
  thresholdDays?: number,
  fileTypes?: string[],
  limit?: number
): Promise<FileMetadata[]> {
  return await invoke<FileMetadata[]>("get_old_files", {
    thresholdDays,
    fileTypes,
    limit,
  });
}

/**
 * Delete specified files
 */
export async function deleteFiles(
  filePaths: string[],
  confirmDeletions: boolean
): Promise<{
  deleted_count: number;
  failed_count: number;
  errors: string[];
  space_freed_mb: number;
}> {
  return await invoke("delete_files", {
    filePaths,
    confirmDeletions,
  });
}

/**
 * Get current configuration
 */
export async function getConfiguration(): Promise<Configuration> {
  return await invoke<Configuration>("get_configuration");
}

/**
 * Update configuration
 */
export async function updateConfiguration(updates: Partial<Configuration>): Promise<Configuration> {
  return await invoke<Configuration>("update_configuration", { updates });
}

/**
 * Export configuration to file
 */
export async function exportConfiguration(destinationPath: string): Promise<void> {
  return await invoke("export_configuration", { destinationPath });
}

/**
 * Import configuration from file
 */
export async function importConfiguration(sourcePath: string, merge: boolean): Promise<void> {
  return await invoke("import_configuration", {
    sourcePath,
    merge,
  });
}

/**
 * Auto-detect screenshot location
 */
export async function detectScreenshotLocation(): Promise<string> {
  return await invoke<string>("detect_screenshot_location");
}

/**
 * Get operation history from database
 */
export async function getOperationHistory(options?: {
  limit?: number;
  offset?: number;
  operation_type?: string;
  rule_id?: string;
  include_dry_runs?: boolean;
}): Promise<any[]> {
  return await invoke("get_operation_history", options || {});
}

/**
 * Get system status
 */
export async function getSystemStatus(): Promise<{
  status: "healthy" | "degraded" | "error";
  uptime_seconds: number;
  memory_usage_mb: number;
  database_size_mb: number;
}> {
  return await invoke("get_system_status");
}

/**
 * Clear cache
 */
export async function clearCache(
  clearChecksums: boolean,
  clearHistory: boolean
): Promise<{
  checksums_deleted: number;
  history_deleted: number;
  space_freed_mb: number;
}> {
  return await invoke("clear_cache", {
    clearChecksums,
    clearHistory,
  });
}

/**
 * Get system metrics (counters, gauges, histograms, timers)
 */
export async function getSystemMetrics(): Promise<SystemMetrics> {
  return await invoke<SystemMetrics>("get_system_metrics");
}

/**
 * Get system health status
 */
export async function getHealthStatus(): Promise<SystemHealthStatus> {
  return await invoke<SystemHealthStatus>("get_health_status");
}

/**
 * Get cache performance statistics
 */
export async function getCacheStatistics(): Promise<CacheStatistics> {
  return await invoke<CacheStatistics>("get_cache_statistics");
}

/**
 * Export metrics in specified format
 */
export async function exportMetrics(
  format: "json" | "prometheus" | "report" = "json",
  includeHealth: boolean = true
): Promise<MetricsExport> {
  return await invoke<MetricsExport>("export_metrics", {
    format,
    includeHealth,
  });
}

/**
 * Get progress for a specific operation
 */
export async function getOperationProgress(operationId: string): Promise<OperationProgress> {
  return await invoke<OperationProgress>("get_operation_progress", {
    operationId,
  });
}

/**
 * Get progress for all operations
 */
export async function getAllOperationsProgress(): Promise<AllOperationsProgress> {
  return await invoke<AllOperationsProgress>("get_all_operations_progress");
}
