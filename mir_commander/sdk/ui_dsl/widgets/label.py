from pathlib import Path
from typing import Literal

from pydantic import Field
from PySide6.QtWidgets import QLabel, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ALIGN, Align, AlignLeft, Widget


class Label(Widget):
    type: Literal["label"]
    text: str = Field(..., min_length=1)
    wrap: bool = Field(default=False)
    align: Align = Field(default=Align.Left)

    def build(self, extension_path: Path, parent: QWidget | None) -> QLabel:
        widget = QLabel(self.text, parent=parent)
        widget.setWordWrap(self.wrap)
        widget.setAlignment(ALIGN.get(self.align, AlignLeft))
        widget.setEnabled(self.enabled)
        return widget
