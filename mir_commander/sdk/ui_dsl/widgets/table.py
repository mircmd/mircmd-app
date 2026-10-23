from collections.abc import Callable
from typing import Any, Literal, Self

from pydantic import BaseModel, Field
from PySide6.QtGui import QKeyEvent, Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import ContentWidget, check_insert, check_range

_EDIT_TRIGGERS = (
    QAbstractItemView.EditTrigger.DoubleClicked
    | QAbstractItemView.EditTrigger.EditKeyPressed
    | QAbstractItemView.EditTrigger.AnyKeyPressed
)


class InsertRows(BaseModel):
    op: Literal["insert_rows"]
    id: str
    # Omitted: the rows are added at the end.
    index: int | None = Field(default=None, ge=0)
    rows: list[list[str]] = Field(..., min_length=1)


class RemoveRows(BaseModel):
    op: Literal["remove_rows"]
    id: str
    index: int = Field(..., ge=0)
    count: int = Field(default=1, ge=1)


class SetRows(BaseModel):
    """Replaces the rows starting at index."""

    op: Literal["set_rows"]
    id: str
    index: int = Field(..., ge=0)
    rows: list[list[str]] = Field(..., min_length=1)


class NewColumn(BaseModel):
    header: str = ""
    # One cell per row from the first; the cells of the remaining rows are empty.
    cells: list[str] = Field(default=[])


class InsertColumns(BaseModel):
    op: Literal["insert_columns"]
    id: str
    # Omitted: the columns are added at the end.
    index: int | None = Field(default=None, ge=0)
    columns: list[NewColumn] = Field(..., min_length=1)


class RemoveColumns(BaseModel):
    op: Literal["remove_columns"]
    id: str
    index: int = Field(..., ge=0)
    count: int = Field(default=1, ge=1)


class ColumnChange(BaseModel):
    # Omitted: the header or the cells stay as they are.
    header: str | None = None
    cells: list[str] | None = None


class SetColumns(BaseModel):
    """Changes the columns starting at index."""

    op: Literal["set_columns"]
    id: str
    index: int = Field(..., ge=0)
    columns: list[ColumnChange] = Field(..., min_length=1)


TableOp = InsertRows | RemoveRows | SetRows | InsertColumns | RemoveColumns | SetColumns


def _check_cells(cells: list[str], rows: int):
    if len(cells) > rows:
        raise ValueError(f"a column has {len(cells)} cells, but there are only {rows} rows")


def _check_rows(rows: list[list[str]], columns: int):
    for row in rows:
        if len(row) > columns:
            raise ValueError(f"a row has {len(row)} cells, but there are only {columns} columns")


class TableWidget(QTableWidget):
    def __init__(self, on_rows_delete: Callable[[list[int]], None], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._on_rows_delete = on_rows_delete

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete_selected_rows()
        else:
            super().keyPressEvent(event)

    def _delete_selected_rows(self):
        selected_indexes = self.selectionModel().selectedRows()
        if not selected_indexes:
            return

        rows_to_delete = [index.row() for index in selected_indexes]
        model = self.model()
        for row in sorted(rows_to_delete, reverse=True):
            model.removeRow(row)

        self._on_rows_delete(rows_to_delete)


class Table(ContentWidget[TableWidget, TableOp, int]):
    """The rows are kept only by the widget and changed by the operations of patches; the shape is the row count."""

    type: Literal["table"]
    headers: list[str] = Field(..., min_length=1)
    horizontal_headers_visible: bool = True
    vertical_headers_visible: bool = False
    editable: bool = False

    on_rows_delete: str = ""
    on_cell_change: str = ""

    def create(self, parent: QWidget | None) -> TableWidget:
        widget = TableWidget(on_rows_delete=lambda rows: self.emit(self.on_rows_delete, rows), parent=parent)
        widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        widget.setAlternatingRowColors(True)
        widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        widget.horizontalHeader().setStretchLastSection(True)
        widget.itemChanged.connect(
            lambda item: self.emit(
                self.on_cell_change, {"column": item.column(), "row": item.row(), "value": item.text()}
            )
        )
        return widget

    def apply(self, changed: set[str]) -> None:
        super().apply(changed)
        widget = self.widget
        if "headers" in changed:
            # Columns beyond the new headers are removed with their cells.
            widget.setColumnCount(len(self.headers))
            widget.setHorizontalHeaderLabels(self.headers)
        if "editable" in changed:
            widget.setEditTriggers(_EDIT_TRIGGERS if self.editable else QAbstractItemView.EditTrigger.NoEditTriggers)
        if "horizontal_headers_visible" in changed:
            widget.horizontalHeader().setVisible(self.horizontal_headers_visible)
        if "vertical_headers_visible" in changed:
            widget.verticalHeader().setVisible(self.vertical_headers_visible)

    def shape(self) -> int:
        return self.widget.rowCount()

    def edited(self, op: TableOp, shape: int) -> tuple[Self, int]:
        if not isinstance(op, TableOp):
            # Builder.patch reports a ValueError as an invalid operation.
            raise ValueError(f"{op.op} does not apply to a table")  # noqa: TRY004
        rows = shape
        headers = list(self.headers)
        if isinstance(op, InsertRows):
            check_insert("rows", rows if op.index is None else op.index, rows)
            _check_rows(op.rows, len(headers))
            rows += len(op.rows)
        elif isinstance(op, RemoveRows):
            check_range("rows", op.index, op.count, rows)
            rows -= op.count
        elif isinstance(op, SetRows):
            check_range("rows", op.index, len(op.rows), rows)
            _check_rows(op.rows, len(headers))
        elif isinstance(op, InsertColumns):
            index = len(headers) if op.index is None else op.index
            check_insert("columns", index, len(headers))
            for column in op.columns:
                _check_cells(column.cells, rows)
            headers[index:index] = [column.header for column in op.columns]
        elif isinstance(op, RemoveColumns):
            check_range("columns", op.index, op.count, len(headers))
            del headers[op.index : op.index + op.count]
        elif isinstance(op, SetColumns):
            check_range("columns", op.index, len(op.columns), len(headers))
            for i, change in enumerate(op.columns):
                if change.header is not None:
                    headers[op.index + i] = change.header
                if change.cells is not None:
                    _check_cells(change.cells, rows)
        if headers == self.headers:
            return self, rows
        return type(self).model_validate({**self.model_dump(), "headers": headers}), rows

    def apply_op(self, op: TableOp) -> None:
        """Changes the widget row by row or column by column, keeping the selection and scrolling."""
        widget = self.widget
        if isinstance(op, InsertRows):
            index = widget.rowCount() if op.index is None else op.index
            for i, cells in enumerate(op.rows):
                widget.insertRow(index + i)
                self._show_row(index + i, cells)
        elif isinstance(op, RemoveRows):
            for _ in range(op.count):
                widget.removeRow(op.index)
        elif isinstance(op, SetRows):
            for i, cells in enumerate(op.rows):
                self._show_row(op.index + i, cells)
        elif isinstance(op, InsertColumns):
            index = widget.columnCount() if op.index is None else op.index
            for i, column in enumerate(op.columns):
                widget.insertColumn(index + i)
                self._show_column(index + i, column.header, column.cells)
        elif isinstance(op, RemoveColumns):
            for _ in range(op.count):
                widget.removeColumn(op.index)
        elif isinstance(op, SetColumns):
            for i, change in enumerate(op.columns):
                self._show_column(op.index + i, change.header, change.cells)

    def _show_row(self, row: int, cells: list[str]):
        # Short rows leave the remaining cells empty.
        for column in range(self.widget.columnCount()):
            self._show_cell(row, column, cells[column] if column < len(cells) else "")

    def _show_column(self, column: int, header: str | None, cells: list[str] | None):
        if header is not None:
            self.widget.setHorizontalHeaderItem(column, QTableWidgetItem(header))
        if cells is not None:
            # Short columns leave the remaining cells empty.
            for row in range(self.widget.rowCount()):
                self._show_cell(row, column, cells[row] if row < len(cells) else "")

    def _show_cell(self, row: int, column: int, text: str):
        if text:
            self.widget.setItem(row, column, QTableWidgetItem(text))
        else:
            self.widget.takeItem(row, column)
