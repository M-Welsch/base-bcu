from __future__ import annotations

from pathlib import Path
from typing import Optional

from base.common.constants import BAUD_RATE
from base.common.exceptions import SbuCommunicationTimeout, SbuNoResponseError, SbuNotAvailableError
from base.common.logger import LoggerFactory
from base.hardware.platform import has_sbu
from base.hardware.sbu.commands import SbuCommand
from base.hardware.sbu.message import SbuMessage
from base.hardware.drivers.serial_interface import SerialInterface
from base.hardware.sbu.uart_finder import get_sbu_uart_interface

LOG = LoggerFactory.get_logger(__name__)


class SbuCommunicator:
    _sbu_uart_interface: Optional[Path] = None

    def __init__(self) -> None:
        if has_sbu():
            self.write = self._write_production  # type: ignore
            self.query = self._query_production  # type: ignore
        else:
            self.write = self.__write_mock  # type: ignore
            self.query = self.__query_mock  # type: ignore

    @property
    def available(self) -> bool:
        return self._sbu_uart_interface is not None

    async def _get_uart_interface(self) -> None:
        if self._sbu_uart_interface is None:
            try:
                self._sbu_uart_interface = await get_sbu_uart_interface()
            except SbuNotAvailableError as e:
                LOG.error(  # TODO: #14
                    "WARNING! Serial port to SBU could not found!\n"
                    "Display will not work!\n"
                    "Wakeup will not work! System must be repowered manually!"
                )

    async def write(self, command: SbuCommand, payload: str = "") -> None:
        ...

    async def query(self, command: SbuCommand, payload: str = "") -> str:
        ...

    async def _write_production(self, command: SbuCommand, payload: str = "") -> None:
        await self._get_uart_interface()
        message = SbuMessage(command=command, payload=payload)
        if self._sbu_uart_interface is not None:
            try:
                async with SerialInterface(port=self._sbu_uart_interface, baud_rate=BAUD_RATE) as ser:
                    await ser.write_to_sbu(message=message)
            except SbuNoResponseError as e:
                raise e
            except SbuCommunicationTimeout as e:
                raise e

    async def _query_production(self, command: SbuCommand, payload: str = "") -> str:
        await self._get_uart_interface()
        sbu_response = ""
        if self._sbu_uart_interface is not None:
            message = SbuMessage(command=command, payload=payload)
            try:
                async with SerialInterface(port=self._sbu_uart_interface, baud_rate=BAUD_RATE) as ser:
                    sbu_response = await ser.query_from_sbu(message=message)
            except SbuNoResponseError as e:
                raise e
            except SbuCommunicationTimeout as e:
                raise e
        return sbu_response

    async def __write_mock(self, command: SbuCommand, payload: str = "") -> None:
        ...

    async def __query_mock(self, command: SbuCommand, payload: str = "") -> str:
        if command.message_code == "":
            response = ""
        else:
            response = ""
        return response
