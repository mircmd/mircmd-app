from pathlib import Path
from typing import Literal

from pydantic import Field
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ORIENTATION, Orientation, Widget


class Slider(Widget):
    type: Literal["slider"]
    orientation: Orientation
    min_value: int
    max_value: int
    value: int
    step: int = Field(default=1)

    def build(self, extension_path: Path, parent: QWidget | None) -> QSlider:
        widget = QSlider(ORIENTATION.get(self.orientation, Qt.Orientation.Horizontal), parent=parent)
        widget.setRange(self.min_value, self.max_value)
        widget.setValue(self.value)
        widget.setSingleStep(self.step)
        widget.setEnabled(self.enabled)
        return widget
