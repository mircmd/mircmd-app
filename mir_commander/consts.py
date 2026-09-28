import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)


BASE_URL = "https://mircmd.com"


class DIR:
    APP = Path(sys.executable) if FROZEN else Path(__file__).parent.parent
    HOME_MIRCMD = Path.home() / ".config" / "mircmd"
    MIRCMD_BIN = HOME_MIRCMD / "bin"
    MIRCMD_EXTENSIONS = HOME_MIRCMD / "extensions"
    MIRCMD_LOGS = HOME_MIRCMD / "logs"
    INTERNAL_EXTENSIONS = APP / "builtin_extensions"
    RESOURCES = APP / "resources"
