use crate::app_state::AppState;
use crate::config::Config;
use crate::project::ProjectNode;
use std::sync::Mutex;
use tauri;
use uuid::Uuid;

#[tauri::command]
pub fn get_project_root_node(state: tauri::State<Mutex<AppState>>) -> ProjectNode {
    let app = state.lock().unwrap();

    app.project.root_node.clone()
}

#[tauri::command]
pub fn get_app_config(state: tauri::State<Mutex<AppState>>) -> Config {
    let app = state.lock().unwrap();

    app.config.clone()
}

#[tauri::command]
pub fn get_startup_messages(state: tauri::State<Mutex<AppState>>) -> Vec<String> {
    let mut app = state.lock().unwrap();

    std::mem::take(&mut app.startup_messages)
}

#[tauri::command]
pub fn get_node_data_by_id(state: tauri::State<Mutex<AppState>>, id: String) -> Option<Vec<u8>> {
    let app = state.lock().unwrap();
    let uuid = Uuid::parse_str(&id).ok()?;

    app.project.root_node.find_by_id(&uuid).map(|node| node.data.clone())
}
