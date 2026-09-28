from dataclasses import dataclass, field

import numpy as np

from mir_commander.builtin_extensions.utils.postcard_reader import PostcardReader


def _empty_cube_data() -> np.ndarray:
    return np.empty((0, 0, 0), dtype=np.float64)


@dataclass
class VolumeCube:
    """
    Class of 3D volume function represented as a cube of voxels.
    """

    comment1: str = field(default="")
    comment2: str = field(default="")
    box_origin: list[float] = field(default_factory=list)
    steps_number: list[int] = field(default_factory=list)
    steps_size: list[list[float]] = field(default_factory=list)
    cube_data: np.ndarray = field(default_factory=_empty_cube_data)


def _read_cube_data(reader: PostcardReader) -> np.ndarray:
    data = reader.vec(lambda: reader.vec(lambda: reader.vec(reader.f64)))
    if not data:
        return _empty_cube_data()
    return np.asarray(data, dtype=np.float64)


def bytes_to_volume_cube(data: bytes) -> VolumeCube:
    if not data:
        return VolumeCube()

    reader = PostcardReader(data)

    return VolumeCube(
        comment1=reader.string(),
        comment2=reader.string(),
        box_origin=reader.vec(reader.f64),
        steps_number=[reader.varint(), reader.varint(), reader.varint()],
        steps_size=reader.vec(lambda: reader.vec(reader.f64)),
        cube_data=_read_cube_data(reader),
    )
