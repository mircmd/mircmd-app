from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, Field, PrivateAttr
from PySide6.QtCore import QSignalBlocker, Qt
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
    # Built widgets by id, filled while the view is built.
    widgets: dict[str, "Widget[Any]"] = field(default_factory=dict)

    def read(self, id: str) -> Any:
        model = self.widgets[id]
        assert isinstance(model, ValueWidget), f"{id!r} has no value"
        return model.read()


class UiItem(BaseModel):
    id: str = Field(..., min_length=1)


class Widget[W: QWidget](UiItem):
    """A model of a Qt widget: create makes the widget and connects its signals, apply sets its properties.

    A model is built into one widget and then stays bound to it; copies made with model_validate are not bound.
    """

    enabled: bool = True
    # Ids of widgets whose current values are added to the payload of every event of this widget.
    collect: list[str] = Field(default=[])

    _widget: W | None = PrivateAttr(default=None)
    _context: BuildContext | None = PrivateAttr(default=None)

    @property
    def widget(self) -> W:
        if self._widget is None:
            raise RuntimeError(f"{self.id!r} is not built")
        return self._widget

    @property
    def context(self) -> BuildContext:
        if self._context is None:
            raise RuntimeError(f"{self.id!r} is not built")
        return self._context

    def build(self, context: BuildContext, parent: QWidget | None) -> W:
        if self._widget is not None:
            raise RuntimeError(f"{self.id!r} is already built")
        self._context = context
        self._widget = self.create(parent)
        # Setting the initial values is not an action of the user.
        with QSignalBlocker(self._widget):
            self.apply(set(type(self).model_fields))
        context.widgets[self.id] = self
        return self._widget

    def create(self, parent: QWidget | None) -> W:
        raise NotImplementedError

    def apply(self, changed: set[str]) -> None:
        """Sets the properties named in changed; called with signals of the widget blocked."""
        if "enabled" in changed:
            self.widget.setEnabled(self.enabled)

    def check_collect(self, items: Mapping[str, UiItem]) -> None:
        for id in self.collect:
            if id not in items:
                raise ValueError(f"{self.id!r} collects {id!r}, which does not exist")
            if not isinstance(items[id], ValueWidget):
                # Pydantic reports only ValueError as a validation error.
                raise ValueError(f"{self.id!r} collects {id!r}, which has no value")  # noqa: TRY004

    def emit(self, action: str, value: Any):
        # Signals are connected once in create, so an event without an action is dropped here.
        if not action:
            return
        payload = {self.id: value}
        if self.collect:
            # Read when the event happens: the collected widgets may be built after this one.
            payload |= {id: self.context.read(id) for id in self.collect}
        self.context.emit(f"{self.id}:{action}", payload)


class ValueWidget[W: QWidget](Widget[W]):
    """A widget with a value that events of other widgets can collect."""

    def read(self) -> Any:
        raise NotImplementedError


def check_range(what: str, index: int, count: int, size: int):
    if index + count > size:
        raise ValueError(f"{what} {index}..{index + count - 1} are out of range, there are {size}")


def check_insert(what: str, index: int, size: int):
    if index > size:
        raise ValueError(f"cannot insert {what} at {index}, there are only {size}")


class ContentWidget[W: QWidget, Op, Shape](Widget[W]):
    """A widget whose content (rows, nodes) is kept only by the Qt widget and changed by patch operations.

    The model describes only the structure, e.g. the headers. A patch is checked against the shape of the
    content taken from the widget and changed operation by operation, and applied only if all of it is valid.
    """

    def shape(self) -> Shape:
        """The shape of the content of the built widget, enough to check operations."""
        raise NotImplementedError

    def edited(self, op: Op, shape: Shape) -> tuple[Self, Shape]:
        """Checks the operation; returns the model and the shape after it. Raises ValueError if it is invalid."""
        raise NotImplementedError

    def apply_op(self, op: Op) -> None:
        """Shows a checked operation in the widget; called with signals of the widget blocked."""
        raise NotImplementedError


class Layout(UiItem):
    def build(self, context: BuildContext, parent: QWidget) -> QLayout | None:
        return None

    def children(self) -> list[UiItem]:
        return []
