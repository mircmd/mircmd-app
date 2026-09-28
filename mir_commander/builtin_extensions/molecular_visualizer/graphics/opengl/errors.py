from mir_commander.errors import MirCommanderError


class OpenGLError(MirCommanderError):
    pass


class FramebufferError(OpenGLError):
    pass


class RendererError(OpenGLError):
    pass
