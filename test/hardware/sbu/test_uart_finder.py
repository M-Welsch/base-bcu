import logging
import sys
from contextlib import nullcontext
from importlib import import_module
from pathlib import Path
from typing import ContextManager, Generator, Optional, Type, Union
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.python_api import RaisesContext
from pytest_mock import MockFixture

from base.common.config import Config
from base.common.exceptions import SbuNotAvailableError, SerialInterfaceError

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.sbu.message import PredefinedSbuMessages
from base.hardware.sbu.serial_interface import SerialInterface
from base.hardware.sbu.uart_finder import (
    _challenge_interface,
    _test_uart_interface_for_echo,
    _test_uart_interfaces_for_echo,
    get_sbu_uart_interface,
)


def test_challenge_interface(mocker: MockFixture) -> None:
    path = Path()
    SerialInterface._config = Config({"wait_for_channel_free_timeout": 1, "serial_connection_timeout": 1})
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_channel_free")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._connect_serial_communication_path")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._establish_serial_connection_or_raise")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.reset_buffers")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.query_from_sbu")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._close_connection")

    _challenge_interface(path)

    SerialInterface._wait_for_channel_free.assert_called_once_with()  # type: ignore
    SerialInterface._connect_serial_communication_path.assert_called_once_with()  # type: ignore
    SerialInterface._establish_serial_connection_or_raise.assert_called_once_with()  # type: ignore
    assert SerialInterface.reset_buffers.call_count == 2  # type: ignore
    SerialInterface.query_from_sbu.assert_called_once_with(message=PredefinedSbuMessages.test_for_echo)  # type: ignore
    assert SerialInterface.flush_sbu_channel.call_count == 3  # type: ignore
    SerialInterface._close_connection.assert_called_once_with()  # type: ignore


@pytest.mark.parametrize(
    "response, error, expected",
    [
        ("Echo", None, True),
        ("ends with Echo", None, True),
        ("ends with Echo... not", None, False),
        ("Something", None, False),
        (None, SerialInterfaceError, False),
    ],
)
def test_test_uart_interface_for_echo(
    mocker: MockFixture, response: bytes, error: Optional[Type[SerialInterfaceError]], expected: bool
) -> None:
    mocker.patch("base.hardware.sbu.uart_finder._challenge_interface", return_value=response, side_effect=error)
    assert _test_uart_interface_for_echo(Path()) == expected


@pytest.mark.parametrize(
    "uart_interfaces, expected, error",
    [
        ((p for p in [Path("X"), Path(), Path()]), Path("X"), nullcontext()),
        ((p for p in [Path(), Path("X"), Path()]), Path("X"), nullcontext()),
        ((p for p in [Path(), Path(), Path("X")]), Path("X"), nullcontext()),
        ((p for p in [Path("X"), Path("X"), Path("X")]), Path("X"), nullcontext()),
        ((p for p in [Path(), Path(), Path()]), Mock(), pytest.raises(SbuNotAvailableError)),
    ],
)
def test_test_uart_interfaces_for_echo(
    mocker: MockFixture,
    uart_interfaces: Generator[Path, None, None],
    expected: Path,
    error: Union[ContextManager[None], RaisesContext[SbuNotAvailableError]],
) -> None:
    mocker.patch("base.hardware.sbu.uart_finder._test_uart_interface_for_echo", side_effect=lambda x: x == Path("X"))
    with error:
        assert _test_uart_interfaces_for_echo(uart_interfaces) == expected


def test_get_sbu_uart_interface(mocker: MockFixture, caplog: LogCaptureFixture) -> None:
    target = Path("X")
    mocker.patch("base.hardware.sbu.uart_finder._test_uart_interfaces_for_echo", side_effect=lambda interfaces: target)
    with caplog.at_level(logging.INFO):
        assert get_sbu_uart_interface() == target
    assert str(target) in caplog.text
