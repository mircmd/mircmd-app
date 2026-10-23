from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QLabel, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ALIGN, Align, AlignLeft, Widget


class Label(Widget[QLabel]):
    type: Literal["label"]
    text: str = Field(..., min_length=1)
    wrap: bool = Field(default=False)
    align: Align = Field(default=Align.Left)

    # Sent when a link <a href="..."> in the text is clicked.
    on_link: str = ""

    def create(self, parent: QWidget | None) -> QLabel:
        widget = QLabel(parent=parent)
        widget.linkActivated.connect(lambda href: self.emit(self.on_link, {"href": href}))
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "text" in changed:
            widget.setText(self.text)
        if "wrap" in changed:
            widget.setWordWrap(self.wrap)
        if "align" in changed:
            widget.setAlignment(ALIGN.get(self.align, AlignLeft))
