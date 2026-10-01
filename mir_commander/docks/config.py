from pydantic import BaseModel

from mir_commander.docks.project_dock.config import ProjectDockConfig


class DocksConfig(BaseModel):
    project: ProjectDockConfig = ProjectDockConfig()
