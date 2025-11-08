// Prevents additional console window on Windows in release
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod backend;

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct ScanResult {
    scan_id: String,
    timestamp: String,
    total_files_scanned: u32,
    files_matched: u32,
    planned_operations: Vec<serde_json::Value>,
    duplicate_pairs: Vec<serde_json::Value>,
    estimated_space_freed_mb: f64,
    scan_duration_ms: u64,
}

#[derive(Debug, Deserialize)]
struct ScanFilesRequest {
    dry_run: Option<bool>,
    #[allow(dead_code)]
    rule_ids: Option<Vec<String>>,
}

/// Scan files using the Python backend
#[tauri::command]
async fn scan_files(request: ScanFilesRequest) -> Result<ScanResult, String> {
    let dry_run_arg = request.dry_run.unwrap_or(true);

    // Debug logging
    eprintln!("[TAURI] scan_files called with dry_run={:?} (unwrapped to: {})", request.dry_run, dry_run_arg);

    let args = serde_json::json!({
        "dry_run": dry_run_arg
    });

    eprintln!("[TAURI] Calling Python backend with JSON: {}", args);

    let stdout = backend::execute_backend_command("scan_files", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get operation history from the Python backend
#[tauri::command]
async fn get_operation_history(
    limit: Option<u32>,
    offset: Option<u32>,
    include_dry_runs: Option<bool>,
) -> Result<Vec<serde_json::Value>, String> {
    let args = serde_json::json!({
        "limit": limit.unwrap_or(100),
        "offset": offset.unwrap_or(0),
        "include_dry_runs": include_dry_runs.unwrap_or(false),
    });

    let stdout = backend::execute_backend_command("get_operation_history", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get all rules
#[tauri::command]
async fn get_rules() -> Result<Vec<serde_json::Value>, String> {
    let args = serde_json::json!({});

    let stdout = backend::execute_backend_command("get_rules", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Create a new rule
#[tauri::command]
async fn create_rule(rule_data: serde_json::Value) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({"rule_data": rule_data});

    let stdout = backend::execute_backend_command("create_rule", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Update an existing rule
#[tauri::command]
async fn update_rule(rule_id: String, rule_data: serde_json::Value) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({"rule_id": rule_id, "rule_data": rule_data});

    let stdout = backend::execute_backend_command("update_rule", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Delete a rule
#[tauri::command]
async fn delete_rule(rule_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({"rule_id": rule_id});

    let stdout = backend::execute_backend_command("delete_rule", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Toggle rule enabled/disabled
#[tauri::command]
async fn toggle_rule(rule_id: String, enabled: bool) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({"rule_id": rule_id, "enabled": enabled});

    let stdout = backend::execute_backend_command("toggle_rule", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get large files
#[tauri::command]
async fn get_large_files(threshold_mb: Option<u32>, limit: Option<u32>) -> Result<Vec<serde_json::Value>, String> {
    let args = serde_json::json!({
        "threshold_mb": threshold_mb.unwrap_or(100),
        "limit": limit
    });

    let stdout = backend::execute_backend_command("get_large_files", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get old files
#[tauri::command]
async fn get_old_files(
    threshold_days: Option<u32>,
    file_types: Option<Vec<String>>,
    limit: Option<u32>
) -> Result<Vec<serde_json::Value>, String> {
    let args = serde_json::json!({
        "threshold_days": threshold_days.unwrap_or(90),
        "file_types": file_types,
        "limit": limit
    });

    let stdout = backend::execute_backend_command("get_old_files", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Delete files
#[tauri::command]
async fn delete_files(file_paths: Vec<String>, confirm_deletions: bool) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "file_paths": file_paths,
        "confirm_deletions": confirm_deletions
    });

    let stdout = backend::execute_backend_command("delete_files", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get current configuration
#[tauri::command]
async fn get_configuration() -> Result<serde_json::Value, String> {
    let args = serde_json::json!({});

    let stdout = backend::execute_backend_command("get_configuration", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Export configuration to file
#[tauri::command]
async fn export_configuration(destination_path: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({"destination_path": destination_path});

    let stdout = backend::execute_backend_command("export_configuration", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Import configuration from file
#[tauri::command]
async fn import_configuration(source_path: String, merge: bool) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "source_path": source_path,
        "merge": merge
    });

    let stdout = backend::execute_backend_command("import_configuration", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Cancel an ongoing file operation
#[tauri::command]
async fn cancel_operation(operation_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "operation_id": operation_id
    });

    let stdout = backend::execute_backend_command("cancel_operation", &args)?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            scan_files,
            cancel_operation,
            get_operation_history,
            get_rules,
            create_rule,
            update_rule,
            delete_rule,
            toggle_rule,
            get_large_files,
            get_old_files,
            delete_files,
            get_configuration,
            export_configuration,
            import_configuration
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
