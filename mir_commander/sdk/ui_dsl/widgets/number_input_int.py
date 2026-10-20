from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QSpinBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, ValueWidget


class NumberInputInt(ValueWidget):
    type: Literal["number_input_int"]
    min_value: int
    max_value: int
    value: int
    step: int = Field(default=1, gt=0)
    prefix: str = ""
    suffix: str = ""

    on_change: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QSpinBox:
        widget = QSpinBox(parent=parent)
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
