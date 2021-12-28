from __future__ import annotations

from pathlib import Path
from typing import Optional

from base.common.exceptions import ComponentOffError, SbuCommunicationTimeout, SbuNoResponseError, SbuNotAvailableError
from base.common.logger import LoggerFactory
from base.hardware.constants import BAUD_RATE
from base.hardware.sbu.commands import SbuCommand
from base.hardware.sbu.message import SbuMessage
from base.hardware.sbu.serial_interface import SerialInterface
from base.hardware.sbu.uart_finder import get_sbu_uart_interface

LOG = LoggerFactory.get_logger(__name__)


class SbuCommunicator:
    _sbu_uart_interface: Optional[Path] = None

    def __init__(self) -> None:
        if self._sbu_uart_interface is None:
            self._sbu_uart_interface = self._get_uart_interface()

    @staticmethod
    def _get_uart_interface() -> Path:
        try:
            return get_sbu_uart_interface()
        except SbuNotAvailableError as e:
            text = (
                "WARNING! Serial port to SBU could not found!\n"
                "Display and buttons will not work!\n"
                "Shutdown will not work! System must be repowered manually!"
            )
            LOG.error(text)  # TODO: #14
            raise ComponentOffError(text, component="SBU", avoids_shutdown=True) from e

    def write(self, command: SbuCommand, payload: str = "") -> None:
        message = SbuMessage(command=command, payload=payload)
        if isinstance(self._sbu_uart_interface, Path):
            try:
                with SerialInterface(port=self._sbu_uart_interface, baud_rate=BAUD_RATE) as ser:
                    ser.write_to_sbu(message=message)
            except SbuNoResponseError as e:
                raise e
            except SbuCommunicationTimeout as e:
                raise e

    def query(self, command: SbuCommand, payload: str = "") -> str:
        message = SbuMessage(command=command, payload=payload)
        sbu_response = ""
        if isinstance(self._sbu_uart_interface, Path):
            try:
                with SerialInterface(port=self._sbu_uart_interface, baud_rate=BAUD_RATE) as ser:
                    sbu_response = ser.query_from_sbu(message=message)
            except SbuNoResponseError as e:
                raise e
            except SbuCommunicationTimeout as e:
                raise e
        return sbu_response
