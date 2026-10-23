from typing import Literal

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class Button(Widget[QPushButton]):
    type: Literal["button"]
    text: str = ""
    icon: str = ""

    on_click: str = ""

    def create(self, parent: QWidget | None) -> QPushButton:
        widget = QPushButton(parent=parent)
        widget.clicked.connect(lambda: self.emit(self.on_click, {}))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "text" in changed:
            widget.setText(self.text)
        if "icon" in changed:
            widget.setIcon(QIcon(str(self.context.extension_path / self.icon)) if self.icon else QIcon())
