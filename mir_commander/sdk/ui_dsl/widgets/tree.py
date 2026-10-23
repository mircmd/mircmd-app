from typing import Literal, Self

from pydantic import BaseModel, Field
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ContentWidget, check_insert, check_range

# The children of a node, each given by its own children: enough to check paths and indices.
type TreeShape = list[TreeShape]


class TreeNode(BaseModel):
    cells: list[str] = Field(..., min_length=1)
    children: list["TreeNode"] = Field(default=[])
    expanded: bool = False
    enabled: bool = True

    def build(self, parent: QTreeWidgetItem, index: int) -> QTreeWidgetItem:
        # Short rows leave the remaining cells empty.
        item = QTreeWidgetItem(self.cells)
        parent.insertChild(index, item)
        # The item is already in the widget, which it must be to be expanded.
        item.setExpanded(self.expanded)
        item.setDisabled(not self.enabled)
        for i, child in enumerate(self.children):
            child.build(item, i)
        return item

    def max_cells(self) -> int:
        return max([len(self.cells), *(child.max_cells() for child in self.children)])

    def shape(self) -> TreeShape:
        return [child.shape() for child in self.children]


class InsertNodes(BaseModel):
    op: Literal["insert_nodes"]
    id: str
    # Indices of the nodes from the top level down to the parent; empty: the top level.
    parent: list[int] = Field(default=[])
    # Omitted: the nodes are added after the last child.
    index: int | None = Field(default=None, ge=0)
    nodes: list[TreeNode] = Field(..., min_length=1)


class RemoveNodes(BaseModel):
    """Removes the nodes with their children."""

    op: Literal["remove_nodes"]
    id: str
    parent: list[int] = Field(default=[])
    index: int = Field(..., ge=0)
    count: int = Field(default=1, ge=1)


class SetNodes(BaseModel):
    """Replaces the nodes starting at index, with their children."""

    op: Literal["set_nodes"]
    id: str
    parent: list[int] = Field(default=[])
    index: int = Field(..., ge=0)
    nodes: list[TreeNode] = Field(..., min_length=1)


TreeOp = InsertNodes | RemoveNodes | SetNodes


def _item_shape(item: QTreeWidgetItem) -> TreeShape:
    return [_item_shape(child) for i in range(item.childCount()) if (child := item.child(i)) is not None]


class Tree(ContentWidget[QTreeWidget, TreeOp, TreeShape]):
    """The nodes are kept only by the widget and changed by the operations of patches."""

    type: Literal["tree"]
    headers: list[str] = Field(..., min_length=1)
    headers_visible: bool = False

    def create(self, parent: QWidget | None) -> QTreeWidget:
        widget = QTreeWidget(parent=parent)
        widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        widget.setAlternatingRowColors(True)
        widget.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        widget.header().setStretchLastSection(True)
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "headers" in changed:
            # Cells beyond the new headers are hidden.
            widget.setColumnCount(len(self.headers))
            widget.setHeaderLabels(self.headers)
        if "headers_visible" in changed:
            widget.header().setVisible(self.headers_visible)

    def shape(self) -> TreeShape:
        return _item_shape(self.widget.invisibleRootItem())

    def edited(self, op: TreeOp, shape: TreeShape) -> tuple[Self, TreeShape]:
        if not isinstance(op, TreeOp):
            # Builder.patch reports a ValueError as an invalid operation.
            raise ValueError(f"{op.op} does not apply to a tree")  # noqa: TRY004
        children = shape
        for depth, i in enumerate(op.parent):
            if not 0 <= i < len(children):
                raise ValueError(f"there is no node {op.parent[: depth + 1]}")
            children = children[i]
        if isinstance(op, InsertNodes | SetNodes):
            for node in op.nodes:
                if (cells := node.max_cells()) > len(self.headers):
                    raise ValueError(
                        f"a node has a row of {cells} cells, but there are only {len(self.headers)} columns"
                    )
        if isinstance(op, InsertNodes):
            index = len(children) if op.index is None else op.index
            check_insert("nodes", index, len(children))
            children[index:index] = [node.shape() for node in op.nodes]
        elif isinstance(op, RemoveNodes):
            check_range("nodes", op.index, op.count, len(children))
            del children[op.index : op.index + op.count]
        elif isinstance(op, SetNodes):
            check_range("nodes", op.index, len(op.nodes), len(children))
            children[op.index : op.index + len(op.nodes)] = [node.shape() for node in op.nodes]
        return self, shape

    def apply_op(self, op: TreeOp) -> None:
        parent = self.widget.invisibleRootItem()
        for i in op.parent:
            child = parent.child(i)
            assert child is not None, "the path is checked by edited"
            parent = child
        if isinstance(op, InsertNodes):
            index = parent.childCount() if op.index is None else op.index
            for i, node in enumerate(op.nodes):
                node.build(parent, index + i)
        elif isinstance(op, RemoveNodes):
            for _ in range(op.count):
                parent.takeChild(op.index)
        elif isinstance(op, SetNodes):
            for i, node in enumerate(op.nodes):
                parent.takeChild(op.index + i)
                node.build(parent, op.index + i)
