use std::process::Command;
use std::path::{Path, PathBuf};

/// Determines if we're running in production (from Applications) or development
fn is_production() -> bool {
    if let Ok(exe) = std::env::current_exe() {
        return exe.to_string_lossy().contains("/Applications/");
    }
    false
}

/// Get the path to the Python backend based on environment
pub fn get_backend_dir() -> Result<PathBuf, String> {
    if is_production() {
        // In production, the backend should be bundled with the app
        // For now, we'll use the installed backend in the user's home
        let home = std::env::var("HOME").map_err(|_| "Failed to get HOME directory")?;
        let backend_path = PathBuf::from(&home).join("code/Filefly-specify/backend");

        if backend_path.exists() {
            Ok(backend_path)
        } else {
            // Fallback to a system-installed location
            Ok(PathBuf::from("/usr/local/lib/fileflow/backend"))
        }
    } else {
        // Development mode - try multiple strategies to find the backend

        // Strategy 1: Use FILEFLOW_BACKEND_PATH environment variable if set
        if let Ok(env_path) = std::env::var("FILEFLOW_BACKEND_PATH") {
            let backend_path = PathBuf::from(env_path);
            if backend_path.exists() {
                return Ok(backend_path);
            }
        }

        // Strategy 2: Try relative path from current executable
        if let Ok(exe) = std::env::current_exe() {
            // exe is likely in frontend/src-tauri/target/debug/fileflow-manager (or similar)
            if let Some(target_dir) = exe.parent() {
                if let Some(debug_or_release) = target_dir.parent() {
                    if let Some(src_tauri) = debug_or_release.parent() {
                        if let Some(frontend) = src_tauri.parent() {
                            if let Some(project_root) = frontend.parent() {
                                let backend_path = project_root.join("backend");
                                if backend_path.exists() {
                                    return Ok(backend_path);
                                }
                            }
                        }
                    }
                }
            }
        }

        // Strategy 3: Try known development location
        let home = std::env::var("HOME").map_err(|_| "Failed to get HOME directory")?;
        let dev_backend_path = PathBuf::from(&home).join("code/Filefly-specify/backend");
        if dev_backend_path.exists() {
            return Ok(dev_backend_path);
        }

        Err("Could not locate backend directory. Tried environment variable, relative path from executable, and ~/code/Filefly-specify/backend".to_string())
    }
}

/// Execute a Python backend command
pub fn execute_backend_command(command: &str, args: &serde_json::Value) -> Result<String, String> {
    let backend_dir = get_backend_dir()?;

    if !backend_dir.exists() {
        return Err(format!("Backend directory not found: {:?}", backend_dir));
    }

    // Always use Poetry since it has all the required dependencies installed
    // The system Python may not have the required packages
    let poetry_cmd = find_poetry_command();

    let output = Command::new(poetry_cmd)
        .current_dir(&backend_dir)
        .arg("run")
        .arg("python")
        .arg("-m")
        .arg("fileflow_api.tauri_commands")
        .arg(command)
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute Python backend with poetry: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        return Err(format!("Python backend error:\nStderr: {}\nStdout: {}", stderr, stdout));
    }

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

/// Find the poetry command in common locations
fn find_poetry_command() -> &'static str {
    if Path::new("/Users/daniel/.local/bin/poetry").exists() {
        "/Users/daniel/.local/bin/poetry"
    } else if Path::new("/usr/local/bin/poetry").exists() {
        "/usr/local/bin/poetry"
    } else {
        "poetry" // Hope it's in PATH
    }
}