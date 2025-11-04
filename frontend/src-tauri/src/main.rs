// Prevents additional console window on Windows in release
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::process::{Command, Stdio};
use std::sync::Mutex;
use tauri::State;

// Application state
struct AppState {
    backend_process: Mutex<Option<std::process::Child>>,
}

// Tauri commands will be implemented here as we build the application
// For now, we'll set up the basic bridge structure

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! FileFlow Manager is starting...", name)
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            backend_process: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|_app| {
            // Backend sidecar will be initialized here
            // For now, we'll just start the Tauri app
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
