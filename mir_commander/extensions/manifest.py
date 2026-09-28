from enum import Enum

from pydantic import BaseModel


class Metadata(BaseModel):
    id: str
    name: str
    version: str
    publisher: str
    description: str


class ExtensionProtocol(str, Enum):
    V1 = "v1"


class ExtensionType(str, Enum):
    ICONS = "icons"
    FILE_IMPORTER = "file_importer"
    FILE_EXPORTER = "file_exporter"
    PROGRAM = "program"


class ExtensionManifest(BaseModel):
    type: ExtensionType
    protocol: ExtensionProtocol
    metadata: Metadata
