import json
import os
import shutil
import struct
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

import mir_commander_file_exporter_host
from mir_commander.docks.project_dock.config import TreeConfig
from mir_commander.docks.project_dock.tree_view import TreeView
from mir_commander.export_item_dialog import ExportFileDialog
from mir_commander.extensions.errors import ExtensionsManagerError, FileExporterError
from mir_commander.extensions.export_format import FileExportFormat
from mir_commander.extensions.extensions_manager import ExtensionsManager, FileExporterExtension
from mir_commander.extensions.file_exporter import FileExporter
from mir_commander.extensions.manifest import ExtensionManifest
from mir_commander.item import Item
from mir_commander.schema_settings_widget import SchemaSettingsWidget

NODE_TYPE = "mircmd:chemistry:atomic_coordinates"
EXTENSIONS_REPO = Path(__file__).resolve().parents[2] / "mircmd-extensions/mircmd-chemistry-extensions"
WASM = Path(
    os.environ.get(
        "MIRCMD_XYZ_EXPORTER_WASM",
        EXTENSIONS_REPO / "files-exporter/target/wasm32-wasip2/release/files_exporter_extension.wasm",
    )
)
WIT = EXTENSIONS_REPO / "files-exporter/wit/file-exporter.wit"
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "default": ""},
        "precision": {"type": "integer", "minimum": 0, "maximum": 16, "default": 14},
    },
}


def export_format(format_id="xyz", node_type=NODE_TYPE, schema=SCHEMA):
    return FileExportFormat(
        id=format_id,
        name=format_id.upper(),
        extensions=[format_id],
        supported_node_types=[node_type],
        settings_schema=schema,
    )


def extension(extension_id="test", formats=None):
    manifest = ExtensionManifest(
        type="file_exporter",
        protocol="v1",
        metadata={
            "id": extension_id,
            "name": extension_id,
            "version": "1.0.0",
            "publisher": "mircmd",
            "description": "Test",
        },
    )
    return FileExporterExtension(manifest=manifest, enabled=True, wasm_path=WASM, formats=formats or [export_format()])


def exporter_for(*extensions):
    manager = SimpleNamespace(get_file_exporters=lambda: extensions)
    return FileExporter(manager)


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def item(qapp, monkeypatch):
    monkeypatch.setattr(qapp, "icons", SimpleNamespace(get_icon_path=lambda _: None), raising=False)
    monkeypatch.setattr(qapp, "program", SimpleNamespace(get_supported_programs=lambda _: []), raising=False)
    # Postcard: Vec<i32> (zigzag), then three Vec<f64> in importer field order.
    data = (
        bytes([1, 16, 1])
        + struct.pack("<d", 1.25)
        + bytes([1])
        + struct.pack("<d", -2.5)
        + bytes([1])
        + struct.pack("<d", 0.0)
    )
    return Item("Coordinates", NODE_TYPE, data)


def test_filters_by_each_format_and_enabled_state():
    first = extension(formats=[export_format(), export_format("mol", "mircmd:chemistry:molecule")])
    second = extension("disabled")
    second.enabled = False
    exporter = exporter_for(first, second)
    assert exporter.get_exporters(NODE_TYPE) == [first]
    assert [fmt.id for fmt in exporter.get_formats(first, NODE_TYPE)] == ["xyz"]
    with pytest.raises(FileExporterError):
        exporter.get_format(NODE_TYPE, "test", "mol")
    with pytest.raises(FileExporterError):
        exporter.get_format(NODE_TYPE, "disabled", "xyz")


def test_validates_settings_before_calling_wasm(item, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(mir_commander_file_exporter_host, "dump", lambda *args: calls.append(args))
    exporter = exporter_for(extension())
    with pytest.raises(FileExporterError, match="precision"):
        exporter.export_file(item, "test", "xyz", tmp_path / "out.xyz", {"precision": 17})
    assert not calls
    exporter.export_file(item, "test", "xyz", tmp_path / "out.xyz", {"title": "Вода"})
    assert calls[0][1] == item.get_data()
    assert calls[0][2] == "xyz"
    assert json.loads(calls[0][3]) == {"title": "Вода"}
    assert calls[0][4] == str(tmp_path / "out.xyz")


def test_wraps_wasm_errors(item, tmp_path, monkeypatch):
    def fail(*args):
        raise RuntimeError("Cannot write output")

    monkeypatch.setattr(mir_commander_file_exporter_host, "dump", fail)
    with pytest.raises(FileExporterError, match="Cannot write"):
        exporter_for(extension()).export_file(item, "test", "xyz", tmp_path / "out.xyz", {})


def test_schema_widgets_preserve_types_and_optional_fields(qapp):
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "default": "Water"},
            "number": {"type": "number", "default": 1.25},
            "enabled": {"type": "boolean", "default": False},
            "mode": {"type": "integer", "enum": [1, 2], "default": 2},
            "optional": {"type": "string"},
            "array": {"type": "array", "default": [1, 2]},
        },
    }
    widget = SchemaSettingsWidget(schema)
    assert widget.get_settings() == {"name": "Water", "number": 1.25, "enabled": False, "mode": 2, "array": [1, 2]}
    widget._fields["optional"].include.setChecked(True)
    widget._fields["optional"].widget.setText("value")
    assert widget.get_settings()["optional"] == "value"
    widget._fields["number"].widget.setText("oops")
    with pytest.raises(FileExporterError):
        widget.get_settings()


def test_complex_schema_uses_json_editor(qapp):
    widget = SchemaSettingsWidget({"type": "object", "allOf": [{"required": ["nested"]}]})
    widget._json_editor.setPlainText('{"nested":{"value":1}}')
    assert widget.get_settings() == {"nested": {"value": 1}}
    widget._json_editor.setPlainText("[]")
    with pytest.raises(FileExporterError):
        widget.get_settings()


def test_dialog_filters_formats_and_preserves_settings(item):
    exporter = exporter_for(
        extension(formats=[export_format(), export_format("abc"), export_format("mol", "mircmd:chemistry:molecule")]),
        extension("second"),
    )
    dialog = ExportFileDialog(item, exporter)
    assert dialog._extension_combo_box.count() == 2
    dialog._extension_combo_box.setCurrentIndex(dialog._extension_combo_box.findText("test"))
    assert dialog._format_combo_box.count() == 2
    dialog._format_combo_box.setCurrentIndex(dialog._format_combo_box.findText("XYZ"))
    dialog._current_settings._fields["title"].widget.setText("Changed")
    dialog._extension_combo_box.setCurrentIndex(dialog._extension_combo_box.findText("second"))
    assert dialog.get_params()[3]["title"] == ""
    dialog._extension_combo_box.setCurrentIndex(dialog._extension_combo_box.findText("test"))
    dialog._format_combo_box.setCurrentIndex(dialog._format_combo_box.findText("XYZ"))
    assert dialog.get_params()[3]["title"] == "Changed"
    assert dialog.get_params()[0].suffix == ".xyz"


def test_dialog_handles_no_exporters(item):
    dialog = ExportFileDialog(item, exporter_for())
    assert not dialog._export_button.isEnabled()
    assert dialog._error_label.text()


def test_dialog_keeps_open_on_failure_and_checks_overwrite(item, tmp_path, monkeypatch):
    calls = []
    exporter = exporter_for(extension())
    monkeypatch.setattr(exporter, "export_file", lambda *args: calls.append(args))
    dialog = ExportFileDialog(item, exporter)
    target = tmp_path / "existing.xyz"
    target.write_text("original")
    dialog._file_name_editbox.setText(str(target))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    dialog.accept()
    assert not calls
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)

    def fail(*args):
        raise FileExporterError("Failed to export")

    monkeypatch.setattr(exporter, "export_file", fail)
    dialog.accept()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog._error_label.text() == "Failed to export"
    assert target.read_text() == "original"


def test_context_menu_only_shows_export_for_supported_objects(item, qapp, monkeypatch):
    monkeypatch.setattr(qapp, "file_exporter", exporter_for(extension()), raising=False)
    monkeypatch.setattr(qapp, "project_window", SimpleNamespace(export_file=lambda _: None), raising=False)
    tree = TreeView(QStandardItemModel(), TreeConfig())
    menu = tree._build_context_menu(item)
    assert "Export..." in [action.text() for action in menu.actions()]
    unsupported = Item("Molecule", "mircmd:chemistry:molecule", b"")
    menu = tree._build_context_menu(unsupported)
    assert "Export..." not in [action.text() for action in menu.actions()]


def test_loader_rejects_missing_wasm_and_duplicate_formats(tmp_path, monkeypatch):
    manifest = extension().manifest
    manager = ExtensionsManager()
    with pytest.raises(ExtensionsManagerError, match="WASM file not found"):
        manager._load_file_exporter_extension(manifest, tmp_path)
    (tmp_path / "extension.wasm").touch()
    fmt = SimpleNamespace(
        id="xyz", name="XYZ", extensions=["xyz"], supported_node_types=[NODE_TYPE], settings_schema=None
    )
    monkeypatch.setattr(mir_commander_file_exporter_host, "formats", lambda _: [fmt, fmt])
    with pytest.raises(ExtensionsManagerError, match="unique IDs"):
        manager._load_file_exporter_extension(manifest, tmp_path)


@pytest.mark.skipif(not WIT.is_file(), reason="Chemistry extensions checkout is required")
def test_host_and_guest_wit_contracts_match():
    host_wit = Path(__file__).resolve().parents[1] / "mir_commander_file_exporter_host/wit/file-exporter.wit"
    assert host_wit.read_text() == WIT.read_text()


@pytest.mark.skipif(not WASM.is_file(), reason="Build the XYZ WASM component before integration tests")
def test_real_wasm_loading_and_dialog_export(item, tmp_path):
    entry = tmp_path / "extension"
    entry.mkdir()
    shutil.copy(WASM, entry / "extension.wasm")
    shutil.copy(EXTENSIONS_REPO / "files-exporter/manifest.yaml", entry / "manifest.yaml")
    manager = ExtensionsManager()
    manager.load_extension(entry)
    exporter = FileExporter(manager)
    assert [ext.manifest.metadata.id for ext in exporter.get_exporters(NODE_TYPE)] == ["chemistry-files-exporter"]
    dialog = ExportFileDialog(item, exporter)
    dialog._current_settings._fields["title"].widget.setText("Координаты")
    dialog._current_settings._fields["precision"].widget.setValue(3)
    target = tmp_path / "координаты.xyz"
    dialog._file_name_editbox.setText(str(target))
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert target.read_text().splitlines()[:2] == ["1", "Координаты"]
    assert target.read_text().splitlines()[2].split() == ["O", "1.250", "-2.500", "0.000"]


@pytest.mark.skipif(not WASM.is_file(), reason="Build the XYZ WASM component before integration tests")
def test_real_wasm_rejects_invalid_data_without_overwriting(item, tmp_path):
    target = tmp_path / "original.xyz"
    target.write_text("original")
    for data, fmt, settings in [
        (b"broken", "xyz", "{}"),
        (item.get_data(), "unex", "{}"),
        (item.get_data(), "xyz", '{"precision":17}'),
    ]:
        with pytest.raises(RuntimeError):
            mir_commander_file_exporter_host.dump(str(WASM), data, fmt, settings, str(target))
        assert target.read_text() == "original"
    with pytest.raises(RuntimeError):
        mir_commander_file_exporter_host.dump(
            str(WASM), item.get_data(), "xyz", "{}", str(tmp_path / "missing/out.xyz")
        )


@pytest.mark.skipif(not WASM.is_file(), reason="Build the XYZ WASM component before integration tests")
def test_wasm_xyz_round_trip(tmp_path):
    import mir_commander_file_importer_host

    importer_wasm = EXTENSIONS_REPO / "files-importer/target/wasm32-wasip2/release/files_importer_extension.wasm"
    if not importer_wasm.is_file():
        pytest.skip("Build the file importer component before the round-trip test")
    source = tmp_path / "source.xyz"
    source.write_text("3\nWater\nO 0 0 0\nH 0.7586 0 0.5043\nH -0.7586 0 0.5043\n")
    tree = mir_commander_file_importer_host.load(str(importer_wasm), str(source))
    original = next(node for node in tree.nodes if node.type_id == NODE_TYPE)
    target = tmp_path / "exported.xyz"
    mir_commander_file_exporter_host.dump(str(WASM), original.data, "xyz", '{"title":"Water"}', str(target))
    restored = mir_commander_file_importer_host.load(str(importer_wasm), str(target))
    result = next(node for node in restored.nodes if node.type_id == NODE_TYPE)
    assert result.data == original.data


def test_switching_formats_with_empty_path(item):
    dialog = ExportFileDialog(item, exporter_for(extension(formats=[export_format(), export_format("abc")])))
    dialog._file_name_editbox.clear()
    dialog._format_combo_box.setCurrentIndex(1)
    assert dialog._file_name_editbox.text() == ""
    dialog.accept()
    assert dialog._error_label.text() == "Choose an output file"


def test_unresolvable_schema_is_reported():
    fmt = export_format(schema={"type": "object", "$ref": "#/$defs/missing"})
    with pytest.raises(FileExporterError, match="Cannot resolve settings schema"):
        exporter_for(extension()).validate_settings(fmt, {})
