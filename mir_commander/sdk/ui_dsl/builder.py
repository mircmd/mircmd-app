from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QWidget

from mir_commander.sdk.ui_dsl.schema import Root
from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, Widget


class Builder:
    def __init__(self, root: Root, extension_path: Path, parent: QWidget | None):
        self._root = root
        self._widget = self._build_view(BuildContext(extension_path, self._emit), root, parent)

    def _build_view(self, context: BuildContext, root: Root, parent: QWidget | None) -> QWidget:
        if isinstance(root.item, Widget):
            widget = root.item.build(context, parent)
            if widget is not None:
                return widget
            return QWidget(parent=parent)
        else:
            container = QWidget(parent=parent)
            if layout := root.item.build(context, container):
                container.setLayout(layout)
            return container

    def _emit(self, action: str, payload: dict[str, Any]) -> None:
        print(action, payload)

    def get_widget(self) -> QWidget:
        return self._widget
