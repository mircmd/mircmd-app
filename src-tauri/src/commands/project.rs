use crate::app_state::{AppState, import_files as app_import_files};
use std::sync::Mutex;
use tauri::State;
use uuid::Uuid;

#[tauri::command]
pub fn get_node_data(state: State<'_, Mutex<AppState>>, node_id: String) -> Vec<u8> {
    let app = state.lock().unwrap();

    app.project
        .root_node
        .find_by_id(&Uuid::parse_str(&node_id).unwrap())
        .unwrap()
        .data
        .clone()
}

#[tauri::command]
pub fn import_files(app_handle: tauri::AppHandle, node_id: Option<String>) {
    app_import_files(app_handle, node_id);
}
