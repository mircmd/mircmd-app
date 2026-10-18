from pathlib import Path

from PySide6.QtWidgets import QWidget

from mir_commander.sdk.ui_dsl.schema import Root
from mir_commander.sdk.ui_dsl.widgets.base import Widget


class Builder:
    def __init__(self, root: Root, extension_path: Path, parent: QWidget | None):
        self._root = root
        self._widget = self._build_view(extension_path, root, parent)

    def _build_view(self, extension_path: Path, root: Root, parent: QWidget | None) -> QWidget:
        if isinstance(root.item, Widget):
            widget = root.item.build(extension_path, parent)
            if widget is not None:
                return widget
            return QWidget(parent=parent)
        else:
            container = QWidget(parent=parent)
            if layout := root.item.build(extension_path, container):
                container.setLayout(layout)
            return container

    def get_widget(self) -> QWidget:
        return self._widget
