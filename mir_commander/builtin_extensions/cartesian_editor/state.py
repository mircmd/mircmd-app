from dataclasses import dataclass
from mir_commander.builtin_extensions.sdk.base_program_state import BaseProgramState


@dataclass
class CartesianEditorState(BaseProgramState):
    decimals: int
