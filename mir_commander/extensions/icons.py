from pathlib import Path

from mir_commander.extensions.extensions_manager import ExtensionsManager


class Icons:
    def __init__(self, extensions_manager: ExtensionsManager):
        self._extensions_manager = extensions_manager

    def get_icon_path(self, icon_id: str) -> Path | None:
        for extension in self._extensions_manager.get_icons():
            if icon_id in extension.icons:
                return extension.path / extension.icons[icon_id]
        return None
