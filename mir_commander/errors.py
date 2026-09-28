class MirCommanderError(Exception):
    pass


class ConfigError(MirCommanderError):
    pass


class NetworkError(MirCommanderError):
    pass


class ProgramError(MirCommanderError):
    pass
