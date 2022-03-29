from pathlib import Path
from typing import Generator

from base.common.constants import BAUD_RATE
from base.common.exceptions import (
    SbuCommunicationTimeout,
    SbuNoResponseError,
    SbuNotAvailableError,
    SerialInterfaceError,
)
from base.common.logger import LoggerFactory
from base.hardware.sbu.message import PredefinedSbuMessages
from base.hardware.sbu.serial_interface import SerialInterface

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
    except SerialInterfaceError:
        return False
    except SbuNoResponseError:
        return False
    except SbuCommunicationTimeout:
        return False
    else:
        return response.endswith("Echo")


def _challenge_interface(uart_interface: Path) -> str:
    with SerialInterface(port=uart_interface, baud_rate=BAUD_RATE) as ser:
        ser.reset_buffers()
        ser.flush_sbu_channel()
        response = ser.query_from_sbu(message=PredefinedSbuMessages.test_for_echo)
        LOG.debug(f"interface: {str(uart_interface)}, response: {str(response)}")
        ser.reset_buffers()
    return response
