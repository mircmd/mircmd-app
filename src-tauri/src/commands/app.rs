use crate::app_state::{AppState, LogMessage};
use crate::config::Config;
use std::sync::Mutex;
use tauri;

#[tauri::command]
pub fn get_app_config(state: tauri::State<Mutex<AppState>>) -> Config {
    let app = state.lock().unwrap();

    app.config.clone()
}

#[tauri::command]
pub fn get_startup_messages(state: tauri::State<Mutex<AppState>>) -> Vec<LogMessage> {
    let app = state.lock().unwrap();

    app.startup_messages.clone()
}
