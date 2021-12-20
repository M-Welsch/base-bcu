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
from base.common.exceptions import SbuNotAvailableError, SerialWrapperError

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.sbu.serial_wrapper import SerialWrapper
from base.hardware.sbu.uart_finder import (
    _challenge_interface,
    _test_uart_interface_for_echo,
    _test_uart_interfaces_for_echo,
    get_sbu_uart_interface,
)


def test_challenge_interface(mocker: MockFixture) -> None:
    path = Path()
    SerialWrapper._config = Config({"wait_for_channel_free_timeout": 1, "serial_connection_timeout": 1})
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper._wait_for_channel_free")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper._connect_serial_communication_path")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper._establish_serial_connection_or_raise")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.reset_buffers")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.send_message_to_sbu")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.read_until")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.flush_sbu_channel")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper._close_connection")

    _challenge_interface(path)

    SerialWrapper._wait_for_channel_free.assert_called_once_with()  # type: ignore
    SerialWrapper._connect_serial_communication_path.assert_called_once_with()  # type: ignore
    SerialWrapper._establish_serial_connection_or_raise.assert_called_once_with()  # type: ignore
    assert SerialWrapper.reset_buffers.call_count == 2  # type: ignore
    assert SerialWrapper.send_message_to_sbu.call_count == 2  # type: ignore
    SerialWrapper.read_until.assert_called_once_with(b"Echo")  # type: ignore
    assert SerialWrapper.flush_sbu_channel.call_count == 2  # type: ignore
    SerialWrapper._close_connection.assert_called_once_with()  # type: ignore


@pytest.mark.parametrize(
    "response, error, expected",
    [
        (b"Echo", None, True),
        (b"ends with Echo", None, True),
        (b"ends with Echo... not", None, False),
        (b"Something", None, False),
        (None, SerialWrapperError, False),
    ],
)
def test_test_uart_interface_for_echo(
    mocker: MockFixture, response: bytes, error: Optional[Type[SerialWrapperError]], expected: bool
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
