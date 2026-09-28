import logging
from collections.abc import Callable
from enum import Enum
from typing import cast

from PySide6.QtCore import QModelIndex, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction, QStandardItemModel
from PySide6.QtWidgets import QApplication, QMenu, QTreeView

from mir_commander.app_config import ImportFileRulesConfig
from mir_commander.docks.project_dock.config import TreeConfig
from mir_commander.item import Item

logger = logging.getLogger(__name__)


class ActionType(Enum):
    OPEN = "open"


class TreeView(QTreeView):
    open_item = Signal(Item, str, dict)  # type: ignore[arg-type]

    def __init__(self, item_model: QStandardItemModel, config: TreeConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._model = item_model

        icon_size = config.icon_size

        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.setIconSize(QSize(icon_size, icon_size))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.doubleClicked.connect(self._item_double_clicked)
        self.setModel(self._model)

    def _show_context_menu(self, pos: QPoint):
        item: Item = cast(Item, self._model.itemFromIndex(self.indexAt(pos)))
        if item:
            if menu := self._build_context_menu(item):
                menu.exec(self.mapToGlobal(pos))

    def _build_context_menu(self, item: Item) -> QMenu | None:
        result = QMenu()

        import_file_action = QAction(text=self.tr("Import File"), parent=result)
        import_file_action.triggered.connect(lambda: self.import_file(item))
        result.addAction(import_file_action)

        # for exporter in self._file_manager.get_exporters():
        #     if item.project_node.type in exporter.plugin.details.supported_node_types:
        #         export_item_action = QAction(text=self.tr("Export..."), parent=result)
        #         export_item_action.triggered.connect(lambda: self.export_item(item))
        #         result.addAction(export_item_action)
        #         break

        def trigger(program_id: str) -> Callable[[], None]:
            return lambda: self.open_item.emit(item, program_id, {})

        if programs := sorted(item.get_supported_programs(), key=lambda x: x.manifest.metadata.name):
            open_with_menu = QMenu(self.tr("Open With"))
            for program in programs:
                action = QAction(text=program.manifest.metadata.name, parent=open_with_menu)
                action.triggered.connect(trigger(program.manifest.metadata.id))
                open_with_menu.addAction(action)
            result.addMenu(open_with_menu)

        if item.hasChildren():
            result.addSeparator()
            view_structures_menu = QMenu(self.tr("View Structures"), result)
            action_vs_child = QAction(text=self.tr("VS_Child"), parent=view_structures_menu)
            action_vs_child.triggered.connect(
                lambda: self.open_item.emit(item, "mircmd:chemistry:molecular_visualizer", {"all": False})
            )
            view_structures_menu.addAction(action_vs_child)
            action_vs_all = QAction(text=self.tr("VS_All"), parent=view_structures_menu)
            action_vs_all.triggered.connect(
                lambda: self.open_item.emit(item, "mircmd:chemistry:molecular_visualizer", {"all": True})
            )
            view_structures_menu.addAction(action_vs_all)
            result.addMenu(view_structures_menu)

        return result

    def _item_double_clicked(self, index: QModelIndex):
        item: Item = cast(Item, self._model.itemFromIndex(index))
        if item.get_default_program():
            self.open_item.emit(item, item.get_default_program(), {})
        else:
            self.setExpanded(index, not self.isExpanded(index))

    def import_file(self, parent: Item) -> None:
        QApplication.instance().project_window.import_files_dialog(parent)

    def add_item(self, item: Item):
        self._model.invisibleRootItem().appendRow(item)

    def expand_top_items(self):
        logger.debug("Expanding top items ...")
        root_item = self._model.invisibleRootItem()
        for i in range(root_item.rowCount()):
            self.setExpanded(self._model.indexFromItem(root_item.child(i)), True)

    def open_auto_open_nodes(self, import_config: ImportFileRulesConfig, is_startup: bool):
        """Open nodes marked for auto-opening after import."""
        root_item = self._model.invisibleRootItem()
        for i in range(root_item.rowCount()):
            self._open_auto_open_nodes(cast(Item, root_item.child(i)), import_config, is_startup)

    def _open_auto_open_nodes(self, item: Item, import_config: ImportFileRulesConfig, is_startup: bool):
        """Recursively open nodes marked with auto_open flag."""
        node = item.project_node
        if node is not None and ActionType.OPEN in node.actions:
            node.actions.remove(ActionType.OPEN)

            should_open = (
                import_config.get_open_on_startup(node.type)
                if is_startup
                else import_config.get_open_on_import(node.type)
            )

            if should_open:
                programs = import_config.get_programs(node.type)
                if len(programs) < 1:
                    if item.default_program:
                        self.open_item.emit(item, item.default_program, {})
                else:
                    for program in programs:
                        if program in item.programs:
                            self.open_item.emit(item, program, {})

        for i in range(item.rowCount()):
            self._open_auto_open_nodes(cast(Item, item.child(i)), import_config, is_startup)
