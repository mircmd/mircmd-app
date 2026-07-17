use crate::plugins::bindings::FileImporter;
use crate::plugins::manager::{Plugin, PluginState};
use crate::project::{ProjectNode, RawProjectNode};
use anyhow::Result;
use std::path::Path;
use wasmtime::Store;
use wasmtime_wasi::{ResourceTable, WasiCtxBuilder};

pub struct FileImporterPlugin;

impl FileImporterPlugin {
    pub fn load(plugin: &Plugin, file_path: &Path) -> Result<ProjectNode> {
        let dir = file_path.parent().unwrap_or(Path::new("."));

        let mut builder = WasiCtxBuilder::new();
        builder.inherit_stdio();

        // Allow reading the directory where the file is located
        let preopen_path = ".";
        builder.preopened_dir(
            dir,
            preopen_path,
            wasmtime_wasi::DirPerms::READ,
            wasmtime_wasi::FilePerms::READ,
        )?;

        let ctx = builder.build();
        let table = ResourceTable::new();
        let mut store = Store::new(&plugin.engine, PluginState { ctx, table });

        let binding = FileImporter::instantiate(&mut store, &plugin.component, &plugin.linker)?;

        // Calculate relative path for the plugin
        let filename = file_path.file_name().unwrap_or_default().to_string_lossy().to_string();

        let result = binding.call_load(&mut store, &filename);

        match result {
            Ok(Ok(bytes)) => {
                let raw_node = serde_json::from_slice::<RawProjectNode>(&bytes)?;
                Ok(ProjectNode::from(raw_node))
            }
            Ok(Err(msg)) => Err(anyhow::anyhow!("{}", msg)),
            Err(e) => Err(anyhow::anyhow!("{}", e)),
        }
    }
}
