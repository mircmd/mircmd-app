import logging
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from mir_commander.extensions.extensions_manager import ExtensionsManager
from mir_commander.item import Item

logger = logging.getLogger(__name__)


class FileExporter:
    def __init__(self, extensions_manager: ExtensionsManager):
        self._extensions_manager = extensions_manager

    def export_file(self, item: Item, extension_id: str, file_path: Path, params: dict[str, Any]):
        # TODO
        pass


class DefaultProperty(BaseModel):
    type: Literal["property"] = "property"
    value: Literal["node.name", "node.full_name"]


class DefaultLiteral(BaseModel):
    type: Literal["literal"] = "literal"
    value: str | int | float | bool | list[str]


class FormatParamsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["bool", "text", "number", "list"]

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    default: Annotated[DefaultProperty | DefaultLiteral, Field(discriminator="type")]
    required: bool


class BoolParam(FormatParamsConfig):
    type: Literal["bool"] = "bool"


class TextParam(FormatParamsConfig):
    type: Literal["text"] = "text"


class NumberParam(FormatParamsConfig):
    type: Literal["number"] = "number"
    min: int = Field(default=-2147483648)
    max: int = Field(default=2147483647)
    step: int = Field(default=1)


class ListParam(FormatParamsConfig):
    type: Literal["list"] = "list"
    items: list[str] = Field(min_length=1)
