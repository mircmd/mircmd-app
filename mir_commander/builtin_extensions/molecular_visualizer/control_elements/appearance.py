from typing import TYPE_CHECKING

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout

from mir_commander.builtin_extensions.molecular_visualizer.graphics.utils import color4f_to_qcolor, qcolor_to_color4f
from mir_commander.builtin_extensions.molecular_visualizer.state import MolecularVisualizerState
from mir_commander.builtin_extensions.sdk.base_control_panel import BlockWidget
from mir_commander.sdk.widgets import ColorButton

if TYPE_CHECKING:
    from mir_commander.builtin_extensions.molecular_visualizer.control_panel import MolecularVisualizerControlPanel


class Appearance(BlockWidget[MolecularVisualizerState]):
    def __init__(self, control_panel: "MolecularVisualizerControlPanel"):
        super().__init__()

        self._control_panel = control_panel

        layout = QVBoxLayout(self)

        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel(self.tr("Background color:"), self))
        self._bg_color_button = ColorButton(QColor(255, 255, 255), alpha=False)
        self._bg_color_button.color_changed.connect(self._bg_color_button_color_changed_handler)
        bg_color_layout.addWidget(self._bg_color_button)
        bg_color_layout.addStretch(1)
        layout.addLayout(bg_color_layout)

        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel(self.tr("Style:"), self))
        self._style_combobox = QComboBox()
        self._style_combobox.currentTextChanged.connect(self._style_combobox_current_text_changed_handler)
        style_layout.addWidget(self._style_combobox)
        style_layout.addStretch(1)
        layout.addLayout(style_layout)

        self.setLayout(layout)

    def _bg_color_button_color_changed_handler(self, color: QColor):
        self._control_panel.program_action_signal.emit("appearance.set_bg_color", {"color": qcolor_to_color4f(color)})

    def _style_combobox_current_text_changed_handler(self, text: str):
        self._control_panel.program_action_signal.emit("appearance.set_style", {"name": text})

    def update_values(self, program_state: MolecularVisualizerState):
        with QSignalBlocker(self._bg_color_button), QSignalBlocker(self._style_combobox):
            color = *program_state.background_color[:3], 1.0
            self._bg_color_button.set_color(color4f_to_qcolor(color))

            styles = [self._style_combobox.itemText(i) for i in range(self._style_combobox.count())]
            if styles != program_state.styles:
                self._style_combobox.clear()
                self._style_combobox.addItems(program_state.styles)
            self._style_combobox.setCurrentText(program_state.current_style)
