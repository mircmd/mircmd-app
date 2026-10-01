from mir_commander.builtin_extensions.molecular_visualizer.graphics.scene.node import Node, NodeType
from mir_commander.builtin_extensions.molecular_visualizer.graphics.scene.rendering_container import RenderingContainer
from mir_commander.builtin_extensions.molecular_visualizer.graphics.scene.root_node import RootNode
from mir_commander.builtin_extensions.molecular_visualizer.graphics.transform import Transform


class Scene:
    __slots__ = ("_root_node", "_main_node", "transform")

    def __init__(self):
        self._root_node = RootNode()
        self._main_node = Node(node_type=NodeType.CONTAINER, root_node=self._root_node)

        self.transform = Transform()

    @property
    def root_node(self) -> RootNode:
        return self._root_node

    @property
    def main_node(self) -> Node:
        return self._main_node

    @property
    def containers(self) -> tuple[dict[NodeType, RenderingContainer], RenderingContainer, RenderingContainer]:
        return self._root_node.containers

    def find_node_by_picking_id(self, picking_id: int) -> Node:
        return self._root_node.find_node_by_picking_id(picking_id)

    def clear(self):
        self._root_node.clear()

    def __repr__(self):
        return f"Scene(root_node={self._root_node})"
