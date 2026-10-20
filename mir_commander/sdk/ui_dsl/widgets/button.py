from typing import Literal

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, Widget


class Button(Widget):
    type: Literal["button"]
    text: str = ""
    icon: str = ""

    on_click: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QPushButton:
        if self.icon:
            widget = QPushButton(QIcon(str(context.extension_path / self.icon)), self.text, parent=parent)
        else:
            widget = QPushButton(self.text, parent=parent)
        widget.setEnabled(self.enabled)
        if len(self.on_click) > 0:
            widget.clicked.connect(lambda: self.emit(context, self.on_click, {}))
        return widget
