from mir_commander.builtin_extensions.molecular_visualizer.graphics.scene.node import Node


class BaseGraphicsNode(Node):
    def set_under_cursor(self, value: bool):
        pass

    def get_text(self) -> str:
        return ""

    def toggle_selection(self) -> bool:
        return False
