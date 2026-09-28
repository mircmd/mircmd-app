from typing import TYPE_CHECKING

from PySide6.QtGui import QStandardItemModel

from mir_commander.docks.project_dock.config import ProjectDockConfig
from mir_commander.docks.project_dock.tree_view import TreeView
from mir_commander.sdk.widgets import DockWidget

if TYPE_CHECKING:
    from mir_commander.project_window import ProjectWindow


class ProjectDock(DockWidget):
    """
    The project dock widget.

    A single instance of this class is created
    for showing a tree widget with objects of the project.
    """

    def __init__(self, parent: "ProjectWindow", config: ProjectDockConfig, item_model: QStandardItemModel):
        super().__init__(self.tr("Project"), parent)
        self.project_window = parent

        self.tree = TreeView(item_model, config.tree, self)
        self.setWidget(self.tree)
