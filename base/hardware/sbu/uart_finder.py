from pathlib import Path
from test.hardware.constants import BAUD_RATE, FREE_CHANNEL
from typing import Generator

from base.common.exceptions import SbuNotAvailableError, SerialWrapperError
from base.common.logger import LoggerFactory
from base.hardware.sbu.serial_wrapper import SerialWrapper

LOG = LoggerFactory.get_logger(__name__)


def get_sbu_uart_interface() -> Path:
    uart_interfaces = Path("/dev").glob("ttyS*")
    uart_sbu = _test_uart_interfaces_for_echo(uart_interfaces)
    LOG.info("SBU answers on UART Interface {}".format(uart_sbu))
    return uart_sbu


def _test_uart_interfaces_for_echo(uart_interfaces: Generator[Path, None, None]) -> Path:
    for uart_interface in uart_interfaces:
        if _test_uart_interface_for_echo(uart_interface):
            return uart_interface
    raise SbuNotAvailableError("UART interface not found!")


def _test_uart_interface_for_echo(uart_interface: Path) -> bool:
    try:
        response = _challenge_interface(uart_interface)
    except SerialWrapperError:
        return False
    else:
        return response.endswith(b"Echo")


def _challenge_interface(uart_interface: Path) -> bytes:
    with SerialWrapper(port=uart_interface, baud_rate=BAUD_RATE, automatically_free_channel=FREE_CHANNEL) as ser:
        ser.reset_buffers()
        ser.write(b"\0")
        ser.write(b"Test\0")
        response: bytes = ser.read_until(b"Echo")
        LOG.debug(f"interface: {str(uart_interface)}, response: {str(response)}")
        ser.reset_buffers()
    return response
