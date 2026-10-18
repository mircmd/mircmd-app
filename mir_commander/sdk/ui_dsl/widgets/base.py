from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLayout, QWidget


class Align(Enum):
    Left = "left"
    Center = "center"
    Right = "right"


class Orientation(Enum):
    Horizontal = "horizontal"
    Vertical = "vertical"


AlignLeft = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

ALIGN = {
    Align.Left: AlignLeft,
    Align.Center: Qt.AlignmentFlag.AlignCenter,
    Align.Right: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
}

ORIENTATION = {
    Orientation.Horizontal: Qt.Orientation.Horizontal,
    Orientation.Vertical: Qt.Orientation.Vertical,
}


class UiItem(BaseModel):
    id: str = Field(..., min_length=1)


class Widget(UiItem):
    enabled: bool = True

    def build(self, extension_path: Path, parent: QWidget | None) -> QWidget | None:
        return None


class Layout(UiItem):
    def build(self, extension_path: Path, parent: QWidget) -> QLayout | None:
        return None
