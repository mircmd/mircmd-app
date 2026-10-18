from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from mir_commander.sdk.ui_dsl.widgets.base import Align

if TYPE_CHECKING:
    from mir_commander.sdk.ui_dsl.schema import BOX_ITEMS


class LayoutItem(BaseModel):
    item: "BOX_ITEMS" = Field(..., discriminator="type")
    align: Align = Field(default=Align.Left)
