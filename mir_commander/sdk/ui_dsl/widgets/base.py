from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

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


@dataclass
class BuildContext:
    extension_path: Path
    emit: Callable[[str, dict[str, Any]], None]
    # Readers of the current values of ValueWidget widgets by id, filled while the view is built.
    values: dict[str, Callable[[], Any]] = field(default_factory=dict)


class UiItem(BaseModel):
    id: str = Field(..., min_length=1)


class Widget(UiItem):
    enabled: bool = True
    # Ids of widgets whose current values are added to the payload of every event of this widget.
    collect: list[str] = Field(default=[])

    def build(self, context: BuildContext, parent: QWidget | None) -> QWidget | None:
        return None

    def emit(self, context: BuildContext, action: str, value: Any):
        payload = {self.id: value}
        if self.collect:
            # Read when the event happens: the collected widgets may be built after this one.
            payload |= {id: context.values[id]() for id in self.collect}
        context.emit(f"{self.id}:{action}", payload)


class ValueWidget(Widget):
    """A widget with a value that events of other widgets can collect; build registers its reader in context."""


class Layout(UiItem):
    def build(self, context: BuildContext, parent: QWidget) -> QLayout | None:
        return None

    def children(self) -> list[UiItem]:
        return []
