from typing import Any, Literal

from pydantic import Field
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ValueWidget
from mir_commander.sdk.widgets import ColorButton as ColorButtonWidget


def _color(color: QColor) -> dict[str, Any]:
    return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}


class ColorPicker(ValueWidget[ColorButtonWidget]):
    type: Literal["color_picker"]
    r: int = Field(default=0, ge=0, le=255)
    g: int = Field(default=0, ge=0, le=255)
    b: int = Field(default=0, ge=0, le=255)
    a: int = Field(default=255, ge=0, le=255)
    alpha: bool = Field(default=False)

    on_change: str = ""

    def create(self, parent: QWidget | None) -> ColorButtonWidget:
        widget = ColorButtonWidget(parent=parent)
        widget.color_changed.connect(lambda color: self.emit(self.on_change, _color(color)))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if changed & {"r", "g", "b", "a"}:
            widget.set_color(QColor(self.r, self.g, self.b, a=self.a))
        if "alpha" in changed:
            widget.set_alpha(self.alpha)

    def read(self) -> dict[str, Any]:
        return _color(self.widget.color)
