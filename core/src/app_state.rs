use crate::config::Config;
use crate::consts::Dirs;
use crate::file_manager::FileManager;
use crate::plugins::manager::PluginManager;
use crate::plugins::manifest::PluginType;
use crate::project::{Project, ProjectNode};
use serde::Serialize;
use std::sync::Mutex;
use tauri::Emitter;
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
use tracing::error;
use uuid::Uuid;

#[derive(Clone, Serialize)]
pub enum LogLevel {
    Info,
    Error,
}

#[derive(Clone, Serialize)]
struct ExplorerAddNodeEvent {
    pub parent_node_id: Option<String>,
    pub node: ProjectNode,
}

#[derive(Clone, Serialize)]
pub struct LogMessage {
    pub level: LogLevel,
    pub message: String,
}

pub struct AppState {
    pub config: Config,
    pub project: Project,
    pub plugin_manager: PluginManager,
    pub file_manager: FileManager,
    pub startup_messages: Vec<LogMessage>,
}

impl AppState {
    pub fn new() -> Self {
        let dirs = Dirs::get();

        let mut plugin_manager = PluginManager::new().expect("Failed to initialize PluginManager");
        if let Err(e) = plugin_manager.load_plugins(&dirs.plugins) {
            error!("Failed to load plugins: {}", e);
        }

        let file_manager_plugins = plugin_manager
            .core_plugins
            .get(&PluginType::FileImporter)
            .cloned()
            .unwrap_or_default();
        let file_manager = FileManager::new(file_manager_plugins);

        Self {
            config: Config::load(dirs.config.clone()),
            project: Project::new(true),
            plugin_manager,
            file_manager,
            startup_messages: vec![LogMessage {
                level: LogLevel::Info,
                message: format!("Mir Commander v{}", env!("CARGO_PKG_VERSION")),
            }],
        }
    }
}

pub fn import_files(app_handle: tauri::AppHandle, node_id: Option<String>) {
    app_handle.dialog().file().pick_files(move |file_paths| {
        if let Some(files) = file_paths {
            let state_handle = app_handle.state::<Mutex<AppState>>();
            let mut guard = state_handle.lock().unwrap();
            let state = &mut *guard;

            let project = &mut state.project;
            let file_manager = &mut state.file_manager;

            let node = match node_id {
                Some(ref id) => {
                    let uuid = Uuid::parse_str(id).unwrap();
                    match project.root_node.find_by_id_mut(&uuid) {
                        Some(node) => node,
                        None => {
                            error!("Node with id {} not found", id);
                            return;
                        }
                    }
                }
                None => &mut project.root_node,
            };

            for file in files {
                let file_path = file.as_path().unwrap();
                match file_manager.import_file(file_path) {
                    Ok(imported_node) => {
                        node.add_child(imported_node.clone());
                        let _ = app_handle.emit(
                            "explorer_add_node",
                            ExplorerAddNodeEvent {
                                parent_node_id: node_id.clone(),
                                node: imported_node,
                            },
                        );
                    }
                    Err(e) => {
                        let error_msg = format!("Failed to import file {}: {}", file_path.display(), e);
                        error!("{}", error_msg);
                        let _ = app_handle.emit(
                            "console_output_append_line",
                            LogMessage {
                                level: LogLevel::Error,
                                message: error_msg,
                            },
                        );
                    }
                }
            }
        }
    });
}
