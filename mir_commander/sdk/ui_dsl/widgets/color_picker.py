from typing import Any, Literal

from pydantic import Field
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, ValueWidget
from mir_commander.sdk.widgets import ColorButton as ColorButtonWidget


def _color(color: QColor) -> dict[str, Any]:
    return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}


class ColorPicker(ValueWidget):
    type: Literal["color_picker"]
    r: int = Field(default=0, ge=0, le=255)
    g: int = Field(default=0, ge=0, le=255)
    b: int = Field(default=0, ge=0, le=255)
    a: int = Field(default=255, ge=0, le=255)
    alpha: bool = Field(default=False)

    on_change: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QPushButton:
        widget = ColorButtonWidget(color=QColor(self.r, self.g, self.b, a=self.a), alpha=self.alpha, parent=parent)
        widget.setEnabled(self.enabled)
        context.values[self.id] = lambda: _color(widget.color)
        if len(self.on_change) > 0:
            widget.color_changed.connect(lambda color: self.emit(context, self.on_change, _color(color)))
        return widget
