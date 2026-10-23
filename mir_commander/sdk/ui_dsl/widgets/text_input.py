from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QLineEdit, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ValueWidget


class TextInput(ValueWidget[QLineEdit]):
    type: Literal["text_input"]
    text: str = Field(..., min_length=0)
    placeholder: str = ""

    # Sent on every change made by the user.
    on_edit: str = ""
    # Sent on Enter.
    on_submit: str = ""

    def create(self, parent: QWidget | None) -> QLineEdit:
        widget = QLineEdit(parent=parent)
        # textEdited, unlike textChanged, is not emitted for text set by the program.
        widget.textEdited.connect(lambda text: self.emit(self.on_edit, text))
        widget.returnPressed.connect(lambda: self.emit(self.on_submit, widget.text()))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "text" in changed:
            widget.setText(self.text)
        if "placeholder" in changed:
            widget.setPlaceholderText(self.placeholder)

    def read(self) -> str:
        return self.widget.text()
