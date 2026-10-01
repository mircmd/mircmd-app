from typing import TYPE_CHECKING, Any

from mir_commander.builtin_extensions.molecular_visualizer.algebra import Vector3D
from mir_commander.builtin_extensions.molecular_visualizer.consts import VAO_CUBE_RESOURCE_NAME
from mir_commander.builtin_extensions.molecular_visualizer.graphics.scene.node import NodeType
from mir_commander.builtin_extensions.molecular_visualizer.graphics_nodes.base import BaseGraphicsNode

if TYPE_CHECKING:
    from mir_commander.builtin_extensions.molecular_visualizer.graphics_nodes.atom.atom import Atom


class Sphere(BaseGraphicsNode):
    parent: "Atom"

    def __init__(self, radius: float, *args: Any, **kwargs: Any):
        kwargs["model_name"] = VAO_CUBE_RESOURCE_NAME
        kwargs["shader_params"] = {"lighting_model": 1, "render_mode": 3, "ray_casting_object": 1}
        kwargs["scale"] = Vector3D(radius, radius, radius)
        super().__init__(*args, **kwargs | dict(node_type=NodeType.OPAQUE, picking_visible=True))

        self._radius = radius

    @property
    def radius(self) -> float:
        return self._radius

    def set_radius(self, radius: float):
        self._radius = radius
        self.set_scale(Vector3D(radius, radius, radius))

    def set_under_cursor(self, value: bool):
        if value:
            radius = self._radius * 1.15
        else:
            radius = self._radius
        self.set_scale(Vector3D(radius, radius, radius))
        self.parent.update_label_position(radius)

    def get_text(self) -> str:
        atom = self.parent
        return f"Atom: {atom.element_symbol}{atom.index + 1}"

    def toggle_selection(self) -> bool:
        return self.parent.toggle_selection()
