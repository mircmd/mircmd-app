from enum import Enum
from pathlib import Path
from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class CheckState(Enum):
    Unchecked = "unchecked"
    PartiallyChecked = "partially_checked"
    Checked = "checked"


class Checkbox(Widget):
    type: Literal["checkbox"]
    state: CheckState

    def build(self, extension_path: Path, parent: QWidget | None) -> QCheckBox:
        widget = QCheckBox(parent=parent)
        if self.state == CheckState.Unchecked:
            widget.setCheckState(Qt.CheckState.Unchecked)
        elif self.state == CheckState.PartiallyChecked:
            widget.setCheckState(Qt.CheckState.PartiallyChecked)
        elif self.state == CheckState.Checked:
            widget.setCheckState(Qt.CheckState.Checked)
        widget.setEnabled(self.enabled)
        return widget
