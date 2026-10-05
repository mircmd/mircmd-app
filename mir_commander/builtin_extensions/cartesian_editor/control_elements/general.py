from typing import TYPE_CHECKING

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QGridLayout, QLabel, QSpinBox

from mir_commander.builtin_extensions.cartesian_editor.state import CartesianEditorState
from mir_commander.builtin_extensions.sdk.base_control_panel import BlockWidget

if TYPE_CHECKING:
    from mir_commander.builtin_extensions.cartesian_editor.control_panel import CartesianEditorControlPanel


class General(BlockWidget[CartesianEditorState]):
    def __init__(self, control_panel: "CartesianEditorControlPanel"):
        super().__init__()

        self._control_panel = control_panel

        layout = QGridLayout(self)

        self._decimals_spinbox = QSpinBox()
        self._decimals_spinbox.setRange(1, 15)
        self._decimals_spinbox.setValue(6)
        self._decimals_spinbox.valueChanged.connect(self._control_panel.set_decimals)

        layout.addWidget(QLabel(self.tr("Decimals:")), 0, 0)
        layout.addWidget(self._decimals_spinbox, 0, 1)

        self.setLayout(layout)

    def update_values(self, program_state: CartesianEditorState):
        with QSignalBlocker(self._decimals_spinbox):
            self._decimals_spinbox.setValue(program_state.decimals)
