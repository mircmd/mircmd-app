from typing import TYPE_CHECKING, cast

from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtWidgets import QApplication

from mir_commander.extensions.extensions_manager import ProgramExtension

if TYPE_CHECKING:
    from mir_commander.application import Application


class Item(QStandardItem):
    _id_counter = 0

    def __init__(self, name: str, type: str, data: bytes):
        super().__init__(name)

        self._data = data
        self._type = type
        self._actions: list[str] = []

        self.setEditable(False)

        Item._id_counter += 1
        self._id = Item._id_counter

        if icon_path := cast("Application", QApplication.instance()).icons.get_icon_path(self._type):
            self.setIcon(QIcon(str(icon_path)))
        else:
            self.setIcon(QIcon(":/core/icons/unknown_node_type.png"))

    def get_id(self) -> int:
        return self._id

    def get_type(self) -> str:
        return self._type

    def get_data(self) -> bytes:
        return self._data

    def get_actions(self) -> list[str]:
        return self._actions

    def get_supported_programs(self) -> list[ProgramExtension]:
        return cast("Application", QApplication.instance()).program.get_supported_programs(self.get_type())

    def get_default_program(self) -> ProgramExtension | None:
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id}, name={self.text()})"
