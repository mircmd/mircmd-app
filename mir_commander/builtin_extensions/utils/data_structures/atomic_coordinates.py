from dataclasses import dataclass, field

from mir_commander.builtin_extensions.utils.postcard_reader import PostcardReader


class AddAtomAction: ...


class NewSymbolAction:
    index: int


class NewPositionAction:
    index: int


class RemoveAtomsAction:
    indices: list[int]


class SwapAtomsIndicesAction:
    index_1: int
    index_2: int


@dataclass
class AtomicCoordinates:
    """
    Class of atomic positions defined as Cartesian coordinates.

    We need this separately because a molecule may have multiple sets of
    geometries, for example as a result of optimization,
    (multidimensional) scans, IRC scans, etc.
    Thus, the basic properties of atoms, common for all possible geometries,
    are collected in the Molecule instance and only the different sets of
    geometries are in separate instances of AtomicCoordinates.
    Note, in a similar manner we may design a class for Z-matrices, etc.
    """

    atomic_num: list[int] = field(default_factory=list)
    x: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)
    z: list[float] = field(default_factory=list)


def bytes_to_atomic_coordinates(data: bytes) -> AtomicCoordinates:
    if not data:
        return AtomicCoordinates()

    reader = PostcardReader(data)

    return AtomicCoordinates(
        atomic_num=reader.vec(reader.i32),
        x=reader.vec(reader.f64),
        y=reader.vec(reader.f64),
        z=reader.vec(reader.f64),
    )
