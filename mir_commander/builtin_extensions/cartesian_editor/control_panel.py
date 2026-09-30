from typing import TYPE_CHECKING, Any

from mir_commander.builtin_extensions.cartesian_editor.control_elements.general import General
from mir_commander.builtin_extensions.sdk.base_control_panel import BaseControlPanel, ControlBlock

if TYPE_CHECKING:
    from mir_commander.builtin_extensions.cartesian_editor.program import CartesianEditorProgram


class CartesianEditorControlPanel(BaseControlPanel):
    def __init__(self):
        super().__init__()

        self._blocks = [ControlBlock(title=self.tr("General"), widget=General(self), expanded=True)]

    def allows_apply_for_all(self) -> bool:
        return True

    def get_blocks(self) -> list[ControlBlock]:
        return self._blocks

    def update_event(self, program: "CartesianEditorProgram", data: dict[Any, Any]):
        for item in self._blocks:
            item.widget.update_values(program)

    def set_decimals(self, value: int):
        self.program_action_signal.emit("set_decimals", {"value": value})
