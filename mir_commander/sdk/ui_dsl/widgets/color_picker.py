from pathlib import Path
from typing import Literal

from pydantic import Field
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget
from mir_commander.sdk.widgets import ColorButton as ColorButtonWidget


class ColorPicker(Widget):
    type: Literal["color_picker"]
    r: int = Field(default=0, ge=0, le=255)
    g: int = Field(default=0, ge=0, le=255)
    b: int = Field(default=0, ge=0, le=255)
    a: int = Field(default=255, ge=0, le=255)
    alpha: bool = Field(default=False)

    def build(self, extension_path: Path, parent: QWidget | None) -> QPushButton:
        widget = ColorButtonWidget(color=QColor(self.r, self.g, self.b, a=self.a), alpha=self.alpha, parent=parent)
        widget.setEnabled(self.enabled)
        return widget
