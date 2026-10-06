from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from mir_commander.extensions.errors import FileExporterError
from mir_commander.extensions.export_format import FileExportFormat
from mir_commander.extensions.file_exporter import FileExporter
from mir_commander.item import Item
from mir_commander.schema_settings_widget import SchemaSettingsWidget
from mir_commander.utils import sanitize_filename


class ExportFileDialog(QDialog):
    def __init__(self, node: Item, file_exporter: FileExporter, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._node = node
        self._file_exporter = file_exporter
        self._settings_widgets: dict[tuple[str, str], SchemaSettingsWidget] = {}
        self._current_settings: SchemaSettingsWidget | None = None
        self.setWindowTitle(self.tr("Export: {}").format(node.text()))
        self.resize(560, 400)
        main_layout = QVBoxLayout(self)
        selection = QGridLayout()
        self._extension_combo_box = QComboBox()
        self._format_combo_box = QComboBox()
        self._file_name_editbox = QLineEdit(str(Path.cwd() / (sanitize_filename(node.text()) or "export")))
        browse = QPushButton(self.tr("Browse..."))
        browse.clicked.connect(self._choose_file)
        selection.addWidget(QLabel(self.tr("Extension:")), 0, 0)
        selection.addWidget(self._extension_combo_box, 0, 1, 1, 2)
        selection.addWidget(QLabel(self.tr("Format:")), 1, 0)
        selection.addWidget(self._format_combo_box, 1, 1, 1, 2)
        selection.addWidget(QLabel(self.tr("Save to:")), 2, 0)
        selection.addWidget(self._file_name_editbox, 2, 1)
        selection.addWidget(browse, 2, 2)
        main_layout.addLayout(selection)
        self._create_settings_area(main_layout)
        self._create_buttons(main_layout)
        self._populate_extensions()

    def _create_settings_area(self, layout: QVBoxLayout):
        self._settings_group = QGroupBox(self.tr("Format parameters"))
        self._settings_layout = QVBoxLayout(self._settings_group)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._settings_group)
        layout.addWidget(scroll)
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)

    def _create_buttons(self, layout: QVBoxLayout):
        buttons = QDialogButtonBox()
        self._export_button = QPushButton(self.tr("Export"))
        buttons.addButton(self._export_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_extensions(self):
        for extension in sorted(
            self._file_exporter.get_exporters(self._node.get_type()), key=lambda ext: ext.manifest.metadata.name
        ):
            self._extension_combo_box.addItem(extension.manifest.metadata.name, extension)
        self._extension_combo_box.currentIndexChanged.connect(self._extension_changed)
        self._format_combo_box.currentIndexChanged.connect(self._format_changed)
        self._extension_changed()

    def _extension_changed(self):
        extension = self._extension_combo_box.currentData()
        self._format_combo_box.blockSignals(True)
        self._format_combo_box.clear()
        if extension is not None:
            for fmt in sorted(
                self._file_exporter.get_formats(extension, self._node.get_type()), key=lambda fmt: fmt.name
            ):
                self._format_combo_box.addItem(fmt.name, fmt)
        self._format_combo_box.blockSignals(False)
        self._format_changed()

    def _format_changed(self):
        if self._current_settings is not None:
            self._current_settings.hide()
        fmt: FileExportFormat | None = self._format_combo_box.currentData()
        self._export_button.setEnabled(fmt is not None)
        self._settings_group.setVisible(fmt is not None and fmt.settings_schema is not None)
        self._error_label.setText(
            "" if fmt is not None else self.tr("No export formats are available for this object.")
        )
        self._current_settings = None
        if fmt is None:
            return
        key = (self._extension_combo_box.currentData().manifest.metadata.id, fmt.id)
        if key not in self._settings_widgets:
            widget = SchemaSettingsWidget(fmt.settings_schema)
            self._settings_widgets[key] = widget
            self._settings_layout.addWidget(widget)
        self._current_settings = self._settings_widgets[key]
        self._current_settings.show()
        path = Path(self._file_name_editbox.text())
        if path.name:
            self._file_name_editbox.setText(str(path.with_suffix("." + fmt.extensions[0])))

    def get_params(self) -> tuple[Path, str, str, dict[str, Any]]:
        if self._current_settings is None:
            raise FileExporterError("No export format selected")
        return (
            Path(self._file_name_editbox.text()).expanduser(),
            self._extension_combo_box.currentData().manifest.metadata.id,
            self._format_combo_box.currentData().id,
            self._current_settings.get_settings(),
        )

    def accept(self):
        try:
            path, extension_id, format_id, settings = self.get_params()
            self._file_exporter.validate_settings(self._format_combo_box.currentData(), settings)
            if not self._file_name_editbox.text().strip() or not path.name or path.is_dir():
                raise FileExporterError(self.tr("Choose an output file"))
            if (
                path.exists()
                and QMessageBox.question(self, self.tr("Replace file?"), self.tr("Replace {}?").format(path))
                != QMessageBox.StandardButton.Yes
            ):
                return
            self._file_exporter.export_file(self._node, extension_id, format_id, path, settings)
        except FileExporterError as error:
            self._error_label.setText(str(error))
            return
        super().accept()

    def _choose_file(self):
        fmt: FileExportFormat | None = self._format_combo_box.currentData()
        name_filter = f"{fmt.name} ({' '.join('*.' + suffix for suffix in fmt.extensions)})" if fmt is not None else ""
        dialog = QFileDialog(self, self.tr("Export"), self._file_name_editbox.text(), name_filter)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setOption(QFileDialog.Option.DontConfirmOverwrite, True)
        if fmt is not None:
            dialog.setDefaultSuffix(fmt.extensions[0])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._file_name_editbox.setText(dialog.selectedFiles()[0])
