from __future__ import annotations

from pathlib import Path
from typing import Optional

from base.common.exceptions import ComponentOffError, SbuNotAvailableError
from base.common.logger import LoggerFactory
from base.hardware.sbu.sbu_commands import SbuCommand
from base.hardware.sbu.sbu_uart_finder import SbuUartFinder
from base.hardware.sbu.serial_wrapper import SerialWrapper

LOG = LoggerFactory.get_logger(__name__)


class SbuCommunicator:
    _sbu_uart_interface: Optional[Path] = None

    def __init__(self) -> None:  # TODO: Move baud_rate to seperate constants file
        if self._sbu_uart_interface is None:
            self._sbu_uart_interface = self._get_uart_interface()

    @staticmethod
    def _get_uart_interface() -> Path:
        try:
            return SbuUartFinder().get_sbu_uart_interface()
        except SbuNotAvailableError as e:
            text = (
                "WARNING! Serial port to SBC could not found!\n"
                "Display and buttons will not work!\n"
                "Shutdown will not work! System must be repowered manually!"
            )
            LOG.error(text)  # TODO: #14
            raise ComponentOffError(text, component="SBU", avoids_shutdown=True) from e

    def process_command(self, command: SbuCommand, payload: str = "") -> Optional[str]:
        if isinstance(self._sbu_uart_interface, Path):
            log_message = ""
            sbu_response: Optional[str] = None
            with SerialWrapper(
                port=self._sbu_uart_interface,
                baud_rate=9600,
                automatically_free_channel=command.automatically_free_channel,
            ) as ser:
                ser.send_message_to_sbu(f"{command.message_code}:{payload}")
                if command.await_acknowledge:
                    acknowledge_delay, _ = ser.await_acknowledge(command.message_code)
                    log_message = (
                        f"{command.message_code} with payload {payload} acknowledged after {acknowledge_delay}s"
                    )
                if command.await_response:
                    response_delay, sbu_response = ser.wait_for_response(command.response_keyword)
                    log_message += f", special string received after {response_delay}"
                if command.await_ready_signal:
                    ready_delay, _ = ser.wait_for_sbu_ready()
                    log_message += f", ready after {ready_delay}"
                # LOG.info(log_message)
                ser.flush_sbu_channel()
            return sbu_response
        return None
