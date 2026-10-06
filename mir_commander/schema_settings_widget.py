import json
from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, floor
from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QWidget,
)

from mir_commander.extensions.errors import FileExporterError


@dataclass
class SchemaField:
    widget: QWidget
    value: Callable[[], Any]
    include: QCheckBox | None


def schema_defaults(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        name: config["default"]
        for name, config in schema.get("properties", {}).items()
        if isinstance(config, dict) and "default" in config
    }


class SchemaSettingsWidget(QWidget):
    def __init__(self, schema: dict[str, Any] | None, parent: QWidget | None = None):
        super().__init__(parent)
        self._fields: dict[str, SchemaField] = {}
        self._json_editor: QPlainTextEdit | None = None
        layout = QFormLayout(self)
        if schema is None:
            return
        if (
            any(key in schema for key in ("$ref", "allOf", "anyOf", "oneOf", "if"))
            or "properties" not in schema
            or any(not isinstance(config, dict) for config in schema["properties"].values())
        ):
            self._json_editor = QPlainTextEdit(json.dumps(schema_defaults(schema), ensure_ascii=False, indent=2))
            layout.addRow(schema.get("title", self.tr("Settings (JSON)")), self._json_editor)
            return
        required = schema.get("required", [])
        for name, config in schema["properties"].items():
            self._add_field(layout, name, config, name in required)

    def _add_field(self, layout: QFormLayout, name: str, config: dict[str, Any], required: bool):
        widget, getter = self._create_editor(config)
        include = None
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        if not required:
            include = QCheckBox(self.tr("Use"))
            include.setChecked("default" in config)
            widget.setEnabled(include.isChecked())
            include.toggled.connect(widget.setEnabled)
            row_layout.addWidget(include)
        row_layout.addWidget(widget)
        widget.setToolTip(config.get("description", ""))
        label = config.get("title", name) + (" *" if required else "")
        layout.addRow(label + ":", row)
        self._fields[name] = SchemaField(widget, getter, include)

    def _create_editor(self, config: dict[str, Any]) -> tuple[QWidget, Callable[[], Any]]:
        default = config.get("default")
        if "enum" in config:
            combo = QComboBox()
            for value in config["enum"]:
                label = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
                combo.addItem(label, value)
            if default in config["enum"]:
                combo.setCurrentIndex(config["enum"].index(default))
            return combo, combo.currentData
        if config.get("type") == "boolean":
            check = QCheckBox()
            check.setChecked(default if isinstance(default, bool) else False)
            return check, check.isChecked
        if config.get("type") == "string":
            text = QLineEdit(default if isinstance(default, str) else "")
            return text, text.text
        return self._create_numeric_or_json_editor(config)

    def _create_numeric_or_json_editor(self, config: dict[str, Any]) -> tuple[QWidget, Callable[[], Any]]:
        default = config.get("default")
        minimum, maximum = config.get("minimum", -2147483648), config.get("maximum", 2147483647)
        if "exclusiveMinimum" in config:
            minimum = max(minimum, floor(config["exclusiveMinimum"]) + 1)
        if "exclusiveMaximum" in config:
            maximum = min(maximum, ceil(config["exclusiveMaximum"]) - 1)
        if config.get("type") == "integer" and -2147483648 <= minimum <= maximum <= 2147483647:
            spin = QSpinBox()
            spin.setRange(ceil(minimum), floor(maximum))
            spin.setValue(default if isinstance(default, int) else max(ceil(minimum), 0))
            return spin, spin.value
        if config.get("type") in ("integer", "number"):
            number = QLineEdit(json.dumps(default if default is not None else 0))
            return number, lambda: json.loads(number.text())
        editor = QPlainTextEdit(json.dumps(default, ensure_ascii=False, indent=2) if default is not None else "")
        editor.setMaximumHeight(120)
        return editor, lambda: json.loads(editor.toPlainText())

    def get_settings(self) -> dict[str, Any]:
        try:
            if self._json_editor is not None:
                result = json.loads(self._json_editor.toPlainText())
                if not isinstance(result, dict):
                    raise FileExporterError("Settings must be a JSON object")
                return result
            return {
                name: field.value()
                for name, field in self._fields.items()
                if field.include is None or field.include.isChecked()
            }
        except (ValueError, TypeError) as error:
            raise FileExporterError(f"Invalid settings: {error}") from error
