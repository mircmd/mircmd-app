from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QLabel, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ALIGN, Align, AlignLeft, BuildContext, Widget


class Label(Widget):
    type: Literal["label"]
    text: str = Field(..., min_length=1)
    wrap: bool = Field(default=False)
    align: Align = Field(default=Align.Left)

    # Sent when a link <a href="..."> in the text is clicked.
    on_link: str = ""

    def build(self, context: BuildContext, parent: QWidget | None) -> QLabel:
        widget = QLabel(self.text, parent=parent)
        widget.setWordWrap(self.wrap)
        widget.setAlignment(ALIGN.get(self.align, AlignLeft))
        widget.setEnabled(self.enabled)
        if len(self.on_link) > 0:
            widget.linkActivated.connect(lambda href: self.emit(context, self.on_link, {"href": href}))
        return widget
