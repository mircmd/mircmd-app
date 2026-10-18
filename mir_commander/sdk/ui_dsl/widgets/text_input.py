from pathlib import Path
from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QLineEdit, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class TextInput(Widget):
    type: Literal["text_input"]
    text: str = Field(..., min_length=0)
    placeholder: str = ""

    def build(self, extension_path: Path, parent: QWidget | None) -> QLineEdit:
        widget = QLineEdit(self.text, parent=parent)
        widget.setPlaceholderText(self.placeholder)
        widget.setEnabled(self.enabled)
        return widget
