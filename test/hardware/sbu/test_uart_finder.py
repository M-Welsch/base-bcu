import sys
from importlib import import_module
from pathlib import Path

from pytest_mock import MockFixture

from base.common.config import Config

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.sbu.serial_wrapper import SerialWrapper
from base.hardware.sbu.uart_finder import _challenge_interface


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
