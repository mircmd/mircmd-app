import logging
from pathlib import Path
from typing import Protocol

import mir_commander_file_importer_host
from mir_commander.extensions.errors import FileImporterError
from mir_commander.extensions.extensions_manager import ExtensionsManager
from mir_commander.item import Item

logger = logging.getLogger(__name__)


class _ImportNode(Protocol):
    id: int
    name: str
    type_id: str
    data: bytes
    children: list[int]


class _ImportTree(Protocol):
    root: int
    nodes: list[_ImportNode]


class FileImporter:
    def __init__(self, extensions_manager: ExtensionsManager):
        self._extensions_manager = extensions_manager

    def import_file(self, file_path: Path) -> Item:
        for extension in self._extensions_manager.get_file_importers():
            try:
                tree = mir_commander_file_importer_host.load(str(extension.wasm_path), str(file_path))
            except RuntimeError as error:
                logger.error("Failed to import file %s: %s", file_path, error)
                continue
            except AttributeError as error:
                raise FileImporterError(str(error))
            return _item_from_import_tree(tree)

        raise FileImporterError("No file importers found")


def _index_import_nodes(nodes: list[_ImportNode]) -> dict[int, _ImportNode]:
    index: dict[int, _ImportNode] = {}
    for node in nodes:
        if node.id in index:
            raise FileImporterError(f"Duplicate node id {node.id}")
        index[node.id] = node
    return index


def _item_from_import_id(node_id: int, index: dict[int, _ImportNode], seen: set[int]) -> Item:
    if node_id in seen:
        raise FileImporterError(f"Cycle at node {node_id}")

    source = index.get(node_id)
    if source is None:
        raise FileImporterError(f"Missing node {node_id}")

    seen.add(node_id)
    item = Item(name=source.name, type=source.type_id, data=bytes(source.data))
    for child_id in source.children:
        item.appendRow(_item_from_import_id(child_id, index, seen))
    return item


def _item_from_import_tree(tree: _ImportTree) -> Item:
    return _item_from_import_id(tree.root, _index_import_nodes(tree.nodes), set())
