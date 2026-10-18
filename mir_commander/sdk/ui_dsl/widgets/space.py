from typing import Literal

from pydantic import Field

from mir_commander.sdk.ui_dsl.widgets.base import UiItem


class Space(UiItem):
    type: Literal["space"]
    size: int = Field(default=1, ge=1)
