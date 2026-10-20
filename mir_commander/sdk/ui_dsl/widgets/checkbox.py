from enum import Enum
from typing import Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, ValueWidget


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


class Checkbox(ValueWidget):
    type: Literal["checkbox"]
    state: CheckState

    on_change: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QCheckBox:
        widget = QCheckBox(parent=parent)
        widget.setCheckState(CHECK_STATE[self.state])
        widget.setEnabled(self.enabled)
        context.values[self.id] = lambda: _FROM_QT_CHECK_STATE[widget.checkState()].value
        if len(self.on_change) > 0:
            widget.checkStateChanged.connect(
                lambda state: self.emit(context, self.on_change, _FROM_QT_CHECK_STATE[state].value)
            )
        return widget
