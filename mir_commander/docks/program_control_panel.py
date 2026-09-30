from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QScrollArea, QVBoxLayout

from mir_commander.app_config import AppConfig, ControlPanelState
from mir_commander.sdk.base_program import BaseControlPanel
from mir_commander.sdk.widgets import DockWidget


class ProgramControlPanelDock(DockWidget):
    """
    The program's control panel dock widget.

    A single instance of this class is used for showing widgets with settings for the program.
    """

    def __init__(self, app_config: AppConfig, program_id: str, control_panel: BaseControlPanel, *args, **kwargs):
        self._program_id = program_id

        super().__init__(*args, **kwargs)

        self._app_config = app_config
        self.control_panel = control_panel

        self._apply_for_all = False

        if program_id not in self._app_config.project_window.control_panels:
            self._app_config.project_window.control_panels[program_id] = ControlPanelState()

        self._visible = self._app_config.project_window.control_panels[program_id].visible
        if self._visible:
            # self.show()
            self.setVisible(True)
        else:
            # self.hide()
            self.setVisible(False)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("mircmd-program-control-panel-scroll-area")
        scroll_area.setWidgetResizable(True)
        scroll_area.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        vbox_layout = QVBoxLayout()
        vbox_layout.setContentsMargins(0, 0, 0, 0)
        vbox_layout.setSpacing(0)
        vbox_layout.addWidget(control_panel.get_widget())
        if control_panel.allows_apply_for_all():
            _apply_for_all_checkbox = QCheckBox(self.tr("Apply for all"))
            _apply_for_all_checkbox.setObjectName("mircmd-apply-for-all-checkbox")
            _apply_for_all_checkbox.setChecked(self._apply_for_all)
            _apply_for_all_checkbox.toggled.connect(self._apply_for_all_handler)
            vbox_layout.addWidget(_apply_for_all_checkbox, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox_layout.addStretch(1)

        frame = QFrame(scroll_area)
        frame.setLayout(vbox_layout)
        scroll_area.setWidget(frame)

        self.visibilityChanged.connect(self._visibility_changed_handler)

        self.setWidget(scroll_area)

    def _apply_for_all_handler(self, checked: bool):
        self._apply_for_all = checked

    def _get_name(self) -> str:
        return f"{self.__class__.__name__}.{self._program_id}"

    @property
    def apply_for_all(self) -> bool:
        return self._apply_for_all

    def hide(self):
        visible = self._visible
        with QSignalBlocker(self):
            super().hide()
        self._visible = visible

    def restore_visibility(self):
        with QSignalBlocker(self):
            if self._visible:
                self.show()
            else:
                self.hide()

    def _visibility_changed_handler(self, visible: bool):
        self._visible = visible
        self._app_config.project_window.control_panels[self._program_id].visible = visible
