import argparse
import os
import platform
import shutil
import sys
from pathlib import Path

from mir_commander import __version__, logging
from mir_commander.application import Application
from mir_commander.consts import DIR, FROZEN
from mir_commander.extensions.errors import ExtensionsManagerError
from mir_commander.extensions.extensions_manager import ExtensionsManager

PLATFORM = platform.system().lower()
logger = logging.getLogger("Main")


def _setup_app_directories():
    for d in (DIR.HOME_MIRCMD, DIR.MIRCMD_BIN, DIR.MIRCMD_EXTENSIONS, DIR.MIRCMD_LOGS):
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)


def _setup_cwd():
    if FROZEN and PLATFORM == "darwin" and Path.cwd() == Path("/"):
        os.chdir(Path.home())


def _setup_cli_commands(install_cli: bool):
    if PLATFORM not in ("darwin", "linux") or FROZEN is False:
        return

    executable = Path(sys.executable)
    if path := shutil.which("mircmd"):
        mircmd = Path(path)
    else:
        mircmd = DIR.MIRCMD_BIN / "mircmd"

    if PLATFORM == "darwin":
        if executable.is_relative_to("/Applications/Mir Commander.app") is False:
            return

        profile = Path.home() / ".profile"
        zshrc = Path.home() / ".zshrc"
        bashrc = Path.home() / ".bashrc"
        for rc in (profile, zshrc, bashrc):
            if rc.exists() and f'export PATH="{DIR.MIRCMD_BIN}:$PATH"' not in rc.read_text():
                with rc.open("a") as f:
                    f.write(f'\nexport PATH="{DIR.MIRCMD_BIN}:$PATH" # Added by Mir Commander App\n')

        if not mircmd.exists():
            os.symlink(executable, mircmd)
    elif PLATFORM == "linux" and "APPIMAGE" in os.environ and install_cli:
        exists = mircmd.exists()
        mircmd.unlink(missing_ok=True)
        os.symlink(Path(os.environ["APPIMAGE"]), mircmd)
        print(f"Symlinked {Path(os.environ['APPIMAGE'])} to {mircmd}")
        if not exists:
            print("Update your PATH environment variable to include the new path.")
            print("For example, in your ~/.profile file, add the following line:")
            print(f'export PATH="{DIR.MIRCMD_BIN}:$PATH"')


def _setup_desktop_integration():
    if PLATFORM != "linux" or FROZEN is False or "APPIMAGE" not in os.environ or "APPDIR" not in os.environ:
        return

    for p in os.environ.get("XDG_DATA_DIRS", "").split(":"):
        part = Path(p)
        if part.is_relative_to(Path.home()):
            icon_file = part / "icons" / "mircmd.png"
            desktop_file = part / "applications" / "mircmd.desktop"
            non_standard = False
            break
    else:
        icon_file = Path.home() / ".icons" / "mircmd.png"
        desktop_file = Path.home() / ".local" / "share" / "applications" / "mircmd.desktop"
        non_standard = True

    icon_file.parent.mkdir(parents=True, exist_ok=True)
    icon_file.unlink(missing_ok=True)
    shutil.copy(Path(os.environ["APPDIR"]) / "mircmd.png", icon_file)

    desktop_file.parent.mkdir(parents=True, exist_ok=True)
    desktop_file.unlink(missing_ok=True)
    shutil.copy(Path(os.environ["APPDIR"]) / "mircmd.desktop", desktop_file)
    desktop_file.write_text(desktop_file.read_text().replace("Exec=mircmd %F", f"Exec={os.environ['APPIMAGE']} %F"))

    print("Desktop integration completed successfully!")
    print(f"Desktop file: {desktop_file}")
    print(f"Icon file: {icon_file}")
    if non_standard:
        print(f"You may need to run 'update-desktop-database {desktop_file.parent}' for the changes to take effect.")
    else:
        print("You may need to run 'update-desktop-database' or log in again for the changes to take effect.")


def main():
    parser = argparse.ArgumentParser(prog="Mir Commander")
    parser.add_argument(
        "files", type=Path, default=[], nargs="*", help="Path to import files. Will be opened in a temporary project."
    )
    parser.add_argument("-p", "--project", type=Path, help="Path to project directory")
    if FROZEN and PLATFORM == "linux":
        parser.add_argument("--install-cli", action="store_true", help="Install CLI commands")
        parser.add_argument("--integrate-desktop", action="store_true", help="Integrate Mir Commander into the desktop")
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}", help="Show version and exit"
    )
    args = parser.parse_args()

    _setup_app_directories()

    logging.setup()

    install_cli = args.install_cli if "install_cli" in args else False
    integrate_desktop = args.integrate_desktop if "integrate_desktop" in args else False
    _setup_cli_commands(install_cli)
    if integrate_desktop:
        _setup_desktop_integration()

    if install_cli or integrate_desktop:
        sys.exit(0)

    logger.debug("Starting Mir Commander ...")

    _setup_cwd()

    extensions_manager = ExtensionsManager()
    try:
        extensions_manager.load_extensions(DIR.MIRCMD_EXTENSIONS)
    except ExtensionsManagerError as e:
        logger.error("Failed to load extensions from %s: %s", DIR.MIRCMD_EXTENSIONS, e)

    app = Application(extensions_manager, [])

    for file in args.files:
        app.project_window.import_file(file)

    sys.exit(app.run())
