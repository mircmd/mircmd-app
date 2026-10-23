from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QDoubleSpinBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ValueWidget


class NumberInputFloat(ValueWidget[QDoubleSpinBox]):
    type: Literal["number_input_float"]
    min_value: float
    max_value: float
    value: float
    step: float = Field(default=1, gt=0)
    decimals: int = Field(default=2, ge=0, le=16)
    prefix: str = ""
    suffix: str = ""

    on_change: str = ""

    def create(self, parent: QWidget | None) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(parent=parent)
        # Report the value when editing is finished, not on every typed digit.
        widget.setKeyboardTracking(False)
        widget.valueChanged.connect(lambda value: self.emit(self.on_change, value))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        # Decimals before range and value, otherwise Qt rounds them to the old number of decimals;
        # the range before the value, otherwise Qt clamps the value to the old range.
        if "decimals" in changed:
            widget.setDecimals(self.decimals)
        if changed & {"decimals", "min_value", "max_value"}:
            widget.setRange(self.min_value, self.max_value)
        if "step" in changed:
            widget.setSingleStep(self.step)
        if changed & {"decimals", "value"}:
            widget.setValue(self.value)
        if "prefix" in changed:
            widget.setPrefix(self.prefix)
        if "suffix" in changed:
            widget.setSuffix(self.suffix)

    def read(self) -> float:
        return self.widget.value()
