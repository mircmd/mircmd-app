from re import fullmatch
from typing import Any

from jsonschema.validators import validator_for
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FileExportFormat(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    extensions: list[str] = Field(min_length=1)
    supported_node_types: list[str] = Field(min_length=1)
    settings_schema: dict[str, Any] | None = None

    @field_validator("extensions")
    @classmethod
    def validate_extensions(cls, extensions: list[str]) -> list[str]:
        if any(fullmatch(r"[A-Za-z0-9]+(?:[._+-][A-Za-z0-9]+)*", suffix) is None for suffix in extensions):
            raise ValueError("File extensions must be suffixes without a leading dot or path separators")
        return extensions

    @field_validator("supported_node_types")
    @classmethod
    def validate_node_types(cls, node_types: list[str]) -> list[str]:
        if any(not node_type for node_type in node_types):
            raise ValueError("Object types must not be empty")
        return node_types

    @field_validator("settings_schema")
    @classmethod
    def validate_schema(cls, schema: dict[str, Any] | None) -> dict[str, Any] | None:
        if schema is not None:
            validator_for(schema).check_schema(schema)
            if schema.get("type") != "object":
                raise ValueError("Format settings schema must describe an object")
        return schema
