from collections.abc import Iterator
from typing import Self

from pydantic import BaseModel, Field, model_validator

from mir_commander.sdk.ui_dsl.widgets.base import Layout, UiItem, ValueWidget, Widget
from mir_commander.sdk.ui_dsl.widgets.button import Button
from mir_commander.sdk.ui_dsl.widgets.checkbox import Checkbox
from mir_commander.sdk.ui_dsl.widgets.color_picker import ColorPicker
from mir_commander.sdk.ui_dsl.widgets.grid_layout import GridItem, GridLayout
from mir_commander.sdk.ui_dsl.widgets.horizontal_layout import HorizontalLayout
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


def _walk(item: UiItem) -> Iterator[UiItem]:
    yield item
    if isinstance(item, Layout):
        for child in item.children():
            yield from _walk(child)


class Root(BaseModel):
    item: ITEMS = Field(..., discriminator="type")

    @model_validator(mode="after")
    def _check_ids(self) -> Self:
        items: dict[str, UiItem] = {}
        for item in _walk(self.item):
            if item.id in items:
                raise ValueError(f"id {item.id!r} is used more than once")
            items[item.id] = item
        for item in items.values():
            if not isinstance(item, Widget):
                continue
            for id in item.collect:
                if id not in items:
                    raise ValueError(f"{item.id!r} collects {id!r}, which does not exist")
                if not isinstance(items[id], ValueWidget):
                    # Pydantic reports only ValueError as a validation error.
                    raise ValueError(f"{item.id!r} collects {id!r}, which has no value")  # noqa: TRY004
        return self
