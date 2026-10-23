from typing import Literal

from pydantic import Field
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ORIENTATION, Orientation, ValueWidget


class Slider(ValueWidget[QSlider]):
    type: Literal["slider"]
    orientation: Orientation
    min_value: int
    max_value: int
    value: int
    step: int = Field(default=1)
    # Send on_change while the handle is dragged, not only when it is released.
    tracking: bool = False

    on_change: str = ""

    def create(self, parent: QWidget | None) -> QSlider:
        widget = QSlider(parent=parent)
        widget.valueChanged.connect(lambda value: self.emit(self.on_change, value))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "orientation" in changed:
            widget.setOrientation(ORIENTATION.get(self.orientation, Qt.Orientation.Horizontal))
        # The range before the value, otherwise Qt clamps the value to the old range.
        if changed & {"min_value", "max_value"}:
            widget.setRange(self.min_value, self.max_value)
        if "value" in changed:
            widget.setValue(self.value)
        if "step" in changed:
            widget.setSingleStep(self.step)
        if "tracking" in changed:
            widget.setTracking(self.tracking)

    def read(self) -> int:
        return self.widget.value()
