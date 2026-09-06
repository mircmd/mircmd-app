use serde::Deserialize;
use std::path::Path;
use tauri::AppHandle;
use tauri_plugin_dialog::{DialogExt, FileDialogBuilder};

#[derive(Deserialize)]
pub struct DialogFilter {
    pub name: String,
    pub extensions: Vec<String>,
}

#[tauri::command]
pub async fn save_file_dialog(
    app: AppHandle,
    default_path: Option<String>,
    filters: Option<Vec<DialogFilter>>,
) -> Option<String> {
    tauri::async_runtime::spawn_blocking(move || {
        let mut dialog = app.dialog().file();
        if let Some(default_path) = default_path.as_deref() {
            dialog = apply_default_path(dialog, default_path);
        }
        if let Some(filters) = filters.as_ref() {
            dialog = apply_filters(dialog, filters);
        }
        dialog
            .blocking_save_file()
            .and_then(|path| path.into_path().ok())
            .map(|path| path.to_string_lossy().into_owned())
    })
    .await
    .ok()
    .flatten()
}

#[tauri::command]
pub fn get_cwd() -> Result<String, String> {
    std::env::current_dir()
        .map(|path| path.to_string_lossy().into_owned())
        .map_err(|err| err.to_string())
}

#[tauri::command]
pub async fn write_file(path: String, data: Vec<u8>) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || {
        std::fs::write(&path, &data).map_err(|err| format!("{path}: {err}"))
    })
        .await
        .map_err(|err| err.to_string())?
}

fn apply_default_path<R: tauri::Runtime>(dialog: FileDialogBuilder<R>, default_path: &str) -> FileDialogBuilder<R> {
    let path = Path::new(default_path);
    let dialog = match path.parent() {
        Some(parent) if !parent.as_os_str().is_empty() => dialog.set_directory(parent),
        _ => dialog,
    };
    match path.file_name().and_then(|name| name.to_str()) {
        Some(name) if !name.is_empty() => dialog.set_file_name(name),
        _ => dialog,
    }
}

fn apply_filters<R: tauri::Runtime>(
    mut dialog: FileDialogBuilder<R>,
    filters: &[DialogFilter],
) -> FileDialogBuilder<R> {
    for filter in filters {
        let extensions: Vec<&str> = filter.extensions.iter().map(String::as_str).collect();
        dialog = dialog.add_filter(&filter.name, &extensions);
    }
    dialog
}
