from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from mir_commander.builtin_extensions.molecular_visualizer.control_elements.appearance import Appearance
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.atom_labels import AtomLabels
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.coordinate_axes import CoordinateAxes
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.image import Image
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.view import View
from mir_commander.builtin_extensions.molecular_visualizer.control_elements.volume_cube import VolumeCube
from mir_commander.builtin_extensions.sdk.base_control_panel import BaseControlBlock, BaseControlPanel

if TYPE_CHECKING:
    from mir_commander.builtin_extensions.molecular_visualizer.program import MolecularVisualizerProgram


class MolecularVisualizerControlPanel(BaseControlPanel):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self._blocks = {
            "view": BaseControlBlock(self.tr("View"), View(self), True),
            "atom_labels": BaseControlBlock(self.tr("Atom labels"), AtomLabels(self), False),
            "cubes_and_surfaces": BaseControlBlock(self.tr("Cubes and surfaces"), VolumeCube(self), False),
            "image": BaseControlBlock(self.tr("Image"), Image(self), False),
            "coordinate_axes": BaseControlBlock(self.tr("Coordinate axes"), CoordinateAxes(self), False),
            "appearance": BaseControlBlock(self.tr("Appearance"), Appearance(self), False),
        }

    def allows_apply_for_all(self) -> bool:
        return True

    def get_blocks(self) -> Iterable[BaseControlBlock]:
        return self._blocks.values()

    def update_event(self, program: "MolecularVisualizerProgram", data: dict[Any, Any]):
        if "update_blocks" in data:
            for name in data["update_blocks"]:
                if name in self._blocks:
                    item = self._blocks[name]
                    item.widget.update_values(program)
        else:
            for item in self._blocks.values():
                item.widget.update_values(program)
