mod bindings;

use anyhow::Result;
use bindings::mircmd::file_importer::types::{Node, Tree};
use bindings::FileImporterExtension;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::path::{Path, PathBuf};
use std::time::Instant;
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
pub struct ImportNode {
    #[pyo3(get)]
    pub id: u32,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub type_id: String,
    #[pyo3(get)]
    pub data: Py<PyBytes>,
    #[pyo3(get)]
    pub children: Vec<u32>,
}

#[pyclass]
pub struct ImportTree {
    #[pyo3(get)]
    pub root: u32,
    #[pyo3(get)]
    pub nodes: Vec<Py<ImportNode>>,
    #[pyo3(get)]
    pub seconds: f64,
}

struct Ready {
    store: Store<ExtensionState>,
    binding: FileImporterExtension,
    file_path: PathBuf,
}

#[pyfunction]
fn load(py: Python<'_>, wasm_path: &str, file_path: &str) -> PyResult<ImportTree> {
    let mut ready = prepare(wasm_path, file_path)?;
    let started = Instant::now();
    let tree = call_load(&mut ready.store, &ready.binding, &ready.file_path)?;
    let nodes = import_nodes(py, tree.nodes)?;
    Ok(ImportTree {
        root: tree.root,
        nodes,
        seconds: started.elapsed().as_secs_f64(),
    })
}

#[pymodule]
fn mir_commander_file_importer_host(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(load, module)?)?;
    module.add_class::<ImportNode>()?;
    module.add_class::<ImportTree>()?;
    Ok(())
}

fn prepare(wasm_path: &str, file_path: &str) -> Result<Ready> {
    let file_path = PathBuf::from(file_path);
    let engine = engine()?;
    let component = Component::from_file(&engine, wasm_path)?;
    let linker = linker(&engine)?;
    let mut store = store(&engine, &file_path)?;
    let binding = FileImporterExtension::instantiate(&mut store, &component, &linker)?;
    Ok(Ready {
        store,
        binding,
        file_path,
    })
}

fn call_load(
    store: &mut Store<ExtensionState>,
    binding: &FileImporterExtension,
    file_path: &Path,
) -> Result<Tree> {
    let guest_file = file_path.to_string_lossy().into_owned();
    binding
        .mircmd_file_importer_importer()
        .call_load(store, &guest_file)?
        .map_err(anyhow::Error::msg)
}

fn import_nodes(py: Python<'_>, nodes: Vec<Node>) -> PyResult<Vec<Py<ImportNode>>> {
    nodes.into_iter().map(|node| import_node(py, node)).collect()
}

fn import_node(py: Python<'_>, node: Node) -> PyResult<Py<ImportNode>> {
    let data = PyBytes::new(py, &node.data).unbind();
    Py::new(
        py,
        ImportNode {
            id: node.id,
            name: node.name,
            type_id: node.type_id,
            data,
            children: node.children,
        },
    )
}

fn engine() -> Result<Engine> {
    let mut config = Config::new();
    config.wasm_component_model(true);
    Ok(Engine::new(&config)?)
}

fn linker(engine: &Engine) -> Result<Linker<ExtensionState>> {
    let mut linker = Linker::new(engine);
    wasmtime_wasi::p2::add_to_linker_sync(&mut linker)?;
    Ok(linker)
}

fn store(engine: &Engine, file_path: &Path) -> Result<Store<ExtensionState>> {
    let dir = file_path.parent().unwrap_or(Path::new("."));
    let guest_dir = dir.to_string_lossy().into_owned();
    let mut builder = WasiCtxBuilder::new();
    builder.inherit_stdio();
    builder.preopened_dir(dir, &guest_dir, FsPerms::ReadOnly)?;
    Ok(Store::new(
        engine,
        ExtensionState {
            ctx: builder.build(),
            table: ResourceTable::new(),
        },
    ))
}
