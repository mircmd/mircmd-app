from dataclasses import dataclass
from json import loads
from typing import Self

from mir_commander.builtin_extensions.molecular_visualizer.entities import (
    VolumeCubeIsosurface,
    VolumeCubeIsosurfaceGroup,
)
from mir_commander.builtin_extensions.molecular_visualizer.graphics.utils import Color4f
from mir_commander.builtin_extensions.sdk.base_program_state import BaseProgramState


@dataclass
class CoordinateAxisState:
    axis_color: Color4f
    label_color: Color4f
    label_text: str


@dataclass
class CoordinateAxesState:
    visible: bool
    labels_visible: bool
    both_directions: bool
    at_000: bool
    length: float
    thickness: float
    labels_size: int
    x: CoordinateAxisState
    y: CoordinateAxisState
    z: CoordinateAxisState


@dataclass
class MolecularVisualizerState(BaseProgramState):
    scene_rotation: tuple[float, float, float]
    scene_scale: float
    atom_label_size: int
    atom_label_offset: float
    atom_label_symbol_visible: bool
    atom_label_number_visible: bool
    coordinate_axes: CoordinateAxesState
    background_color: Color4f
    styles: list[str]
    current_style: str
    image_width: int
    image_height: int
    isosurface_groups: list[VolumeCubeIsosurfaceGroup]
    empty_volume_cube_scalar_field: bool

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        values = loads(data.decode("utf-8"))
        values["scene_rotation"] = tuple(values["scene_rotation"])
        values["background_color"] = tuple(values["background_color"])
        axes = values["coordinate_axes"]
        for name in ("x", "y", "z"):
            axis = axes[name]
            axis["axis_color"] = tuple(axis["axis_color"])
            axis["label_color"] = tuple(axis["label_color"])
            axes[name] = CoordinateAxisState(**axis)
        values["coordinate_axes"] = CoordinateAxesState(**axes)
        values["isosurface_groups"] = [
            cls._deserialize_isosurface_group(group) for group in values["isosurface_groups"]
        ]
        return cls(**values)

    @staticmethod
    def _deserialize_isosurface_group(group: dict) -> VolumeCubeIsosurfaceGroup:
        for surface in group["isosurfaces"]:
            surface["color"] = tuple(surface["color"])
        group["isosurfaces"] = [VolumeCubeIsosurface(**surface) for surface in group["isosurfaces"]]
        return VolumeCubeIsosurfaceGroup(**group)
