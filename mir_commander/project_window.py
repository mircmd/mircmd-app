import base64
import logging
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QFile, Qt, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMdiSubWindow,
    QMenu,
    QStatusBar,
    QTabWidget,
)

from mir_commander import __version__
from mir_commander.about import About
from mir_commander.app_config import AppConfig, ApplyCallbacks
from mir_commander.docks.console_dock import ConsoleDock
from mir_commander.docks.program_control_panel import ProgramControlPanelDock
from mir_commander.docks.project_dock.project_dock import ProjectDock
from mir_commander.export_item_dialog import ExportFileDialog
from mir_commander.extensions.errors import FileExporterError, FileImporterError
from mir_commander.item import Item
from mir_commander.mdi_area import MdiArea
from mir_commander.project_config import ProjectConfig
from mir_commander.sdk.base_program import MessageChannel
from mir_commander.settings.settings_dialog import SettingsDialog
from mir_commander.updates import ApplicationUpdateDialog, CheckForUpdatesBackgroundWorker, NewVersionNotification

logger = logging.getLogger(__name__)


@dataclass
class Docks:
    project: ProjectDock
    console: ConsoleDock


class ProjectWindow(QMainWindow):
    quit_application_signal = Signal()

    def __init__(self, app_config: AppConfig, app_apply_callbacks: ApplyCallbacks):
        logger.debug("Initializing main window ...")
        super().__init__(None)

        self._item_model = QStandardItemModel()

        self._license_text = self._load_license()

        self._programs_control_panels: dict[str, ProgramControlPanelDock] = {}

        self.app_config = app_config
        self.project_config = ProjectConfig()
        self.config = app_config.project_window
        self.app_apply_callbacks = app_apply_callbacks
        self.apply_callbacks = ApplyCallbacks()

        self.apply_callbacks.add(self._set_mainwindow_title)

        self.setWindowIcon(QIcon(":/core/icons/app.png"))

        self.setup_docks()  # Create docks before menus
        self.setup_mdi_area()
        self.setup_menubar()  # Toolbars and docks must have been already created, so we can populate the View menu.

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self._set_mainwindow_title()

        self.mdi_area.tileSubWindows()

        # Settings
        self._restore_settings()

        self.update_menus(None)

        self.docks.console.append(f"Mir Commander v{__version__}")

        self.status_bar.showMessage(self.tr("Ready"), 10000)

        self._new_version_notification = NewVersionNotification(app_config=self.app_config, parent=self)

        self._check_for_updates_worker = CheckForUpdatesBackgroundWorker(app_config=self.app_config, parent=self)
        self._check_for_updates_worker.start()
        self._check_for_updates_worker.new_version_signal.connect(self._new_version_notification.show_message)

    def _load_license(self) -> str:
        license = QFile(":/core/policy/LICENSE.txt")
        if license.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            return license.readAll().data().decode("utf-8")  # type: ignore[union-attr]
        else:
            logger.error("Failed to open license file: %s", license.errorString())
            return ""

    def import_file(self, file_path: Path, parent: Item | None = None):
        file_importer = QApplication.instance().file_importer
        try:
            logs: list[str] = []

            parent_item = self._item_model.invisibleRootItem() if parent is None else parent
            parent_item.appendRow(file_importer.import_file(file_path))

            # Show import messages in console
            self.docks.console.append(f"Imported file: {file_path}")
            for log in logs:
                self.docks.console.append(log)

            self.status_bar.showMessage(self.tr("File imported successfully"), 3000)
        except FileImporterError as e:
            logger.error("Failed to import file %s: %s", file_path, e)
            self.docks.console.append(self.tr("Error importing file {file_path}: {e}").format(file_path=file_path, e=e))
            self.status_bar.showMessage(self.tr("Failed to import file"), 5000)

    @property
    def programs_control_panels(self) -> dict[str, ProgramControlPanelDock]:
        return self._programs_control_panels

    def setup_mdi_area(self):
        def program_send_message_handler(message_channel: MessageChannel, message: str):
            if message_channel == MessageChannel.CONSOLE:
                self.docks.console.append(message)
            elif message_channel == MessageChannel.STATUS:
                self.status_bar.showMessage(message, 10000)
            else:
                logger.error("Unknown message channel: %s", message_channel)

        self.mdi_area = MdiArea(project_window=self, parent=self)
        self.mdi_area.subWindowActivated.connect(self.update_menus)
        self.mdi_area.program_send_message_signal.connect(program_send_message_handler)
        self.setCentralWidget(self.mdi_area)

        self.docks.project.tree.open_item.connect(self.mdi_area.open_program)

    def setup_docks(self):
        self.setTabPosition(Qt.DockWidgetArea.BottomDockWidgetArea, QTabWidget.TabPosition.North)
        self.setTabPosition(Qt.DockWidgetArea.LeftDockWidgetArea, QTabWidget.TabPosition.West)
        self.setTabPosition(Qt.DockWidgetArea.RightDockWidgetArea, QTabWidget.TabPosition.East)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

        self.docks = Docks(
            ProjectDock(
                parent=self,
                config=self.config.widgets.docks.project,
                item_model=self._item_model,
            ),
            ConsoleDock(parent=self),
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.docks.project)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.docks.console)

    def _set_mainwindow_title(self):
        self.setWindowTitle(self.project_config.name)

    def setup_menubar(self):
        menubar = self.menuBar()
        menubar.addMenu(self._setup_menubar_file())
        menubar.addMenu(self._setup_menubar_view())
        menubar.addMenu(self._setup_menubar_window())
        menubar.addMenu(self._setup_menubar_help())

    def _setup_menubar_file(self) -> QMenu:
        menu = QMenu(self.tr("File"), self)
        menu.addAction(self._import_file_action())
        menu.addSeparator()
        menu.addAction(self._settings_action())
        menu.addAction(self._close_project_action())
        menu.addAction(self._quit_action())
        return menu

    def _setup_menubar_view(self) -> QMenu:
        self._view_menu = QMenu(self.tr("View"), self)
        self._view_menu.addAction(self.docks.project.toggleViewAction())
        self._view_menu.addAction(self.docks.console.toggleViewAction())
        return self._view_menu

    def _setup_menubar_window(self) -> QMenu:
        self._window_actions()
        self._window_menu = QMenu(self.tr("Window"), self)
        self.update_window_menu()
        self._window_menu.aboutToShow.connect(self.update_window_menu)
        return self._window_menu

    def _setup_menubar_help(self) -> QMenu:
        menu = QMenu(self.tr("Help"), self)
        menu.addAction(self._about_action())
        menu.addAction(self._check_for_updates_action())
        return menu

    def _close_project_action(self, checked: bool = False) -> QAction:
        action = QAction(self.tr("Close Project"), self)
        action.triggered.connect(self.close)
        return action

    def _settings_action(self) -> QAction:
        action = QAction(self.tr("Preferences..."), self)
        action.setMenuRole(QAction.MenuRole.PreferencesRole)
        # Settings dialog is actually created here.
        settings_dialog = SettingsDialog(
            parent=self,
            app_apply_callbacks=self.app_apply_callbacks,
            mw_apply_callbacks=self.apply_callbacks,
            app_config=self.app_config,
            project_config=self.project_config,
        )
        action.triggered.connect(settings_dialog.show)
        return action

    def _quit_action(self) -> QAction:
        action = QAction(self.tr("Quit"), self)
        action.setMenuRole(QAction.MenuRole.QuitRole)
        action.setShortcut(QKeySequence.StandardKey.Quit)
        action.triggered.connect(self.quit_application_signal.emit)
        return action

    def _about_action(self) -> QAction:
        action = QAction(self.tr("About Mir Commander"), self)
        action.setMenuRole(QAction.MenuRole.AboutQtRole)
        action.triggered.connect(About(license_text=self._license_text, parent=self).show)
        return action

    def _check_for_updates_action(self) -> QAction:
        action = QAction(self.tr("Check for Updates"), self)
        action.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        action.triggered.connect(ApplicationUpdateDialog(app_config=self.app_config, parent=self).show)
        return action

    def _import_file_action(self) -> QAction:
        action = QAction(self.tr("Import File..."), self)
        action.setShortcut(QKeySequence(self.config.hotkeys.menu_file.import_file))
        action.triggered.connect(lambda: self.import_files_dialog(None))
        return action

    def _window_actions(self):
        self._win_close_act = QAction(text=self.tr("Close"), parent=self, statusTip=self.tr("Close the active window"))
        self._win_close_act.triggered.connect(self.mdi_area.closeActiveSubWindow)

        self._win_close_all_act = QAction(
            text=self.tr("Close All"), parent=self, statusTip=self.tr("Close all the windows")
        )
        self._win_close_all_act.triggered.connect(self.mdi_area.closeAllSubWindows)

        self._win_tile_act = QAction(text=self.tr("Tile"), parent=self, statusTip=self.tr("Tile the windows"))
        self._win_tile_act.triggered.connect(self.mdi_area.tileSubWindows)

        self._win_cascade_act = QAction(text=self.tr("Cascade"), parent=self, statusTip=self.tr("Cascade the windows"))
        self._win_cascade_act.triggered.connect(self.mdi_area.cascadeSubWindows)

        self._win_next_act = QAction(
            text=self.tr("Next"),
            parent=self,
            shortcut=QKeySequence(QKeySequence.StandardKey.NextChild),
            statusTip=self.tr("Move the focus to the next window"),
        )
        self._win_next_act.triggered.connect(self.mdi_area.activateNextSubWindow)

        self._win_previous_act = QAction(
            text=self.tr("Previous"),
            parent=self,
            shortcut=QKeySequence(QKeySequence.StandardKey.PreviousChild),
            statusTip=self.tr("Move the focus to the previous window"),
        )
        self._win_previous_act.triggered.connect(self.mdi_area.activatePreviousSubWindow)

        self._win_separator_act = QAction("", self)
        self._win_separator_act.setSeparator(True)

    def _save_settings(self):
        """Save parameters of main window to settings."""
        self.app_config.project_window.state = self.saveState().toBase64().toStdString()
        self.app_config.project_window.window_state = self.windowState().value
        if self.app_config.project_window.window_state == 0:
            self.app_config.project_window.pos = [self.pos().x(), self.pos().y()]
            self.app_config.project_window.size = [self.size().width(), self.size().height()]

    def _restore_settings(self):
        """Read parameters of main window from settings and apply them."""
        geometry = self.screen().availableGeometry()
        pos = self.app_config.project_window.pos or [int(geometry.width() * 0.125), int(geometry.height() * 0.125)]
        size = self.app_config.project_window.size or [int(geometry.width() * 0.75), int(geometry.height() * 0.75)]
        self.move(*pos)
        self.resize(*size)
        if state := self.app_config.project_window.state:
            self.restoreState(base64.b64decode(state))

    def show(self):
        window_state = Qt.WindowState(self.app_config.project_window.window_state)
        if window_state == Qt.WindowState.WindowMaximized:
            self.showMaximized()
        elif window_state == Qt.WindowState.WindowFullScreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def resizeEvent(self, event):
        self._new_version_notification.update_position()
        super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent):
        logger.info("Closing project ...")
        for control_panel in self._programs_control_panels.values():
            control_panel.visibilityChanged.disconnect()
        self._check_for_updates_worker.stop()
        self._save_settings()
        self.quit_application_signal.emit()
        event.accept()

    @Slot()
    def update_menus(self, window: None | QMdiSubWindow):
        has_mdi_child = window is not None
        self._win_close_act.setEnabled(has_mdi_child)
        self._win_close_all_act.setEnabled(has_mdi_child)
        self._win_tile_act.setEnabled(has_mdi_child)
        self._win_cascade_act.setEnabled(has_mdi_child)
        self._win_next_act.setEnabled(has_mdi_child)
        self._win_previous_act.setEnabled(has_mdi_child)
        self._win_separator_act.setVisible(has_mdi_child)

    def set_active_sub_window(self, window: QMdiSubWindow) -> None:
        if window:
            self.mdi_area.setActiveSubWindow(window)

    def add_program_control_panel(self, program_id: str) -> None | ProgramControlPanelDock:
        if program_id not in self._programs_control_panels:
            program = QApplication.instance().program.get_program(program_id)
            if program.control_panel_cls is None:
                return None
            control_panel = program.control_panel_cls()
            program_control_panel_dock = ProgramControlPanelDock(
                app_config=self.app_config, program_id=program_id, control_panel=control_panel, parent=self
            )
            program_control_panel_dock.setWindowTitle(
                QCoreApplication.translate(program_id, program.manifest.metadata.name)
            )
            control_panel.program_action_signal.connect(
                lambda key, data: self.mdi_area.update_program_event(
                    program_id, program_control_panel_dock.apply_for_all, key, data
                )
            )
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, program_control_panel_dock)
            self._view_menu.addAction(program_control_panel_dock.toggleViewAction())
            self._programs_control_panels[program_id] = program_control_panel_dock
        return self._programs_control_panels[program_id]

    def import_files(self, files: list[Path]):
        pass

    def import_files_dialog(self, parent: Item | None = None):
        """Import files into the current project."""

        dialog = QFileDialog(self, self.tr("Import Files"))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter(self.tr("All files (*)"))

        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            for file_path in dialog.selectedFiles():
                self.import_file(Path(file_path), parent)

    def export_file(self, item: Item):
        file_exporter = QApplication.instance().file_exporter
        dialog = ExportFileDialog(item, file_exporter, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            path, extension_id, format_settings = dialog.get_params()
            try:
                file_exporter.export_file(node=item, extension_id=extension_id, path=path, params=format_settings)
                self.status_bar.showMessage(self.tr("File exported successfully"), 3000)
            except FileExporterError as e:
                logger.error("Failed to export file: %s", e)
                self.docks.console.append(self.tr("Failed to export file: {}").format(e))
                self.status_bar.showMessage(self.tr("Failed to export file"), 5000)

    @Slot()
    def update_window_menu(self):
        self._window_menu.clear()
        self._window_menu.addAction(self._win_close_act)
        self._window_menu.addAction(self._win_close_all_act)
        self._window_menu.addSeparator()
        self._window_menu.addAction(self._win_tile_act)
        self._window_menu.addAction(self._win_cascade_act)
        self._window_menu.addSeparator()
        self._window_menu.addAction(self._win_next_act)
        self._window_menu.addAction(self._win_previous_act)
        self._window_menu.addAction(self._win_separator_act)

        windows = self.mdi_area.subWindowList()
        active_sub_window = self.mdi_area.activeSubWindow()
        self._win_separator_act.setVisible(len(windows) != 0)

        for i, window in enumerate(windows):
            f = window.windowTitle()
            text = f"{i + 1} {f}"
            if i < 9:
                text = "&" + text

            action = self._window_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(window is active_sub_window)
            slot_func = partial(self.set_active_sub_window, window=window)
            action.triggered.connect(slot_func)
