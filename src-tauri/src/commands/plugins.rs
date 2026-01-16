use crate::app_state::AppState;
use crate::plugins::manager::PluginInfo;
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::State;

#[tauri::command]
pub async fn import_file(state: State<'_, Mutex<AppState>>, path: String) -> Result<(), String> {
    let mut state = state.lock().unwrap();

    let path_buf = PathBuf::from(path);

    state.import_file(&path_buf)
}

#[tauri::command]
pub fn get_plugins(state: State<'_, Mutex<AppState>>) -> Vec<PluginInfo> {
    let state = state.lock().unwrap();
    state.plugin_manager.all_plugins.clone()
}
