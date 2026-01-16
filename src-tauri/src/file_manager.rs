use crate::plugins::file_importer::FileImporterPlugin;
use crate::plugins::manager::Plugin;
use crate::project::ProjectNode;
use anyhow::Result;
use std::collections::HashMap;
use std::path::Path;

#[derive(Clone)]
pub struct FileManager {
    plugins_registry: HashMap<String, Plugin>,
}

impl FileManager {
    pub fn new(plugins_registry: HashMap<String, Plugin>) -> Self {
        Self { plugins_registry }
    }

    pub fn import_file(&self, file_path: &Path) -> Result<ProjectNode> {
        for (_name, plugin) in &self.plugins_registry {
            match FileImporterPlugin::load(plugin, file_path) {
                Ok(node) => return Ok(node),
                Err(e) => return Err(e),
            }
        }

        Err(anyhow::anyhow!("No importers can handle this file"))
    }
}
