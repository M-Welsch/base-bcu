from __future__ import annotations

from pathlib import Path
from typing import Optional

from base.common.exceptions import ComponentOffError, SbuCommunicationTimeout, SbuNoResponseError, SbuNotAvailableError
from base.common.logger import LoggerFactory
from base.hardware.sbu.commands import SbuCommand
from base.hardware.sbu.serial_wrapper import SerialWrapper
from base.hardware.sbu.uart_finder import get_sbu_uart_interface

LOG = LoggerFactory.get_logger(__name__)


class SbuMessage:
    def __init__(self, command: SbuCommand, payload: str) -> None:
        self._command: SbuCommand = command
        self._payload: str = payload
        self._retries: int = 3

    @classmethod
    def from_command(cls, command: SbuCommand, payload: str) -> SbuMessage:
        return cls(command=command, payload=payload)

    @property
    def code(self) -> str:
        return self._command.message_code

    @property
    def automatically_free_channel(self) -> bool:
        return self._command.automatically_free_channel

    @property
    def await_acknowledge(self) -> bool:
        return self._command.await_acknowledge

    @property
    def await_response(self) -> bool:
        return self._command.await_response

    @property
    def response_keyword(self) -> str:
        return self._command.response_keyword

    @property
    def await_ready_signal(self) -> bool:
        return self._command.await_ready_signal

    @property
    def payload(self) -> str:
        return self._payload


class SbuCommunicator:
    _sbu_uart_interface: Optional[Path] = None

    def __init__(self) -> None:  # TODO: Move baud_rate to seperate constants file
        if self._sbu_uart_interface is None:
            self._sbu_uart_interface = self._get_uart_interface()

    @staticmethod
    def _get_uart_interface() -> Path:
        try:
            return get_sbu_uart_interface()
        except SbuNotAvailableError as e:
            text = (
                "WARNING! Serial port to SBC could not found!\n"
                "Display and buttons will not work!\n"
                "Shutdown will not work! System must be repowered manually!"
            )
            LOG.error(text)  # TODO: #14
            raise ComponentOffError(text, component="SBU", avoids_shutdown=True) from e

    def process_command(self, command: SbuCommand, payload: str = "") -> Optional[str]:
        message = SbuMessage.from_command(command=command, payload=payload)
        # message = SbuMessage(command=command, payload=payload)
        try:
            sbu_response = self._process_message(message=message)
        except SbuNoResponseError as e:
            raise e
        except SbuCommunicationTimeout as e:
            raise e
        return sbu_response

    def _process_message(self, message: SbuMessage) -> Optional[str]:
        if isinstance(self._sbu_uart_interface, Path):
            with SerialWrapper(
                port=self._sbu_uart_interface,
                baud_rate=9600,
                automatically_free_channel=message.automatically_free_channel,
            ) as ser:
                ser.send_message_to_sbu(f"{message.code}:{message.payload}".encode())
                self._process_acknowledge(message, ser)
                sbu_response = self._process_await_response(message, ser)
                self._process_await_ready_signal(message, ser)
                ser.flush_sbu_channel()
            return sbu_response

    @staticmethod
    def _process_acknowledge(message: SbuMessage, ser: SerialWrapper) -> None:
        if message.await_acknowledge:
            acknowledge_delay, _ = ser.await_acknowledge(message.code)
            LOG.debug(f"{message.code} with payload {message.payload} acknowledged after {acknowledge_delay}s")

    @staticmethod
    def _process_await_response(message: SbuMessage, ser: SerialWrapper) -> Optional[str]:
        if message.await_response:
            response_delay, sbu_response = ser.wait_for_response(message.response_keyword)
            LOG.debug(f", special string received after {response_delay}")
            return sbu_response

    @staticmethod
    def _process_await_ready_signal(message: SbuMessage, ser: SerialWrapper) -> None:
        if message.await_ready_signal:
            ready_delay, _ = ser.wait_for_sbu_ready()
            LOG.debug(f", ready after {ready_delay}")
