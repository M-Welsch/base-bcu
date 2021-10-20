from __future__ import annotations

from pathlib import Path
from time import sleep, time
from types import TracebackType
from typing import Optional, Tuple, Type

import serial

from base.common.config import BoundConfig, Config
from base.common.exceptions import SbuCommunicationTimeout, SerialWrapperError
from base.common.logger import LoggerFactory
from base.hardware.pin_interface import PinInterface

LOG = LoggerFactory.get_logger(__name__)


class SerialWrapper:
    _channel_busy: bool = False
    _sbu_ready: bool = True  # TODO: What for?
    _config: Optional[Config] = None

    def __init__(
        self, port: Path, automatically_free_channel: bool, baud_rate: int = 9600
    ) -> None:  # TODO: Move baud_rate to seperate constants file
        if SerialWrapper._config is None:
            SerialWrapper._config = BoundConfig("sbu.json")
        self._port: Path = port
        self._automatically_free_channel: bool = automatically_free_channel
        self._baud_rate: int = baud_rate
        self._serial_connection: Optional[serial.Serial] = None

    def __enter__(self) -> SerialWrapper:
        assert isinstance(self._config, Config)
        self._wait_for_channel_free()
        SerialWrapper._channel_busy = True
        self._pin_interface: PinInterface = PinInterface.global_instance()
        self._connect_serial_communication_path()
        try:
            self._serial_connection = serial.Serial(
                port=str(self._port), baudrate=self._baud_rate, timeout=self._config.serial_connection_timeout
            )
        except serial.SerialException as e:
            raise SerialWrapperError("Failed to open serial connection") from e
        # self._serial_connection.open() is called implicitly!
        self.flush_sbu_channel()
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        if self._serial_connection is not None:
            self.flush_sbu_channel()
            self._serial_connection.close()
        self._pin_interface.disable_receiving_messages_from_sbu()
        if self._automatically_free_channel:
            SerialWrapper._channel_busy = False

    @property
    def serial_connection(self) -> serial.Serial:
        return self._serial_connection

    def _connect_serial_communication_path(self) -> None:
        self._pin_interface.set_sbu_serial_path_to_communication()
        self._pin_interface.enable_receiving_messages_from_sbu()  # Fixme: this is not called when needed!

    def flush_sbu_channel(self) -> None:
        self.send_message_to_sbu("\0")

    def send_message_to_sbu(self, message: str) -> None:
        assert isinstance(self._serial_connection, serial.Serial)
        message = message + "\0"
        self._serial_connection.write(message.encode())

    def _wait_for_channel_free(self) -> None:
        assert isinstance(self._config, Config)
        channel_timeout: int = self._config.wait_for_channel_free_timeout
        time_start = time()
        while SerialWrapper._channel_busy or not SerialWrapper._sbu_ready:
            sleep(0.05)
            if time() - time_start > channel_timeout:
                raise SbuCommunicationTimeout(f"Waiting for longer than {channel_timeout} for channel to be free.")

    def await_acknowledge(self, message_code: str) -> Tuple[float, str]:
        return self.wait_for_response(f"ACK:{message_code}")

    def wait_for_sbu_ready(self) -> Tuple[float, str]:
        return self.wait_for_response(f"Ready")

    def wait_for_response(self, response: str) -> Tuple[float, str]:
        assert isinstance(self._config, Config)
        assert isinstance(self._serial_connection, serial.Serial)
        time_start = time()
        while True:
            time_diff = time() - time_start
            tmp: str = self._serial_connection.read_until().decode()
            if response in tmp:
                break
            if time_diff > self._config.sbu_response_timeout:
                raise SbuCommunicationTimeout(f"waiting for {response} took {time_diff}")
        return time_diff, tmp
