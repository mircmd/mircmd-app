from typing import Literal

from pydantic import Field
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ORIENTATION, BuildContext, Orientation, ValueWidget


class Slider(ValueWidget):
    type: Literal["slider"]
    orientation: Orientation
    min_value: int
    max_value: int
    value: int
    step: int = Field(default=1)
    # Send on_change while the handle is dragged, not only when it is released.
    tracking: bool = False

    on_change: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QSlider:
        widget = QSlider(ORIENTATION.get(self.orientation, Qt.Orientation.Horizontal), parent=parent)
        widget.setRange(self.min_value, self.max_value)
        widget.setValue(self.value)
        widget.setSingleStep(self.step)
        widget.setTracking(self.tracking)
        widget.setEnabled(self.enabled)
        context.values[self.id] = widget.value
        if len(self.on_change) > 0:
            widget.valueChanged.connect(lambda value: self.emit(context, self.on_change, value))
        return widget
