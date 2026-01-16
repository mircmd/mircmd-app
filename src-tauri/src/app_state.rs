use crate::config::Config;
use crate::consts::Dirs;
use crate::file_manager::FileManager;
use crate::plugins::manager::PluginManager;
use crate::plugins::manifest::PluginType;
use crate::project::Project;
use anyhow::Result;
use std::path::Path;
use tracing::error;

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

    pub fn import_file(&mut self, file_path: &Path) -> Result<(), String> {
        match self.file_manager.import_file(file_path) {
            Ok(node) => {
                self.project.root_node.add_child(node);
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
