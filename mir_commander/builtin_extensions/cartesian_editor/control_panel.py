from mir_commander.builtin_extensions.cartesian_editor.control_elements.general import General
from mir_commander.builtin_extensions.sdk.base_control_panel import BaseControlPanel, ControlBlock

from mir_commander.builtin_extensions.cartesian_editor.state import CartesianEditorState


class CartesianEditorControlPanel(BaseControlPanel):
    def __init__(self):
        super().__init__()

        self._blocks = [ControlBlock(title=self.tr("General"), widget=General(self), expanded=True)]

    def allows_apply_for_all(self) -> bool:
        return True

    def get_blocks(self) -> list[ControlBlock]:
        return self._blocks

    def update_event(self, program_state: bytes):
        state = CartesianEditorState.deserialize(program_state)

        for block in self._blocks:
            block.widget.update_values(state)

    def set_decimals(self, value: int):
        self.program_action_signal.emit("set_decimals", {"value": value})
