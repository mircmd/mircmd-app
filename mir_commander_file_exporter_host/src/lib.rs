mod bindings;

use anyhow::{Context, Result};
use bindings::FileExporterExtension;
use pyo3::prelude::*;
use std::path::Path;
use wasmtime::component::{Component, Linker};
use wasmtime::{Config, Engine, Store};
use wasmtime_wasi::{FsPerms, ResourceTable, WasiCtx, WasiCtxBuilder, WasiCtxView, WasiView};

struct ExtensionState {
    ctx: WasiCtx,
    table: ResourceTable,
}

impl WasiView for ExtensionState {
    fn ctx(&mut self) -> WasiCtxView<'_> {
        WasiCtxView {
            ctx: &mut self.ctx,
            table: &mut self.table,
        }
    }
}

#[pyclass]
struct ExportFormat {
    #[pyo3(get)]
    id: String,
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    extensions: Vec<String>,
    #[pyo3(get)]
    supported_node_types: Vec<String>,
    #[pyo3(get)]
    settings_schema: Option<String>,
}

#[pyfunction]
fn formats(wasm_path: &str) -> PyResult<Vec<ExportFormat>> {
    let (mut store, binding) = prepare(wasm_path, None)?;
    let formats = binding
        .mircmd_file_exporter_exporter()
        .call_formats(&mut store)
        .map_err(anyhow::Error::from)?
        .map_err(anyhow::Error::msg)?;
    Ok(formats
        .into_iter()
        .map(|format| ExportFormat {
            id: format.id,
            name: format.name,
            extensions: format.extensions,
            supported_node_types: format.supported_node_types,
            settings_schema: format.settings_schema,
        })
        .collect())
}

#[pyfunction]
fn dump(
    wasm_path: &str,
    data: &[u8],
    format_id: &str,
    settings: &str,
    file_path: &str,
) -> PyResult<()> {
    let path = Path::new(file_path);
    let parent = path
        .parent()
        .filter(|dir| !dir.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let parent = parent
        .canonicalize()
        .context("Cannot access the export directory")?;
    let name = path
        .file_name()
        .context("Export path must include a file name")?;
    let absolute_path = parent.join(name);
    let guest_path = absolute_path
        .to_str()
        .context("Export path must be valid UTF-8")?;
    let (mut store, binding) = prepare(wasm_path, Some(&parent))?;
    binding
        .mircmd_file_exporter_exporter()
        .call_dump(&mut store, data, format_id, settings, guest_path)
        .map_err(anyhow::Error::from)?
        .map_err(anyhow::Error::msg)?;
    Ok(())
}

fn prepare(
    wasm_path: &str,
    directory: Option<&Path>,
) -> Result<(Store<ExtensionState>, FileExporterExtension)> {
    let mut config = Config::new();
    config.wasm_component_model(true);
    let engine = Engine::new(&config)?;
    let component = Component::from_file(&engine, wasm_path)?;
    let mut linker = Linker::new(&engine);
    wasmtime_wasi::p2::add_to_linker_sync(&mut linker)?;
    let mut builder = WasiCtxBuilder::new();
    if let Some(directory) = directory {
        let guest_dir = directory
            .to_str()
            .context("Export directory must be valid UTF-8")?;
        builder.preopened_dir(directory, guest_dir, FsPerms::ReadWrite)?;
    }
    let state = ExtensionState {
        ctx: builder.build(),
        table: ResourceTable::new(),
    };
    let mut store = Store::new(&engine, state);
    let binding = FileExporterExtension::instantiate(&mut store, &component, &linker)?;
    Ok((store, binding))
}

#[pymodule]
fn mir_commander_file_exporter_host(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(formats, module)?)?;
    module.add_function(wrap_pyfunction!(dump, module)?)?;
    module.add_class::<ExportFormat>()?;
    Ok(())
}
