from collections.abc import Iterable
from dataclasses import dataclass, field

from PySide6.QtWidgets import QWidget

from mir_commander.sdk.program import ControlPanel
from mir_commander.sdk.widgets import VerticalStackLayout


@dataclass
class BaseControlBlock:
    title: str
    widget: QWidget
    expanded: bool = field(default=True, doc="Whether the block is expanded by default")


class BaseControlPanel(ControlPanel):
    def get_widget(self) -> QWidget:
        vertical_stack = VerticalStackLayout()

        for block in self.get_blocks():
            vertical_stack.add_widget(block.title, block.widget, block.expanded)
        vertical_stack.addStretch(1)

        widget = QWidget()
        widget.setLayout(vertical_stack)
        return widget

    def get_blocks(self) -> Iterable[BaseControlBlock]:
        raise NotImplementedError
