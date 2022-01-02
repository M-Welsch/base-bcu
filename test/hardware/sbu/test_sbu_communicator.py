import logging
import sys
from importlib import import_module
from pathlib import Path
from typing import Optional, Type, Union

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from base.common.config import Config

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.common.exceptions import ComponentOffError, SbuCommunicationTimeout, SbuNoResponseError, SbuNotAvailableError
from base.hardware.sbu.commands import SbuCommands
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.serial_interface import SerialInterface


@pytest.mark.parametrize(
    "error, expected",
    [(None, Path()), (SbuNotAvailableError, Path())],
)
def test_get_uart_interface(
    mocker: MockFixture, caplog: LogCaptureFixture, error: Optional[Type[SbuNotAvailableError]], expected: Path
) -> None:
    mocker.patch("base.hardware.sbu.communicator.get_sbu_uart_interface", return_value=expected, side_effect=error)
    if error:
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ComponentOffError):
                SbuCommunicator._get_uart_interface()
        assert "Display and buttons will not work!" in caplog.text
        assert "Shutdown will not work!" in caplog.text
    else:
        assert expected == SbuCommunicator._get_uart_interface()


@pytest.mark.parametrize(
    "payload, error, expected",
    [
        ("", None, None),
        ("", SbuNoResponseError, SbuNoResponseError),
        ("", SbuCommunicationTimeout, SbuCommunicationTimeout),
        ("Something", None, None),
        ("Something", SbuNoResponseError, SbuNoResponseError),
        ("Something", SbuCommunicationTimeout, SbuCommunicationTimeout),
    ],
)
def test_write(
    mocker: MockFixture,
    payload: str,
    error: Optional[Union[Type[SbuNoResponseError], Type[SbuNoResponseError]]],
    expected: Optional[Union[Type[SbuNoResponseError], Type[SbuNoResponseError]]],
) -> None:
    patched_write_to_sbu = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface.write_to_sbu", side_effect=error
    )
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator._get_uart_interface", return_value=Path())

    # the following mocks the SerialInterface context manager
    SerialInterface._config = Config({"wait_for_channel_free_timeout": 1, "serial_connection_timeout": 1})
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_channel_free")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._connect_serial_communication_path")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._establish_serial_connection_or_raise")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.reset_buffers")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.query_from_sbu")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._close_connection")
    command = SbuCommands.test
    if error:
        with pytest.raises(error):
            SbuCommunicator().write(command, payload)
    else:
        SbuCommunicator().write(command, payload)
    assert patched_write_to_sbu.call_count == 1


@pytest.mark.parametrize(
    "payload, error, expected, response",
    [
        ("", None, None, "For Nothing"),
        ("", SbuNoResponseError, SbuNoResponseError, ""),
        ("", SbuCommunicationTimeout, SbuCommunicationTimeout, ""),
        ("Something", None, None, "For Nothing"),
        ("Something", SbuNoResponseError, SbuNoResponseError, ""),
        ("Something", SbuCommunicationTimeout, SbuCommunicationTimeout, ""),
    ],
)
def test_query(
    mocker: MockFixture,
    payload: str,
    error: Optional[Union[Type[SbuNoResponseError], Type[SbuNoResponseError]]],
    expected: Optional[Union[Type[SbuNoResponseError], Type[SbuNoResponseError]]],
    response: str,
) -> None:
    patched_query_from_sbu = mocker.patch(
        "base.hardware.sbu.serial_interface.SerialInterface.query_from_sbu", side_effect=error, return_value=response
    )
    mocker.patch("base.hardware.sbu.communicator.SbuCommunicator._get_uart_interface", return_value=Path())

    # the following mocks the SerialInterface context manager
    SerialInterface._config = Config({"wait_for_channel_free_timeout": 1, "serial_connection_timeout": 1})
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._wait_for_channel_free")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._connect_serial_communication_path")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._establish_serial_connection_or_raise")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.reset_buffers")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface.flush_sbu_channel")
    mocker.patch("base.hardware.sbu.serial_interface.SerialInterface._close_connection")
    command = SbuCommands.test
    if error:
        with pytest.raises(error):
            SbuCommunicator().query(command, payload)
    else:
        response_from_sbu = SbuCommunicator().query(command, payload)
        assert response_from_sbu == response
    assert patched_query_from_sbu.call_count == 1
