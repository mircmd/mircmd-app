// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

mod app_state;
mod commands;
mod config;
mod consts;
mod file_manager;
mod logging;
mod menu;
mod plugins;
mod project;

use clap::Parser;
use std::path::PathBuf;
use std::sync::Mutex;
use tracing::debug;

#[derive(Parser, Debug)]
#[command(name = "Mir Commander")]
#[command(version, about, long_about = None)]
struct Cli {
    /// Path to import files. Will be opened in a temporary project.
    files: Vec<PathBuf>,
}

fn main() {
    let args = Cli::parse();

    let _guard = match logging::setup(false) {
        Ok(g) => g,
        Err(e) => {
            eprintln!("Failed to setup logger: {}", e);
            return;
        }
    };

    unsafe { std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1") };

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .register_uri_scheme_protocol("plugin", plugins::protocol::plugin_protocol_handler)
        .manage(Mutex::new(app_state::AppState::new()))
        .invoke_handler(tauri::generate_handler![
            commands::app::get_app_state,
            commands::app::get_startup_messages,
            commands::logging::log,
            commands::logging::append_console_line,
            commands::plugins::get_plugins,
            commands::fs::save_file_dialog,
            commands::fs::get_cwd,
            commands::fs::write_file,
            commands::project::get_project_root_node,
            commands::project::get_project_node_by_id,
            commands::project::get_project_node_data_by_id,
            commands::project::import_files,
        ])
        .setup(|app| {
            menu::create_menu(app)?;

            let state_handle = app.state::<Mutex<app_state::AppState>>();
            let mut state = state_handle.lock().unwrap();

            for file in args.files {
                match state.file_manager.import_file(&file) {
                    Ok(node) => {
                        state.project.root_node.add_child(node);
                    }
                    Err(e) => {
                        state.startup_messages.push(app_state::LogMessage {
                            level: app_state::LogLevel::Error,
                            message: format!("Failed to import file {}: {}", file.display(), e.to_string()),
                        });
                    }
                }
            }

            let window = WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
                .title("Mir Commander")
                .resizable(true)
                .position(state.config.window.pos.0 as f64, state.config.window.pos.1 as f64)
                .inner_size(state.config.window.size.0 as f64, state.config.window.size.1 as f64)
                .build()?;

            let window_handle = window.clone();

            window.on_window_event(move |event| {
                let scale_factor = window_handle.scale_factor().unwrap_or(1.0);
                let state_handle = window_handle.state::<Mutex<app_state::AppState>>();
                let mut state = state_handle.lock().unwrap();

                match event {
                    tauri::WindowEvent::Resized(physical_size) => {
                        let size = physical_size.to_logical::<u32>(scale_factor);
                        state.config.window.size = (size.width, size.height);
                    }

                    tauri::WindowEvent::Moved(physical_pos) => {
                        let pos = physical_pos.to_logical::<i32>(scale_factor);
                        state.config.window.pos = (pos.x, pos.y);
                    }

                    tauri::WindowEvent::CloseRequested { .. } => {
                        window_handle.app_handle().exit(0);
                    }
                    _ => {}
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application");

    app.run(|app_handle, event| match event {
        tauri::RunEvent::Ready => {
            debug!(target: "Core", "Mir Commander started");
        }
        tauri::RunEvent::Exit { .. } => {
            let state_handle = app_handle.state::<Mutex<app_state::AppState>>();
            if let Ok(state) = state_handle.lock() {
                state.config.save().ok();
            }
        }
        _ => {}
    });
}
