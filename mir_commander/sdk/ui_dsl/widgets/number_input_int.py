from pathlib import Path
from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QSpinBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class NumberInputInt(Widget):
    type: Literal["number_input_int"]
    min_value: int
    max_value: int
    value: int
    step: int = Field(default=1, gt=0)
    prefix: str = ""
    suffix: str = ""

    def build(self, extension_path: Path, parent: QWidget | None) -> QSpinBox:
        widget = QSpinBox(parent=parent)
        widget.setRange(self.min_value, self.max_value)
        widget.setSingleStep(self.step)
        widget.setValue(self.value)
        widget.setPrefix(self.prefix)
        widget.setSuffix(self.suffix)
        widget.setEnabled(self.enabled)
        return widget
