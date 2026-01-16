use wasmtime::component::bindgen;

bindgen!({
    path: "wit",
    world: "file-importer",
});
