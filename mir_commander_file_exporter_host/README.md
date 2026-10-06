# File exporter host

PyO3 host for WASI Preview 2 export components. The WIT contract is packaged in
`wit/file-exporter.wit`, so the host builds without the chemistry extensions
repository.

The application installs this package through its local dependency in
`pyproject.toml` (`uv sync`).

- `formats(wasm_path)` returns typed format descriptors without granting
  filesystem access.
- `dump(wasm_path, data, format_id, settings, file_path)` instantiates the
  component, grants read/write access to the output parent directory, and calls
  its export function. `settings` is a JSON object encoded as a string; the
  guest receives an absolute UTF-8 file path. WASM traps and guest errors are
  raised as Python errors.

The application checks each format's supported object types and validates
settings against its JSON Schema before invoking the host. The dialog renders
strings, integers, numbers, booleans and enums as native controls. Optional
settings can be omitted; schema defaults prefill controls. Arrays and nested
objects use JSON editors, as do composed root schemas. The full schema is still
used for validation. Each extension/format pair keeps its own form values while
the dialog is open.

To run tests including the actual chemistry component:

```sh
cd ../mircmd-extensions/mircmd-chemistry-extensions/files-exporter
make build test
cd ../../../mircmd-app
uv sync
QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_file_exporter.py
```

Integration tests use the sibling checkout's release component by default.
Set `MIRCMD_XYZ_EXPORTER_WASM` to select a different build. When no component is
available, integration tests are skipped and the application tests still run.
