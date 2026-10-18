from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from mir_commander.sdk.ui_dsl.widgets.base import Widget


class Table(Widget):
    type: Literal["table"]
    headers: list[str] = Field(..., min_length=1)
    data: list[list[str]] = Field(default=[])

    @model_validator(mode="after")
    def _check_rows(self) -> Self:
        for i, row in enumerate(self.data):
            if len(row) > len(self.headers):
                raise ValueError(f"row {i} has {len(row)} cells, but there are only {len(self.headers)} columns")
        return self

    def build(self, extension_path: Path, parent: QWidget | None) -> QTableWidget:
        widget = QTableWidget(len(self.data), len(self.headers), parent=parent)
        widget.setHorizontalHeaderLabels(self.headers)
        # Short rows leave the remaining cells empty.
        for row, cells in enumerate(self.data):
            for column, text in enumerate(cells):
                widget.setItem(row, column, QTableWidgetItem(text))
        widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        widget.setAlternatingRowColors(True)
        widget.verticalHeader().setVisible(False)
        widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        widget.horizontalHeader().setStretchLastSection(True)
        widget.setEnabled(self.enabled)
        return widget
