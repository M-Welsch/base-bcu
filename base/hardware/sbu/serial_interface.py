from __future__ import annotations

from pathlib import Path
from time import sleep, time
from types import TracebackType
from typing import Optional, Tuple, Type

import serial

from base.common.config import Config, get_config
from base.common.constants import BAUD_RATE
from base.common.exceptions import SbuCommunicationTimeout, SbuNoResponseError, SerialInterfaceError
from base.common.logger import LoggerFactory
from base.hardware.pin_interface import PinInterface
from base.hardware.sbu.message import SbuMessage

LOG = LoggerFactory.get_logger(__name__)


class SerialInterface:
    _channel_busy: bool = False
    _sbu_ready: bool = True  # TODO: What for?
    _config: Optional[Config] = None

    def __init__(self, port: Path, baud_rate: int = BAUD_RATE) -> None:
        if SerialInterface._config is None:
            SerialInterface._config = get_config("sbu.json")
        self._port: Path = port
        self._baud_rate: int = baud_rate
        self._serial_connection: Optional[serial.Serial] = None
        self._pin_interface: PinInterface = PinInterface.global_instance()

    def __enter__(self) -> SerialInterface:
        assert isinstance(self._config, Config)
        self._wait_for_channel_free()
        SerialInterface._channel_busy = True
        self._connect_serial_communication_path()
        self._establish_serial_connection_or_raise()
        # self._serial_connection.open() is called implicitly!
        self.flush_sbu_channel()
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        self.flush_sbu_channel()
        self._close_connection()
        self._pin_interface.disable_receiving_messages_from_sbu()
        SerialInterface._channel_busy = False

    def _wait_for_channel_free(self) -> None:
        assert isinstance(self._config, Config)
        channel_timeout: int = self._config.wait_for_channel_free_timeout
        time_start = time()
        while SerialInterface._channel_busy or not SerialInterface._sbu_ready:
            sleep(0.05)
            if time() - time_start > channel_timeout:
                raise SbuCommunicationTimeout(f"Waiting for longer than {channel_timeout} for channel to be free.")

    def _connect_serial_communication_path(self) -> None:
        self._pin_interface.set_sbu_serial_path_to_communication()
        self._pin_interface.enable_receiving_messages_from_sbu()  # Fixme: this is not called when needed!
        sleep(4e-8)  # t_on / t_off max of ADG734 (ensures signal switchover)

    def _establish_serial_connection_or_raise(self) -> None:
        assert isinstance(self._config, Config)
        try:
            self._serial_connection = serial.Serial(
                port=str(self._port), baudrate=self._baud_rate, timeout=self._config.serial_connection_timeout
            )
        except serial.SerialException as e:
            raise SerialInterfaceError("Failed to open serial connection") from e

    def _close_connection(self) -> None:
        if isinstance(self._serial_connection, serial.Serial):
            self._serial_connection.close()

    def reset_buffers(self) -> None:
        if not isinstance(self._serial_connection, serial.Serial):
            raise RuntimeError(f"Use {self.__class__.__name__} as context manager only")
        self._serial_connection.reset_input_buffer()
        self._serial_connection.reset_output_buffer()

    def flush_sbu_channel(self) -> None:
        self._send_message(b"\0")

    def write_to_sbu(self, message: SbuMessage) -> None:
        self._send_message(message=message.binary)
        self._await_acknowledge(message.code)
        self._wait_for_sbu_ready()

    def query_from_sbu(self, message: SbuMessage) -> str:
        self._send_message(message=message.binary)
        self._await_acknowledge(message.code)
        response_delay, response = self._wait_for_response(message.response_keyword)
        LOG.debug(f", response received after {response_delay}")
        self._wait_for_sbu_ready()
        return response

    def _send_message(self, message: bytes) -> None:
        if self._serial_connection is None:
            raise RuntimeError(f"Use {self.__class__.__name__} as context manager only")
        self._serial_connection.write(message)

    def _await_acknowledge(self, message_code: str) -> None:
        acknowledge_delay, _ = self._wait_for_response(f"ACK:{message_code}")
        LOG.debug(f"{message_code} acknowledged after {acknowledge_delay}s")

    def _wait_for_sbu_ready(self) -> None:
        ready_delay, _ = self._wait_for_response("Ready")
        LOG.debug(f", ready after {ready_delay}")
        self.flush_sbu_channel()

    def _wait_for_response(self, response_keyword: str) -> Tuple[float, str]:
        assert isinstance(self._config, Config)
        assert isinstance(self._serial_connection, serial.Serial)
        time_start = time()
        duration: float = 0.0
        while duration < self._config.sbu_response_timeout:
            response: str = self._serial_connection.read_until().decode()
            if response_keyword in response:
                return duration, response.strip("\x00").strip()
            duration = time() - time_start
        raise SbuNoResponseError(f"waiting for {response_keyword} timed out. Took: {duration}")
