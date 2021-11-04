from typing import Any


class Serial:
    response = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def write(self, *args: Any) -> None:
        pass

    def close(self) -> None:
        pass

    @classmethod
    def read_until(cls) -> bytes:
        return cls.response.encode()


class SerialException(Exception):
    pass
