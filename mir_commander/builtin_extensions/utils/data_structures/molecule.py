from dataclasses import dataclass, field

from mir_commander.builtin_extensions.utils.postcard_reader import PostcardReader


@dataclass
class Molecule:
    n_atoms: int = field(default=0)
    atomic_num: list[int] = field(default_factory=list)
    charge: int = field(default=0)
    multiplicity: int = field(default=1)
    contribution: float = field(default=0.0)


def bytes_to_molecule(data: bytes) -> Molecule:
    if not data:
        return Molecule()

    reader = PostcardReader(data)
    return Molecule(
        n_atoms=reader.i32(),
        atomic_num=reader.vec(reader.i32),
        charge=reader.i32(),
    )
