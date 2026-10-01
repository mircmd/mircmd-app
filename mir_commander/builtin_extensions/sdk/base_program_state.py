from typing import Self
from dataclasses import dataclass, asdict
from json import dumps, loads


@dataclass
class BaseProgramState:
    def serialize(self) -> bytes:
        return dumps(asdict(self), ensure_ascii=False).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        return cls(**loads(data.decode("utf-8")))
