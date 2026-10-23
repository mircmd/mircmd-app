from enum import Enum
from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ValueWidget


class CheckState(Enum):
    Unchecked = "unchecked"
    PartiallyChecked = "partially_checked"
    Checked = "checked"


CHECK_STATE = {
    CheckState.Unchecked: Qt.CheckState.Unchecked,
    CheckState.PartiallyChecked: Qt.CheckState.PartiallyChecked,
    CheckState.Checked: Qt.CheckState.Checked,
}

_FROM_QT_CHECK_STATE = {qt_state: state for state, qt_state in CHECK_STATE.items()}


class Checkbox(ValueWidget[QCheckBox]):
    type: Literal["checkbox"]
    state: CheckState

    on_change: str = ""

    def create(self, parent: QWidget | None) -> QCheckBox:
        widget = QCheckBox(parent=parent)
        widget.checkStateChanged.connect(lambda state: self.emit(self.on_change, _FROM_QT_CHECK_STATE[state].value))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "state" in changed:
            widget.setCheckState(CHECK_STATE[self.state])

    def read(self) -> str:
        return _FROM_QT_CHECK_STATE[self.widget.checkState()].value
