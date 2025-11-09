/**
 * TypeScript type definitions for FileFlow Manager.
 *
 * These types match the Pydantic models from backend/fileflow_core/models.py
 */

export type OperationType = "move" | "delete" | "skip";

export type SkipReason =
  | "name_conflict"
  | "permission_denied"
  | "already_processed"
  | "file_not_found";

export interface Rule {
  id: string;
  enabled: boolean;
  name: string;
  description: string;
  source_patterns: string[];
  source_directories: string[];
  destination: string;
  organize_by_date: boolean;
  detect_duplicates: boolean;
  recursive_search: boolean;
  file_types: string[];
  priority: number;
  exclude_patterns: string[];
  min_size_kb?: number;
  max_size_kb?: number;
  min_age_days?: number;
  max_age_days?: number;
  created_at: string;
  last_modified: string;
}

export interface FileMetadata {
  path: string;
  filename: string;
  extension: string;
  size_bytes: number;
  created_at: string;
  modified_at: string;
  checksum?: string;
  matched_rules: string[];
  age_days?: number;
  size_mb?: number;
}

export interface FileOperation {
  id: string;
  timestamp: string;
  operation_type: OperationType;
  source_path: string;
  destination_path?: string;
  file_size: number;
  checksum: string;
  rule_id: string;
  dry_run: boolean;
  success: boolean;
  error_message?: string;
  skip_reason?: SkipReason;
  duplicate_of?: string;
}

export interface DuplicatePair {
  original_path: string;
  duplicate_path: string;
  checksum: string;
  file_size: number;
}

export interface ScanResult {
  scan_id: string;
  timestamp: string;
  total_files_scanned: number;
  files_matched: number;
  planned_operations: FileOperation[];
  duplicate_pairs: DuplicatePair[];
  large_files: FileMetadata[];
  old_files: FileMetadata[];
  scan_duration_ms: number;
  estimated_space_freed_mb?: number;
}

export interface GeneralSettings {
  log_level: "DEBUG" | "INFO" | "WARNING" | "ERROR";
  auto_run_on_startup: boolean;
  auto_run_interval_minutes: number;
  enable_notifications: boolean;
  cache_enabled: boolean;
}

export interface PathSettings {
  screenshot_source: string;
  screenshot_destination: string;
  monitored_directories: string[];
}

export interface ThresholdSettings {
  large_file_mb: number;
  old_file_days: number;
}

export interface DuplicateHandling {
  auto_delete_duplicates: boolean;
  always_keep_oldest: boolean;
}

export interface Configuration {
  general: GeneralSettings;
  paths: PathSettings;
  thresholds: ThresholdSettings;
  duplicate_handling: DuplicateHandling;
  rules: Rule[];
}

export interface CommandError {
  code: string;
  message: string;
  details?: unknown;
}

// Tauri command request/response types

export interface ScanFilesRequest {
  dry_run: boolean;
  rule_ids?: string[];
}

export interface ExecuteOperationsRequest {
  operation_ids: string[];
  confirm_deletions: boolean;
}

export interface CreateRuleRequest {
  rule: Omit<Rule, "id" | "created_at" | "last_modified">;
}

export interface UpdateRuleRequest {
  rule_id: string;
  updates: Partial<Omit<Rule, "id" | "created_at" | "last_modified">>;
}

export interface ProgressEvent {
  operation_id: string;
  operation_type: "scan" | "execute";
  progress_percent: number;
  current_file: string;
  files_processed: number;
  total_files: number;
  estimated_time_remaining_ms: number;
}
