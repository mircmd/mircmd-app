from pathlib import Path
from typing import Literal

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class Button(Widget):
    type: Literal["button"]
    text: str = ""
    icon: str = ""

    def build(self, extension_path: Path, parent: QWidget | None) -> QPushButton:
        if self.icon:
            widget = QPushButton(QIcon(str(extension_path / self.icon)), self.text, parent=parent)
        else:
            widget = QPushButton(self.text, parent=parent)
        widget.setEnabled(self.enabled)
        return widget
