import json
from pathlib import Path
from typing import Any

from jsonschema.exceptions import ValidationError
from jsonschema.validators import validator_for
from referencing.exceptions import Unresolvable

from mir_commander.extensions.errors import FileExporterError
from mir_commander.extensions.export_format import FileExportFormat
from mir_commander.extensions.extensions_manager import ExtensionsManager, FileExporterExtension
from mir_commander.item import Item


class FileExporter:
    def __init__(self, extensions_manager: ExtensionsManager):
        self._extensions_manager = extensions_manager

    def get_exporters(self, node_type: str) -> list[FileExporterExtension]:
        return [
            extension
            for extension in self._extensions_manager.get_file_exporters()
            if extension.enabled and self.get_formats(extension, node_type)
        ]

    def get_formats(self, extension: FileExporterExtension, node_type: str) -> list[FileExportFormat]:
        return [fmt for fmt in extension.formats if node_type in fmt.supported_node_types]

    def get_format(
        self, node_type: str, extension_id: str, format_id: str
    ) -> tuple[FileExporterExtension, FileExportFormat]:
        for extension in self.get_exporters(node_type):
            if extension.manifest.metadata.id == extension_id:
                for fmt in self.get_formats(extension, node_type):
                    if fmt.id == format_id:
                        return extension, fmt
        raise FileExporterError(f"Export format {extension_id}/{format_id} is not available for {node_type}")

    def validate_settings(self, fmt: FileExportFormat, params: dict[str, Any]):
        if fmt.settings_schema is None:
            if params:
                raise FileExporterError("This format has no settings")
            return
        try:
            validator_for(fmt.settings_schema)(fmt.settings_schema).validate(params)
        except ValidationError as error:
            field = ".".join(str(part) for part in error.absolute_path)
            raise FileExporterError(f"{field + ': ' if field else ''}{error.message}") from error
        except Unresolvable as error:
            raise FileExporterError(f"Cannot resolve settings schema: {error}") from error

    def export_file(self, item: Item, extension_id: str, format_id: str, file_path: Path, params: dict[str, Any]):
        extension, fmt = self.get_format(item.get_type(), extension_id, format_id)
        self.validate_settings(fmt, params)
        try:
            import mir_commander_file_exporter_host

            settings = json.dumps(params, ensure_ascii=False, allow_nan=False)
            mir_commander_file_exporter_host.dump(
                str(extension.wasm_path), item.get_data(), fmt.id, settings, str(file_path.absolute())
            )
        except (ImportError, RuntimeError, AttributeError, OSError, ValueError) as error:
            raise FileExporterError(str(error)) from error
