from pathlib import Path
from typing import Generator, Optional

from base.common.exceptions import SbuNotAvailableError, SerialWrapperError
from base.common.logger import LoggerFactory
from base.hardware.sbu.serial_wrapper import SerialWrapper

LOG = LoggerFactory.get_logger(__name__)


class SbuUartFinder:
    def get_sbu_uart_interface(self) -> Optional[Path]:
        uart_interfaces = self._get_available_uart_interfaces()
        uart_sbu = self._test_uart_interfaces_for_echo(uart_interfaces)
        if uart_sbu:
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
        except SerialWrapperError:
            return False
        else:
            return response.endswith(b"Echo")

    @staticmethod
    def _challenge_interface(uart_interface: Path) -> bytes:
        with SerialWrapper(port=uart_interface, baud_rate=9600, automatically_free_channel=True) as ser:
            ser.serial_connection.reset_input_buffer()
            ser.serial_connection.reset_output_buffer()
            ser.serial_connection.write(b"\0")
            ser.serial_connection.write(b"Test\0")
            response = ser.serial_connection.read_until(b"Echo")
            print(f"interface: {str(uart_interface)}, response: {response}")
            ser.serial_connection.reset_input_buffer()
            ser.serial_connection.reset_output_buffer()
        return response
