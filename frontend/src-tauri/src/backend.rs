use std::process::Command;
use std::path::PathBuf;
use tauri::api::process::Command as TauriCommand;

/// Determines if we're running in production (from Applications) or development
fn is_production() -> bool {
    if let Ok(exe) = std::env::current_exe() {
        return exe.to_string_lossy().contains("/Applications/");
    }
    false
}

/// Get the path to the backend executable based on environment
pub fn get_backend_executable() -> Result<PathBuf, String> {
    if is_production() {
        // In production, use Tauri's sidecar resolution for externalBin
        // Tauri places external binaries in MacOS directory with -<triple> suffix
        if let Ok(exe) = std::env::current_exe() {
            if let Some(macos_dir) = exe.parent() {
                // Check for architecture-specific sidecar name
                #[cfg(target_arch = "aarch64")]
                let backend_name = "fileflow-backend-aarch64-apple-darwin";
                #[cfg(target_arch = "x86_64")]
                let backend_name = "fileflow-backend-x86_64-apple-darwin";

                let backend_exe = macos_dir.join(backend_name);
                if backend_exe.exists() {
                    return Ok(backend_exe);
                }

                // Fallback: try without architecture suffix
                let backend_exe_simple = macos_dir.join("fileflow-backend");
                if backend_exe_simple.exists() {
                    return Ok(backend_exe_simple);
                }
            }
        }

        Err("Backend executable not found in app bundle. Please reinstall the application.".to_string())
    } else {
        // Development mode - use the development executable

        // Strategy 1: Try relative path from current executable
        if let Ok(exe) = std::env::current_exe() {
            // exe is likely in frontend/src-tauri/target/debug/fileflow-manager (or similar)
            if let Some(target_dir) = exe.parent() {
                if let Some(debug_or_release) = target_dir.parent() {
                    if let Some(src_tauri) = debug_or_release.parent() {
                        if let Some(frontend) = src_tauri.parent() {
                            if let Some(project_root) = frontend.parent() {
                                let backend_exe = project_root.join("backend/dist/fileflow-backend");
                                if backend_exe.exists() {
                                    return Ok(backend_exe);
                                }
                            }
                        }
                    }
                }
            }
        }

        // Strategy 2: Try known development location
        let home = std::env::var("HOME").map_err(|_| "Failed to get HOME directory")?;
        let dev_backend_exe = PathBuf::from(&home).join("code/Filefly-specify/backend/dist/fileflow-backend");
        if dev_backend_exe.exists() {
            return Ok(dev_backend_exe);
        }

        Err("Could not locate backend executable. Have you run ./build_executable.sh in the backend directory?".to_string())
    }
}

/// Execute a Python backend command
pub fn execute_backend_command(command: &str, args: &serde_json::Value) -> Result<String, String> {
    let backend_executable = get_backend_executable()?;

    if !backend_executable.exists() {
        return Err(format!("Backend executable not found: {:?}", backend_executable));
    }

    // Execute the standalone backend binary
    let output = Command::new(&backend_executable)
        .arg(command)
        .arg(args.to_string())
        .output()
        .map_err(|e| format!("Failed to execute backend: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        return Err(format!("Backend error:\nStderr: {}\nStdout: {}", stderr, stdout));
    }

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}