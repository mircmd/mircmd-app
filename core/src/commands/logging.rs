use crate::app_state::{LogLevel, LogMessage};
use tauri::{AppHandle, Emitter};
use tracing::{debug, error, info, trace, warn};

#[tauri::command]
pub fn log(level: String, message: String) {
    match level.as_str() {
        "error" => error!(target: "UI", "{}", message),
        "warn" => warn!(target: "UI", "{}", message),
        "info" => info!(target: "UI", "{}", message),
        "debug" => debug!(target: "UI", "{}", message),
        "trace" => trace!(target: "UI", "{}", message),
        _ => info!(target: "UI", "[UNKNOWN LEVEL] {}", message),
    }
}

#[tauri::command]
pub fn append_console_line(app: AppHandle, level: String, message: String) {
    let log_level = if level == "error" {
        error!(target: "UI", "{}", message);
        LogLevel::Error
    } else {
        info!(target: "UI", "{}", message);
        LogLevel::Info
    };
    let _ = app.emit(
        "console_output_append_line",
        LogMessage {
            level: log_level,
            message,
        },
    );
}
