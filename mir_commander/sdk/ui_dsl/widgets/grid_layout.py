from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field
from PySide6.QtWidgets import QGridLayout, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ALIGN, Align, AlignLeft, Layout, Widget

if TYPE_CHECKING:
    from mir_commander.sdk.ui_dsl.schema import ITEMS


class GridItem(BaseModel):
    item: "ITEMS" = Field(..., discriminator="type")
    row: int = Field(..., ge=0)
    column: int = Field(..., ge=0)
    row_span: int = Field(default=1, ge=1)
    column_span: int = Field(default=1, ge=1)
    align: Align = Field(default=Align.Left)


class GridLayout(Layout):
    type: Literal["grid_layout"]
    items: list[GridItem]

    def build(self, extension_path: Path, parent: QWidget) -> QGridLayout:
        layout = QGridLayout()
        for item in self.items:
            if isinstance(item.item, Widget):
                if q_widget := item.item.build(extension_path, parent):
                    layout.addWidget(
                        q_widget,
                        item.row,
                        item.column,
                        item.row_span,
                        item.column_span,
                        alignment=ALIGN.get(item.align, AlignLeft),
                    )
            else:
                if q_layout := item.item.build(extension_path, parent):
                    layout.addLayout(
                        q_layout,
                        item.row,
                        item.column,
                        item.row_span,
                        item.column_span,
                        alignment=ALIGN.get(item.align, AlignLeft),
                    )
        return layout
