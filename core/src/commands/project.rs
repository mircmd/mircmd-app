use crate::app_state::{AppState, import_files as app_import_files};
use crate::project::ProjectNode;
use std::sync::Mutex;
use uuid::Uuid;

#[tauri::command]
pub fn get_project_root_node(state: tauri::State<Mutex<AppState>>) -> ProjectNode {
    let app = state.lock().unwrap();

    app.project.root_node.clone()
}

#[tauri::command]
pub fn get_project_node_by_id(state: tauri::State<Mutex<AppState>>, id: String) -> Option<ProjectNode> {
    let app = state.lock().unwrap();
    let uuid = Uuid::parse_str(&id).ok()?;

    app.project.root_node.find_by_id(&uuid).map(|node| node.clone())
}

#[tauri::command]
pub fn get_project_node_data_by_id(state: tauri::State<Mutex<AppState>>, id: String) -> Option<Vec<u8>> {
    let app = state.lock().unwrap();
    let uuid = Uuid::parse_str(&id).ok()?;

    app.project.root_node.find_by_id(&uuid).map(|node| node.data.clone())
}

#[tauri::command]
pub fn import_files(app_handle: tauri::AppHandle, node_id: Option<String>) {
    app_import_files(app_handle, node_id)
}
