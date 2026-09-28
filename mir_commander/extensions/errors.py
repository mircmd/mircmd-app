from mir_commander.errors import MirCommanderError


class ExtensionsManagerError(MirCommanderError):
    pass


class FileImporterError(ExtensionsManagerError):
    pass


class FileExporterError(ExtensionsManagerError):
    pass
