use crate::config::Config;
use crate::consts::Dirs;
use crate::file_manager::FileManager;
use crate::plugins::manager::PluginManager;
use crate::plugins::manifest::PluginType;
use crate::project::Project;
use anyhow::Result;
use std::path::Path;
use std::sync::Mutex;
use tauri::Emitter;
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
use tracing::error;
use uuid::Uuid;

pub struct AppState {
    pub config: Config,
    pub project: Project,
    pub plugin_manager: PluginManager,
    pub file_manager: FileManager,
    pub startup_messages: Vec<String>,
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
            startup_messages: vec![format!("Mir Commander v{}", env!("CARGO_PKG_VERSION"))],
        }
    }

    pub fn import_file(&mut self, file_path: &Path, node_id: Option<String>) -> Result<(), String> {
        let node = match node_id {
            Some(id) => {
                let uuid = Uuid::parse_str(&id).unwrap();
                self.project
                    .root_node
                    .find_by_id_mut(&uuid)
                    .ok_or_else(|| format!("Node with id {} not found", id))?
            }
            None => &mut self.project.root_node,
        };

        match self.file_manager.import_file(file_path) {
            Ok(imported_node) => {
                node.add_child(imported_node);
                Ok(())
            }
            Err(e) => {
                let error = format!("Failed to import file {}: {}", file_path.display(), e);
                error!("{}", error);
                Err(error)
            }
        }
    }
}

pub fn import_files(app_handle: tauri::AppHandle, node_id: Option<String>) {
    app_handle.dialog().file().pick_files(move |file_paths| {
        if let Some(files) = file_paths {
            let state_handle = app_handle.state::<Mutex<AppState>>();
            let mut state = state_handle.lock().unwrap();
            for file in files {
                match state.import_file(file.as_path().unwrap(), node_id.clone()) {
                    Ok(_) => {
                        let _ = app_handle.emit("explorer_refresh", true);
                    }
                    Err(e) => {
                        let _ = app_handle.emit("console_output_append_line", e);
                    }
                }
            }
        }
    });
}
