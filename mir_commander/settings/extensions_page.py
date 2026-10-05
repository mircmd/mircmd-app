from typing import TYPE_CHECKING, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QBoxLayout, QTableView, QVBoxLayout

from mir_commander.extensions.extensions_manager import Extension
from mir_commander.settings.base import BasePage

if TYPE_CHECKING:
    from mir_commander.application import Application


class Extensions(BasePage):
    """The page with extensions information.

    Displays a table with all registered extensions and their metadata.
    """

    def setup_ui(self) -> QBoxLayout:
        layout = QVBoxLayout()

        self._table = QTableView()
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self._model = QStandardItemModel()
        self._table.setModel(self._model)

        layout.addWidget(self._table)

        return layout

    def setup_data(self):
        self._populate_table()

    def _populate_table(self):
        extensions_manager = cast("Application", QApplication.instance()).extensions_manager
        self._model.clear()

        headers = [
            self.tr("Name"),
            self.tr("Type"),
            self.tr("Version"),
            self.tr("Publisher"),
            self.tr("Enabled"),
        ]
        self._model.setHorizontalHeaderLabels([h for h in headers])

        extensions: list[tuple[Extension, str]] = []

        for importer in extensions_manager.get_file_importers():
            extensions.append((importer, self.tr("File Importer")))

        for exporter in extensions_manager.get_file_exporters():
            extensions.append((exporter, self.tr("File Exporter")))

        for program in extensions_manager.get_programs():
            extensions.append((program, self.tr("Program")))

        for icon in extensions_manager.get_icons():
            extensions.append((icon, self.tr("Icons")))

        for extension, extension_type in extensions:
            metadata = extension.manifest.metadata

            name_item = QStandardItem(metadata.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            type_item = QStandardItem(extension_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            version_item = QStandardItem(metadata.version)
            version_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            publisher_item = QStandardItem(metadata.publisher)
            publisher_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            enabled_item = QStandardItem(self.tr("Yes") if extension.enabled else self.tr("No"))
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            self._model.appendRow([name_item, type_item, version_item, publisher_item, enabled_item])

        self._table.resizeColumnsToContents()
