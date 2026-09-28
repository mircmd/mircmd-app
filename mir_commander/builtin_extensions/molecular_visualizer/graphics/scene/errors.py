from mir_commander.errors import MirCommanderError


class SceneError(MirCommanderError):
    pass


class NodeError(SceneError):
    pass


class NodeParentError(SceneError):
    pass


class NodeNotFoundError(SceneError):
    pass
