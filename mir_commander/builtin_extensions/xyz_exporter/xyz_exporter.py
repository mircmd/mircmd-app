from pathlib import Path
from typing import Any

from mir_commander.builtin_extensions.utils.chemistry import atomic_number_to_symbol
from mir_commander.builtin_extensions.utils.data_structures.atomic_coordinates import bytes_to_atomic_coordinates


class XYZExporter:
    def dump(self, data: bytes, file_path: Path, format_params: dict[str, Any]):
        atomic_coordinates = bytes_to_atomic_coordinates(data)

        title = format_params["title"]
        atomic_num: list[int] = atomic_coordinates.atomic_num
        x: list[float] = atomic_coordinates.data.x
        y: list[float] = atomic_coordinates.data.y
        z: list[float] = atomic_coordinates.data.z

        n = len(atomic_num)
        with open(file_path, "w") as f:
            f.write(f"{n}\n")
            f.write(f"{title}\n")
            for i in range(n):
                symbol = atomic_number_to_symbol(atomic_num[i])
                f.write(f"{symbol:<6} {x[i]:>20.14f} {y[i]:>20.14f} {z[i]:>20.14f}\n")
