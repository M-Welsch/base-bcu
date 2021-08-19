from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import sleep, time
from types import TracebackType
from typing import Optional, Tuple, Type

import serial

from base.common.config import Config
from base.common.exceptions import SbuCommunicationTimeout
from base.common.logger import LoggerFactory
from base.hardware.pin_interface import PinInterface
from base.hardware.sbu.sbu_commands import SbuCommand

LOG = LoggerFactory.get_logger(__name__)


class SbuCommunicator:
    _channel_busy: bool = False
    _sbu_ready: bool = True

    def __init__(self, config, baud_rate: int = 9600) -> None:  # TODO: Move baud_rate to seperate constants file
        self._config: Config = config
        self._baud_rate: int = baud_rate
        self._serial_connection: Optional[serial.Serial] = None

    def __enter__(self) -> SbuCommunicator:
        self._pin_interface: PinInterface = PinInterface.global_instance()
        self._connect_serial_communication_path()
        self._serial_connection = serial.Serial(
            port=self._config.sbu_uart_interface,
            baudrate=self._baud_rate,
            timeout=self._config.serial_connection_timeout
        )
        self._serial_connection.open()
        self._flush_sbu_channel()
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        LOG.info("SBU Communicator is terminating. So long and thanks for all the bytes!")
        if self._serial_connection is not None:
            self._flush_sbu_channel()
            self._serial_connection.close()
        self._pin_interface.disable_receiving_messages_from_sbu()

    def _connect_serial_communication_path(self) -> None:
        self._pin_interface.set_sbu_serial_path_to_communication()
        self._pin_interface.enable_receiving_messages_from_sbu()

    def _flush_sbu_channel(self) -> None:
        self._send_message_to_sbu("\0")

    def _send_message_to_sbu(self, message: str) -> None:
        self._wait_for_channel_free()
        message = message + "\0"
        self._serial_connection.write(message.encode())

    def _wait_for_channel_free(self) -> None:
        channel_timeout: int = self._config.wait_for_channel_free_timeout
        time_start = time()
        while self._channel_busy or not self._sbu_ready:
            sleep(0.05)
            if time() - time_start > channel_timeout:
                raise SbuCommunicationTimeout(f"Waiting for longer than {channel_timeout} for channel to be free.")

    def process_command(self, command: SbuCommand, payload: str = "") -> Optional[str]:
        log_message = ""
        sbu_response: Optional[str] = None
        self._channel_busy = True
        try:
            self._send_message_to_sbu(f"{command.message_code}:{payload}")
            if command.await_acknowledge:
                acknowledge_delay, _ = self._await_acknowledge(command.message_code)
                log_message = f"{command.message_code} with payload {payload} acknowledged after {acknowledge_delay}s"
            if command.await_response:
                response_delay, sbu_response = self._wait_for_response(command.response_keyword)
                log_message += f", special string received after {response_delay}"
            if command.await_ready_signal:
                ready_delay, _ = self._wait_for_sbu_ready()
                log_message += f", ready after {ready_delay}"
            # LOG.info(log_message)
        except SbuCommunicationTimeout as e:
            LOG.error(e)
            self._flush_sbu_channel()
        finally:
            if command.automatically_free_channel:
                self._channel_busy = False
        return sbu_response

    def _await_acknowledge(self, message_code: str) -> Tuple[float, str]:
        return self._wait_for_response(f"ACK:{message_code}")

    def _wait_for_sbu_ready(self) -> Tuple[float, str]:
        return self._wait_for_response(f"Ready")

    def _wait_for_response(self, response: str) -> Tuple[float, str]:
        time_start = time()
        while True:
            time_diff = time() - time_start
            tmp: str = self._serial_connection.read_until().decode()
            if response in tmp:
                break
            if time_diff > self._config.sbu_response_timeout:
                raise SbuCommunicationTimeout(f"waiting for {response} took {time_diff}")
        return time_diff, tmp


@dataclass
class CommFlags:
    channel_busy: bool
    sbu_ready: bool
