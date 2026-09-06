use crate::app_state::AppState;
use crate::plugins::manager::PluginInfo;
use std::sync::Mutex;
use tauri::State;

#[tauri::command]
pub fn get_plugins(state: State<'_, Mutex<AppState>>) -> Vec<PluginInfo> {
    let state = state.lock().unwrap();
    state.plugin_manager.all_plugins.clone()
}
