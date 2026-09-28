import struct


class PostcardReader:
    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0

    def varint(self) -> int:
        value = 0
        shift = 0
        while True:
            byte = self._data[self._offset]
            self._offset += 1
            value |= (byte & 0x7F) << shift
            if byte < 0x80:
                return value
            shift += 7

    def i32(self) -> int:
        n = self.varint()
        return (n >> 1) ^ -(n & 1)

    def f64(self) -> float:
        value = struct.unpack_from("<d", self._data, self._offset)[0]
        self._offset += 8
        return value

    def string(self) -> str:
        length = self.varint()
        end = self._offset + length
        value = self._data[self._offset : end].decode("utf-8")
        self._offset = end
        return value

    def vec(self, read_item):
        return [read_item() for _ in range(self.varint())]
