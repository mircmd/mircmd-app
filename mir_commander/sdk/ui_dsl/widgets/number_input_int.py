from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QSpinBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ValueWidget


class NumberInputInt(ValueWidget[QSpinBox]):
    type: Literal["number_input_int"]
    min_value: int
    max_value: int
    value: int
    step: int = Field(default=1, gt=0)
    prefix: str = ""
    suffix: str = ""

    on_change: str = ""

    def create(self, parent: QWidget | None) -> QSpinBox:
        widget = QSpinBox(parent=parent)
        # Report the value when editing is finished, not on every typed digit.
        widget.setKeyboardTracking(False)
        widget.valueChanged.connect(lambda value: self.emit(self.on_change, value))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        # The range before the value, otherwise Qt clamps the value to the old range.
        if changed & {"min_value", "max_value"}:
            widget.setRange(self.min_value, self.max_value)
        if "step" in changed:
            widget.setSingleStep(self.step)
        if "value" in changed:
            widget.setValue(self.value)
        if "prefix" in changed:
            widget.setPrefix(self.prefix)
        if "suffix" in changed:
            widget.setSuffix(self.suffix)

    def read(self) -> int:
        return self.widget.value()
