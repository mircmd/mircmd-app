from pathlib import Path
from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QDoubleSpinBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class NumberInputFloat(Widget):
    type: Literal["number_input_float"]
    min_value: float
    max_value: float
    value: float
    step: float = Field(default=1, gt=0)
    decimals: int = Field(default=2, ge=0, le=16)
    prefix: str = ""
    suffix: str = ""

    def build(self, extension_path: Path, parent: QWidget | None) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(parent=parent)
        # Decimals before range and value, otherwise Qt rounds them to the default 2 decimals.
        widget.setDecimals(self.decimals)
        widget.setRange(self.min_value, self.max_value)
        widget.setSingleStep(self.step)
        widget.setValue(self.value)
        widget.setPrefix(self.prefix)
        widget.setSuffix(self.suffix)
        widget.setEnabled(self.enabled)
        return widget
