from __future__ import annotations

from base.hardware.sbu.commands import SbuCommand, SbuCommands


class SbuMessage:
    def __init__(self, command: SbuCommand, payload: str = "") -> None:
        self._code: str = command.message_code
        self._payload: str = payload
        self._response_keyword = command.response_keyword
        self._retries: int = 3  # TODO: Use retries

    @property
    def code(self) -> str:
        return self._code

    @property
    def response_keyword(self) -> str:
        return self._response_keyword

    @property
    def binary(self) -> bytes:
        return f"{self.code}:{self._payload}".encode()


class PredefinedSbuMessages:
    test_for_echo = SbuMessage(SbuCommands.test)
    shutdown_request = SbuMessage(SbuCommands.request_shutdown)
