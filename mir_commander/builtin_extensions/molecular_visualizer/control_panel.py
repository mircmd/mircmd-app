from collections.abc import Iterable
from typing import Any

from mir_commander.builtin_extensions.molecular_visualizer.control_elements.appearance import Appearance
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.atom_labels import AtomLabels
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.coordinate_axes import CoordinateAxes
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.image import Image
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.view import View
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.volume_cube import VolumeCube
from mir_commander.builtin_extensions.molecular_visualizer.state import MolecularVisualizerState
from mir_commander.builtin_extensions.sdk.base_control_panel import BaseControlPanel, ControlBlock


class MolecularVisualizerControlPanel(BaseControlPanel):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__()

        self._blocks = {
            "view": ControlBlock(self.tr("View"), View(self), True),
            "atom_labels": ControlBlock(self.tr("Atom labels"), AtomLabels(self), False),
            "cubes_and_surfaces": ControlBlock(self.tr("Cubes and surfaces"), VolumeCube(self), False),
            "image": ControlBlock(self.tr("Image"), Image(self), False),
            "coordinate_axes": ControlBlock(self.tr("Coordinate axes"), CoordinateAxes(self), False),
            "appearance": ControlBlock(self.tr("Appearance"), Appearance(self), False),
        }

    def allows_apply_for_all(self) -> bool:
        return True

    def get_blocks(self) -> Iterable[ControlBlock]:
        return self._blocks.values()

    def update_event(self, program_state: bytes):
        state = MolecularVisualizerState.deserialize(program_state)

        for block in self._blocks.values():
            block.widget.update_values(state)
