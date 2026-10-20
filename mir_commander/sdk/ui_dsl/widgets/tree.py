from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, Widget


class TreeNode(BaseModel):
    cells: list[str] = Field(..., min_length=1)
    children: list["TreeNode"] = Field(default=[])
    expanded: bool = False
    enabled: bool = True

    def build(self, parent: QTreeWidget | QTreeWidgetItem) -> QTreeWidgetItem:
        # Short rows leave the remaining cells empty.
        item = QTreeWidgetItem(parent, self.cells)
        # The item is already in the widget, which it must be to be expanded.
        item.setExpanded(self.expanded)
        item.setDisabled(not self.enabled)
        for child in self.children:
            child.build(item)
        return item

    def max_cells(self) -> int:
        return max([len(self.cells), *(child.max_cells() for child in self.children)])


class Tree(Widget):
    type: Literal["tree"]
    headers: list[str] = Field(..., min_length=1)
    data: list[TreeNode] = Field(default=[])

    @model_validator(mode="after")
    def _check_nodes(self) -> Self:
        for i, node in enumerate(self.data):
            if (cells := node.max_cells()) > len(self.headers):
                raise ValueError(f"node {i} has a row of {cells} cells, but there are only {len(self.headers)} columns")
        return self

    def build(self, context: BuildContext, parent: QWidget | None) -> QTreeWidget:
        widget = QTreeWidget(parent=parent)
        widget.setHeaderLabels(self.headers)
        for node in self.data:
            node.build(widget)
        widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        widget.setAlternatingRowColors(True)
        widget.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        widget.header().setStretchLastSection(True)
        widget.setEnabled(self.enabled)
        return widget
