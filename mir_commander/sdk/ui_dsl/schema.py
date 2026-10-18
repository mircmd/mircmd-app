from pydantic import BaseModel, Field

from mir_commander.sdk.ui_dsl.widgets.checkbox import Checkbox
from mir_commander.sdk.ui_dsl.widgets.color_picker import ColorPicker
from mir_commander.sdk.ui_dsl.widgets.grid_layout import GridItem, GridLayout
from mir_commander.sdk.ui_dsl.widgets.horizontal_layout import HorizontalLayout
from mir_commander.sdk.ui_dsl.widgets.button import Button
from mir_commander.sdk.ui_dsl.widgets.label import Label
from mir_commander.sdk.ui_dsl.widgets.layout_item import LayoutItem
from mir_commander.sdk.ui_dsl.widgets.number_input_float import NumberInputFloat
from mir_commander.sdk.ui_dsl.widgets.number_input_int import NumberInputInt
from mir_commander.sdk.ui_dsl.widgets.slider import Slider
from mir_commander.sdk.ui_dsl.widgets.space import Space
from mir_commander.sdk.ui_dsl.widgets.table import Table
from mir_commander.sdk.ui_dsl.widgets.text_input import TextInput
from mir_commander.sdk.ui_dsl.widgets.tree import Tree
from mir_commander.sdk.ui_dsl.widgets.vertical_layout import VarticalLayout

ITEMS = (
    Button
    | ColorPicker
    | TextInput
    | Slider
    | NumberInputInt
    | NumberInputFloat
    | Checkbox
    | Label
    | Table
    | Tree
    | GridLayout
    | HorizontalLayout
    | VarticalLayout
)

# Space is only meaningful between items of vertical and horizontal layouts.
BOX_ITEMS = ITEMS | Space

# Layout items refer to ITEMS, which is defined only here, so resolve them now.
for _model in (LayoutItem, GridItem, GridLayout, HorizontalLayout, VarticalLayout):
    _model.model_rebuild(_types_namespace={"ITEMS": ITEMS, "BOX_ITEMS": BOX_ITEMS})


class Root(BaseModel):
    item: ITEMS = Field(..., discriminator="type")
