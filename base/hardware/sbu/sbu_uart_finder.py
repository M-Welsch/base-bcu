from pathlib import Path
from typing import Generator, Optional

import serial

from base.common.config import Config
from base.common.exceptions import SbuNotAvailableError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class SbuUartFinder:
    def get_sbu_uart_interface(self) -> Optional[Path]:
        uart_interfaces = self._get_available_uart_interfaces()
        uart_sbu = self._test_uart_interfaces_for_echo(uart_interfaces)
        if uart_sbu:
            config = Config("sbu.json", read_only=False)
            config.sbu_uart_interface = str(uart_sbu)
            config.save()
            LOG.info("SBU answers on UART Interface {}".format(uart_sbu))
        else:
            LOG.error("SBU doesn't respond on any UART Interface!")
        return uart_sbu

    @staticmethod
    def _get_available_uart_interfaces() -> Generator[Path, None, None]:
        return Path("/dev").glob("ttyS*")

    def _test_uart_interfaces_for_echo(self, uart_interfaces: Generator[Path, None, None]) -> Optional[Path]:
        for uart_interface in uart_interfaces:
            if self._test_uart_interface_for_echo(uart_interface):
                return uart_interface
        raise SbuNotAvailableError("UART interface not found!")

    @staticmethod
    def _test_uart_interface_for_echo(uart_interface: Path) -> bool:
        try:
            response = SbuUartFinder._challenge_interface(uart_interface)
        except serial.SerialException:
            return False
        else:
            return response.endswith(b"Echo")

    @staticmethod
    def _challenge_interface(uart_interface: Path) -> bytes:
        with serial.Serial(str(uart_interface), 9600, timeout=1) as ser:
            ser.reset_input_buffer()
            ser.write(b"\0")
            ser.write(b"Test\0")
            response = ser.read_until(b"Echo")
            print(f"response: {response}")
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        return response
