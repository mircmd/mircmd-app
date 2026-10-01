from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtWidgets import QApplication, QWidget


class NodeChangedAction: ...


class MessageChannel(Enum):
    CONSOLE = "console"
    STATUS = "status"


class BaseProgram(QObject):
    send_message_signal = Signal(MessageChannel, str)
    node_changed_signal = Signal(int, NodeChangedAction)
    update_control_panel_signal = Signal()
    update_window_title_signal = Signal(str)

    def __init__(self, item: QStandardItem):
        super().__init__()
        self.item = item

    @staticmethod
    def get_supported_node_types() -> list[str]:
        raise NotImplementedError

    def get_title(self) -> str:
        return self.item.text()

    def get_icon(self) -> QIcon:
        if icon_path := QApplication.instance().icons.get_icon_path(self.item.get_type()):
            return QIcon(str(icon_path))
        return QIcon(":/core/icons/unknown_node_type.png")

    def get_config(self) -> bytes:
        raise NotImplementedError

    def set_config(self, data: bytes) -> None:
        raise NotImplementedError

    def get_widget(self) -> QWidget:
        raise NotImplementedError

    def get_state(self) -> bytes:
        raise NotImplementedError

    def node_changed_event(self, node_id: int, action: NodeChangedAction) -> None:
        raise NotImplementedError

    def action_event(self, action: str, data: dict[str, Any], instance_index: int) -> None:
        raise NotImplementedError


class BaseControlPanel(QObject):
    program_action_signal = Signal(str, dict)

    def get_widget(self) -> QWidget:
        raise NotImplementedError

    def allows_apply_for_all(self) -> bool:
        raise NotImplementedError

    def update_event(self, program_state: bytes) -> None:
        raise NotImplementedError
