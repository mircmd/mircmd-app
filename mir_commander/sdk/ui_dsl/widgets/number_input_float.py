from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QDoubleSpinBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, ValueWidget


class NumberInputFloat(ValueWidget):
    type: Literal["number_input_float"]
    min_value: float
    max_value: float
    value: float
    step: float = Field(default=1, gt=0)
    decimals: int = Field(default=2, ge=0, le=16)
    prefix: str = ""
    suffix: str = ""

    on_change: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(parent=parent)
        # Decimals before range and value, otherwise Qt rounds them to the default 2 decimals.
        widget.setDecimals(self.decimals)
        widget.setRange(self.min_value, self.max_value)
        widget.setSingleStep(self.step)
        widget.setValue(self.value)
        widget.setPrefix(self.prefix)
        widget.setSuffix(self.suffix)
        # Report the value when editing is finished, not on every typed digit.
        widget.setKeyboardTracking(False)
        widget.setEnabled(self.enabled)
        context.values[self.id] = widget.value
        if len(self.on_change) > 0:
            widget.valueChanged.connect(lambda value: self.emit(context, self.on_change, value))
        return widget
