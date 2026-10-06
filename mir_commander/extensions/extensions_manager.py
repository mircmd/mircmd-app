import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema.exceptions import SchemaError
from pydantic import ValidationError

import mir_commander_file_exporter_host
from mir_commander.builtin_extensions.cartesian_editor.control_panel import CartesianEditorControlPanel
from mir_commander.builtin_extensions.cartesian_editor.program import CartesianEditorProgram
from mir_commander.builtin_extensions.molecular_visualizer.control_panel import MolecularVisualizerControlPanel
from mir_commander.builtin_extensions.molecular_visualizer.program import MolecularVisualizerProgram
from mir_commander.extensions.errors import ExtensionsManagerError
from mir_commander.extensions.export_format import FileExportFormat
from mir_commander.extensions.manifest import ExtensionManifest, ExtensionProtocol, ExtensionType, Metadata
from mir_commander.sdk.base_program import BaseControlPanel, BaseProgram

logger = logging.getLogger(__name__)


@dataclass
class Extension:
    manifest: ExtensionManifest
    enabled: bool


@dataclass
class IconsExtension(Extension):
    path: Path
    icons: dict[str, str]


@dataclass
class FileImporterExtension(Extension):
    wasm_path: Path


@dataclass
class FileExporterExtension(Extension):
    wasm_path: Path
    formats: list[FileExportFormat]


@dataclass
class ProgramExtension(Extension):
    supported_node_types: list[str]
    program_cls: type[BaseProgram]
    control_panel_cls: type[BaseControlPanel] | None


@dataclass
class ExtensionsRegistry:
    icons: dict[str, IconsExtension] = field(default_factory=dict)
    file_importers: dict[str, FileImporterExtension] = field(default_factory=dict)
    file_exporters: dict[str, FileExporterExtension] = field(default_factory=dict)
    programs: dict[str, ProgramExtension] = field(default_factory=dict)


class ExtensionsManager:
    def __init__(self):
        self._extensions_registry = ExtensionsRegistry()

        self._extensions_registry.programs["mircmd:chemistry:cartesian_editor"] = ProgramExtension(
            manifest=ExtensionManifest(
                type=ExtensionType.PROGRAM,
                protocol=ExtensionProtocol.V1,
                metadata=Metadata(
                    id="mircmd:chemistry:cartesian_editor",
                    name="Cartesian Editor",
                    version="1.0.0",
                    publisher="mircmd",
                    description="Powerful editor for manipulating atomic coordinates with precision and ease.",
                ),
            ),
            enabled=True,
            supported_node_types=CartesianEditorProgram.get_supported_node_types(),
            program_cls=CartesianEditorProgram,
            control_panel_cls=CartesianEditorControlPanel,
        )

        self._extensions_registry.programs["mircmd:chemistry:molecular_visualizer"] = ProgramExtension(
            manifest=ExtensionManifest(
                type=ExtensionType.PROGRAM,
                protocol=ExtensionProtocol.V1,
                metadata=Metadata(
                    id="mircmd:chemistry:molecular_visualizer",
                    name="Molecular Visualizer",
                    version="1.0.0",
                    publisher="mircmd",
                    description="Advanced 3D visualization tool for molecular structures with interactive controls and multiple rendering modes.",
                ),
            ),
            enabled=True,
            supported_node_types=MolecularVisualizerProgram.get_supported_node_types(),
            program_cls=MolecularVisualizerProgram,
            control_panel_cls=MolecularVisualizerControlPanel,
        )

    def load_extensions(self, extensions_dir: Path):
        if not extensions_dir.exists():
            raise ExtensionsManagerError(f"Extensions directory does not exist: {extensions_dir}")

        if not extensions_dir.is_dir():
            raise ExtensionsManagerError(f"Extensions directory is not a directory: {extensions_dir}")

        for publisher_entry in extensions_dir.iterdir():
            self.load_publisher_extensions(publisher_entry)

    def load_publisher_extensions(self, publisher_entry: Path):
        if not publisher_entry.is_dir():
            return

        for extension_entry in publisher_entry.iterdir():
            try:
                self.load_extension(extension_entry)
            except ExtensionsManagerError as e:
                logger.error("Failed to load extension: %s", e)

    def load_extension(self, extension_entry: Path):
        if not extension_entry.is_dir():
            return

        manifest_path = extension_entry / "manifest.yaml"
        if not manifest_path.exists():
            raise ExtensionsManagerError(f"Manifest file not found: {manifest_path}")

        manifest_content = manifest_path.read_text()
        manifest = yaml.safe_load(manifest_content)
        try:
            extension_manifest = ExtensionManifest(**manifest)
        except ValidationError as e:
            raise ExtensionsManagerError(f"Invalid manifest: {e}")

        if extension_manifest.type == ExtensionType.ICONS:
            self._load_icons_extension(extension_manifest, extension_entry)
        elif extension_manifest.type == ExtensionType.FILE_IMPORTER:
            self._load_file_importer_extension(extension_manifest, extension_entry)
        elif extension_manifest.type == ExtensionType.FILE_EXPORTER:
            self._load_file_exporter_extension(extension_manifest, extension_entry)

    def _load_icons_extension(self, manifest: ExtensionManifest, entry: Path):
        json_path = entry / "extension.json"
        if not json_path.exists():
            raise ExtensionsManagerError(f"JSON file not found: {json_path}")

        self._extensions_registry.icons[manifest.metadata.id] = IconsExtension(
            manifest=manifest, enabled=True, path=entry, icons=json.loads(json_path.read_text())
        )

    def _load_file_importer_extension(self, manifest: ExtensionManifest, entry: Path):
        wasm_path = entry / "extension.wasm"
        if not wasm_path.exists():
            raise ExtensionsManagerError(f"WASM file not found: {wasm_path}")

        self._extensions_registry.file_importers[manifest.metadata.id] = FileImporterExtension(
            manifest=manifest,
            enabled=True,
            wasm_path=wasm_path,
        )

    def _load_file_exporter_extension(self, manifest: ExtensionManifest, entry: Path):
        wasm_path = entry / "extension.wasm"
        if not wasm_path.is_file():
            raise ExtensionsManagerError(f"WASM file not found: {wasm_path}")
        try:
            formats = [
                FileExportFormat(
                    id=fmt.id,
                    name=fmt.name,
                    extensions=fmt.extensions,
                    supported_node_types=fmt.supported_node_types,
                    settings_schema=json.loads(fmt.settings_schema) if fmt.settings_schema is not None else None,
                )
                for fmt in mir_commander_file_exporter_host.formats(str(wasm_path))
            ]
            if not formats or len({fmt.id for fmt in formats}) != len(formats):
                raise ValueError("Exporter must provide formats with unique IDs")
        except (ImportError, RuntimeError, AttributeError, ValueError, SchemaError) as error:
            raise ExtensionsManagerError(f"Invalid file exporter {manifest.metadata.id}: {error}") from error
        self._extensions_registry.file_exporters[manifest.metadata.id] = FileExporterExtension(
            manifest=manifest, enabled=True, wasm_path=wasm_path, formats=formats
        )

    def get_icons(self) -> Iterable[IconsExtension]:
        return self._extensions_registry.icons.values()

    def get_file_importers(self) -> Iterable[FileImporterExtension]:
        return self._extensions_registry.file_importers.values()

    def get_file_exporters(self) -> Iterable[FileExporterExtension]:
        return self._extensions_registry.file_exporters.values()

    def get_programs(self) -> Iterable[ProgramExtension]:
        return self._extensions_registry.programs.values()
