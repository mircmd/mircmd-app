use crate::plugins::manifest::{PluginManifest, PluginTarget, PluginType};
use anyhow::{Context, Result};
use serde::Serialize;
use std::collections::HashMap;
use std::fs::DirEntry;
use std::path::Path;
use std::sync::Arc;
use tracing::error;
use wasmtime::{
    Config, Engine,
    component::{Component, Linker},
};
use wasmtime_wasi::{ResourceTable, WasiCtx, WasiCtxView, WasiView};

pub struct PluginState {
    pub ctx: WasiCtx,
    pub table: ResourceTable,
}

impl WasiView for PluginState {
    fn ctx(&mut self) -> WasiCtxView<'_> {
        WasiCtxView {
            ctx: &mut self.ctx,
            table: &mut self.table,
        }
    }
}

#[derive(Clone, Serialize)]
pub struct Plugin {
    pub manifest: PluginManifest,

    #[serde(skip)]
    pub component: Component,

    #[serde(skip)]
    pub linker: Arc<Linker<PluginState>>,

    #[serde(skip)]
    pub engine: Engine,
}

#[derive(Clone, Serialize)]
pub struct PluginInfo {
    pub path: String,
    pub manifest: PluginManifest,
}

#[derive(Clone, Serialize)]
pub struct PluginManager {
    #[serde(skip)]
    engine: Engine,

    #[serde(skip)]
    linker: Arc<Linker<PluginState>>,

    pub core_plugins: HashMap<PluginType, HashMap<String, Plugin>>,
    pub all_plugins: Vec<PluginInfo>,
}

impl PluginManager {
    pub fn new() -> Result<Self> {
        let mut config = Config::new();
        config.wasm_component_model(true);
        let engine = Engine::new(&config)?;

        let mut linker = Linker::new(&engine);
        wasmtime_wasi::p2::add_to_linker_sync(&mut linker)?;

        Ok(Self {
            engine,
            linker: Arc::new(linker),
            core_plugins: HashMap::new(),
            all_plugins: Vec::new(),
        })
    }

    pub fn load_plugins(&mut self, plugins_dir: &Path) -> Result<()> {
        if !plugins_dir.exists() {
            return Err(anyhow::anyhow!("{} directory does not exist", plugins_dir.display()));
        }

        if !plugins_dir.is_dir() {
            return Err(anyhow::anyhow!("{} path is not a directory", plugins_dir.display()));
        }

        for publisher_entry in std::fs::read_dir(plugins_dir)? {
            match publisher_entry {
                Ok(publisher_entry) => {
                    let publisher_name = publisher_entry
                        .path()
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .to_string();

                    match load_publisher_plugins(self, &publisher_name, &publisher_entry) {
                        Ok(_) => continue,
                        Err(e) => {
                            error!("Failed to load publisher `{}`: {}", publisher_name, e);
                        }
                    }
                }
                Err(e) => {
                    error!("Failed to read publisher entry: {}", e);
                }
            }
        }
        Ok(())
    }
}

fn load_publisher_plugins(
    plugin_manager: &mut PluginManager,
    publisher_name: &String,
    publisher_entry: &DirEntry,
) -> Result<()> {
    let publisher_path = publisher_entry.path();
    if !publisher_path.is_dir() {
        return Ok(());
    }

    for plugin_entry in std::fs::read_dir(&publisher_path)? {
        match plugin_entry {
            Ok(plugin_entry) => {
                let plugin_name = plugin_entry
                    .path()
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string();

                match load_plugin(plugin_manager, publisher_name, &plugin_name, &plugin_entry) {
                    Ok(_) => {
                        continue;
                    }
                    Err(e) => {
                        error!("Failed to load plugin `{}:{}`: {}", publisher_name, plugin_name, e);
                    }
                }
            }
            Err(e) => {
                error!("Failed to read plugin entry: {}", e);
            }
        }
    }
    Ok(())
}

fn load_plugin(
    plugin_manager: &mut PluginManager,
    publisher_name: &String,
    plugin_name: &String,
    plugin_entry: &DirEntry,
) -> Result<()> {
    let plugin_path = plugin_entry.path();
    if !plugin_path.is_dir() {
        return Ok(());
    }

    let manifest_path = plugin_path.join("manifest.yaml");
    if !manifest_path.exists() {
        return Err(anyhow::anyhow!("{} file not found", manifest_path.display()));
    }

    let manifest_content = std::fs::read_to_string(&manifest_path)
        .with_context(|| format!("failed to read {}", manifest_path.display()))?;

    let manifest = serde_yaml::from_str::<PluginManifest>(&manifest_content)
        .with_context(|| format!("failed to parse {}", manifest_path.display()))?;

    plugin_manager.all_plugins.push(PluginInfo {
        path: format!("{}/{}", publisher_name, plugin_name),
        manifest: manifest.clone(),
    });

    if manifest.target != PluginTarget::Core {
        return Ok(());
    }

    let wasm_path = plugin_path.join("plugin.wasm");
    if !wasm_path.exists() {
        return Err(anyhow::anyhow!("{} file not found", wasm_path.display()));
    }

    let component = Component::from_file(&plugin_manager.engine, &wasm_path)
        .with_context(|| format!("failed to load {}", wasm_path.display()))?;

    let plugin = Plugin {
        manifest: manifest.clone(),
        component,
        linker: Arc::clone(&plugin_manager.linker),
        engine: plugin_manager.engine.clone(),
    };

    let plugin_id = format!("{}:{}", manifest.metadata.publisher, manifest.metadata.id);

    plugin_manager
        .core_plugins
        .entry(plugin.manifest.r#type)
        .or_default()
        .insert(plugin_id, plugin);
    Ok(())
}
