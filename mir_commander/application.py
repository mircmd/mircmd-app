import logging

from PySide6.QtCore import QFile, QLocale, QResource, Qt, QTranslator
from PySide6.QtGui import QColor, QFont, QFontDatabase, QOpenGLContext, QPalette, QSurfaceFormat
from PySide6.QtWidgets import QApplication, QMessageBox

from mir_commander.app_config import AppConfig, ApplyCallbacks
from mir_commander.consts import DIR
from mir_commander.extensions.extensions_manager import ExtensionsManager
from mir_commander.extensions.file_exporter import FileExporter
from mir_commander.extensions.file_importer import FileImporter
from mir_commander.extensions.icons import Icons
from mir_commander.extensions.program import Program
from mir_commander.project_window import ProjectWindow

logger = logging.getLogger(__name__)


class Application(QApplication):
    def __init__(self, extensions_manager: ExtensionsManager, *args, **kwargs):
        self.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, on=False)
        super().__init__(*args, **kwargs)
        self.setApplicationName("mir_commander")
        self.setApplicationDisplayName("Mir Commander")
        self.setAttribute(Qt.ApplicationAttribute.AA_DontShowShortcutsInContextMenus, on=False)
        self._quitting = False

        self.extensions_manager = extensions_manager
        self.icons = Icons(self.extensions_manager)
        self.file_importer = FileImporter(self.extensions_manager)
        self.file_exporter = FileExporter(self.extensions_manager)
        self.program = Program(self.extensions_manager)

        self._apply_callbacks = ApplyCallbacks()
        self._config: AppConfig = AppConfig.load(DIR.HOME_MIRCMD / "config.yaml")

        if self._config.language != "system":
            QLocale.setDefault(QLocale(self._config.language))

        self._register_resources()

        self._set_translation()

        self._error = QMessageBox()
        self._error.setIcon(QMessageBox.Icon.Critical)

        self.setStyle("Fusion")

        self._setup_opengl()
        self._fix_palette()
        self._load_fonts()
        self._set_stylesheet()

        self.project_window = ProjectWindow(
            app_config=self._config,
            app_apply_callbacks=self._apply_callbacks,
        )
        self.project_window.quit_application_signal.connect(self.close_app)

    def _setup_opengl(self):
        context = QOpenGLContext()
        fmt = QSurfaceFormat()
        fmt.setVersion(4, 6)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        context.setFormat(fmt)
        context.create()
        version = context.format().version()

        sf = QSurfaceFormat()
        sf.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        sf.setVersion(*version)
        sf.setColorSpace(QSurfaceFormat.ColorSpace.sRGBColorSpace)
        QSurfaceFormat.setDefaultFormat(sf)

    def _fix_palette(self):
        """
        PySide6 may work bad if GTK3 theme engine is active with builtin themes Adwaita, Adwaita-dark and High-Contrast.
        In this case text labels (window text) of many different (QLabel, etc) Qt widgets is shown as if it were
        disabled. This behavior has been seen in Debian 11, 12 with XFCE at least as of 19.06.2023.
        The problem is detected by checking current colors for active and disabled QPalette.WindowText.
        You may want to add more checking if the current way is too generic.
        It is also possible, that the bug will be fixed at some point in Adwaita, so we will not need this hack anymore.
        """
        palette = self.palette()
        color_windowtext = palette.color(QPalette.ColorRole.WindowText)
        color_disabledwindowtext = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText)

        # This combination is specific to Adwaita and High-Contrast:
        if (
            color_windowtext.red() == 146
            and color_windowtext.green() == 149
            and color_windowtext.blue() == 149
            and color_disabledwindowtext.red() == 73
            and color_disabledwindowtext.green() == 74
            and color_disabledwindowtext.blue() == 74
        ):
            palette.setColor(QPalette.ColorRole.WindowText, QColor(46, 52, 54))
            self.setPalette(palette)
        # specific to Adwaita-dark:
        elif (
            color_windowtext.red() == 145
            and color_windowtext.green() == 145
            and color_windowtext.blue() == 144
            and color_disabledwindowtext.red() == 72
            and color_disabledwindowtext.green() == 72
            and color_disabledwindowtext.blue() == 72
        ):
            palette.setColor(QPalette.ColorRole.WindowText, QColor(238, 238, 236))
            self.setPalette(palette)

    def _register_resources(self):
        print(DIR.RESOURCES)
        for file in DIR.RESOURCES.glob("*.rcc"):
            if QResource.registerResource(str(file)) is False:
                logger.error("Failed to register resource %s", file)

    def _set_translation(self):
        locale = QLocale()
        translator = QTranslator(self)
        if translator.load(locale, "", "", ":/core/i18n"):
            if not self.installTranslator(translator):
                logger.error("Failed to install translator for language %s", locale.name())
        else:
            logger.error("Failed to load translator for language %s", locale.name())

    def _load_fonts(self):
        font_family_map = {"inter": ":/core/fonts/Inter.ttf"}

        if self._config.font.family == "system":
            return

        if self._config.font.family in font_family_map:
            font_id = QFontDatabase.addApplicationFont(font_family_map[self._config.font.family])
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font_family = font_families[0]
                    font = QFont(font_family)
                    font.setPixelSize(self._config.font.size)
                    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
                    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
                    self.setFont(font)
                else:
                    logger.error(
                        "Failed to get font family from font file: %s", font_family_map[self._config.font.family]
                    )
            else:
                logger.error("Failed to open font file: %s", font_family_map[self._config.font.family])
        else:
            logger.warning("Font family '%s' not found, using system font", self._config.font.family)

    def _set_stylesheet(self):
        font_stylesheet = f"""
            QLabel, QTreeView, QTableView, QListView, QCheckBox, QPushButton, QLineEdit, QSpinBox, QMenu, QMenuBar, QDoubleSpinBox, QComboBox, QDockWidget, QHeaderView::section, QTabBar::tab {{
                font-size: {self._config.font.size}px;
            }}

            QStatusBar, QPlainTextEdit {{
                font-size: {self._config.font.size - 1}px;
            }}

            QGroupBox {{
                font-size: {self._config.font.size - 2}px;
            }}
        """

        about_stylesheet = f"""
            QLabel#mircmd-about-title-label {{
                font-size: {self._config.font.size + 3}px;
            }}

            QLabel#mircmd-about-version-label {{
                font-size: {self._config.font.size - 2}px;
            }}
        """
        styles = QFile(":/core/styles/stylesheets.qss")
        if styles.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stylesheet = styles.readAll().data().decode("utf-8")  # type: ignore[union-attr]
            self.setStyleSheet(
                stylesheet + about_stylesheet + ("" if self._config.font.family == "system" else font_stylesheet)
            )
            styles.close()
        else:
            logger.error("Failed to open stylesheet file: %s", styles.errorString())

    def run(self) -> int:
        self.project_window.show()
        return self.exec()

    def close_app(self):
        self._quitting = True
        self.project_window.close()
        self._config.dump()
        self.quit()
