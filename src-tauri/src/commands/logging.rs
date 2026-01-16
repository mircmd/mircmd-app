use tauri;
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
