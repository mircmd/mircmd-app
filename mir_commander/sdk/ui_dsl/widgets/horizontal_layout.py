from typing import Literal

from PySide6.QtWidgets import QHBoxLayout, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ALIGN, AlignLeft, BuildContext, Layout, UiItem, Widget
from mir_commander.sdk.ui_dsl.widgets.layout_item import LayoutItem
from mir_commander.sdk.ui_dsl.widgets.space import Space


class HorizontalLayout(Layout):
    type: Literal["horizontal_layout"]
    items: list[LayoutItem]

    def build(self, context: BuildContext, parent: QWidget) -> QHBoxLayout:
        layout = QHBoxLayout()
        for item in self.items:
            if isinstance(item.item, Space):
                layout.addSpacing(item.item.size)
            elif isinstance(item.item, Widget):
                if q_widget := item.item.build(context, parent):
                    layout.addWidget(q_widget, alignment=ALIGN.get(item.align, AlignLeft))
            else:
                if q_layout := item.item.build(context, parent):
                    layout.addLayout(q_layout)
        return layout

    def children(self) -> list[UiItem]:
        return [item.item for item in self.items]
