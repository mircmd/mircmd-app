from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QLineEdit, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, ValueWidget


class TextInput(ValueWidget):
    type: Literal["text_input"]
    text: str = Field(..., min_length=0)
    placeholder: str = ""

    # Sent on every change made by the user.
    on_edit: str = ""
    # Sent on Enter.
    on_submit: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QLineEdit:
        widget = QLineEdit(self.text, parent=parent)
        widget.setPlaceholderText(self.placeholder)
        widget.setEnabled(self.enabled)
        context.values[self.id] = widget.text
        if len(self.on_edit) > 0:
            # textEdited, unlike textChanged, is not emitted for text set by the program.
            widget.textEdited.connect(lambda text: self.emit(context, self.on_edit, text))
        if len(self.on_submit) > 0:
            widget.returnPressed.connect(lambda: self.emit(context, self.on_submit, widget.text()))
        return widget
