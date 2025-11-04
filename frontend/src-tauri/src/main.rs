// Prevents additional console window on Windows in release
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::Command;
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

/// Scan files using the Python backend
#[tauri::command]
async fn scan_files(dry_run: Option<bool>, rule_ids: Option<Vec<String>>) -> Result<ScanResult, String> {
    // Get the path to the Python backend
    // For development, we'll use poetry run from the backend directory
    // Current dir is /frontend/src-tauri, so go up 2 levels to project root
    let backend_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current dir: {}", e))?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    if !backend_dir.exists() {
        return Err(format!("Backend directory not found: {:?}", backend_dir));
    }

    let dry_run_arg = dry_run.unwrap_or(true);

    // Try to find poetry in common locations
    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry" // Hope it's in PATH
    };

    // Call the Python backend via tauri_commands.py
    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("scan_files")
        .arg(format!(r#"{{"dry_run":{}}}"#, dry_run_arg))
        .output()
        .map_err(|e| format!("Failed to execute Python backend (poetry: {}): {}", poetry_cmd, e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        return Err(format!("Python backend error:\nStderr: {}\nStdout: {}", stderr, stdout));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
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
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let args = serde_json::json!({
        "limit": limit.unwrap_or(100),
        "offset": offset.unwrap_or(0),
        "include_dry_runs": include_dry_runs.unwrap_or(false),
    });

    // Try to find poetry in common locations
    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry" // Hope it's in PATH
    };

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("get_operation_history")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get all rules
#[tauri::command]
async fn get_rules() -> Result<Vec<serde_json::Value>, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("get_rules")
        .arg("{}")
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Create a new rule
#[tauri::command]
async fn create_rule(rule_data: serde_json::Value) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({"rule_data": rule_data});

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("create_rule")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Update an existing rule
#[tauri::command]
async fn update_rule(rule_id: String, rule_data: serde_json::Value) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({"rule_id": rule_id, "rule_data": rule_data});

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("update_rule")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Delete a rule
#[tauri::command]
async fn delete_rule(rule_id: String) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({"rule_id": rule_id});

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("delete_rule")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Toggle rule enabled/disabled
#[tauri::command]
async fn toggle_rule(rule_id: String, enabled: bool) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({"rule_id": rule_id, "enabled": enabled});

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("toggle_rule")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get large files
#[tauri::command]
async fn get_large_files(threshold_mb: Option<u32>, limit: Option<u32>) -> Result<Vec<serde_json::Value>, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({
        "threshold_mb": threshold_mb.unwrap_or(100),
        "limit": limit
    });

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("get_large_files")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
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
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({
        "threshold_days": threshold_days.unwrap_or(90),
        "file_types": file_types,
        "limit": limit
    });

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("get_old_files")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Delete files
#[tauri::command]
async fn delete_files(file_paths: Vec<String>, confirm_deletions: bool) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({
        "file_paths": file_paths,
        "confirm_deletions": confirm_deletions
    });

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("delete_files")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Get current configuration
#[tauri::command]
async fn get_configuration() -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("get_configuration")
        .arg("{}")
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Export configuration to file
#[tauri::command]
async fn export_configuration(destination_path: String) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({"destination_path": destination_path});

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("export_configuration")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

/// Import configuration from file
#[tauri::command]
async fn import_configuration(source_path: String, merge: bool) -> Result<serde_json::Value, String> {
    let backend_dir = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .parent()
        .ok_or("Failed to get parent directory")?
        .parent()
        .ok_or("Failed to get grandparent directory")?
        .join("backend");

    let poetry_cmd = if std::path::Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if std::path::Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry"
    };

    let args = serde_json::json!({
        "source_path": source_path,
        "merge": merge
    });

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg("import_configuration")
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Python backend error: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            scan_files,
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
