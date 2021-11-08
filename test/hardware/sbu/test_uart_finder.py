import sys
from importlib import import_module
from pathlib import Path

import pytest
from pytest_mock import MockFixture

from base.common.config import Config

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from test.hardware.constants import BAUD_RATE, FREE_CHANNEL

from base.hardware.sbu.serial_wrapper import SerialWrapper
from base.hardware.sbu.uart_finder import _challenge_interface


@pytest.mark.skip("Find out how to mock methods of a context manager.")
def test_challenge_interface(mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.__enter__")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.reset_buffers")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.write")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.read_until")
    SerialWrapper._config = Config({"wait_for_channel_free_timeout": 1, "serial_connection_timeout": 1})
    path = Path()
    _challenge_interface(path)
    SerialWrapper.__enter__.assert_called_once_with()
    # SerialWrapper.__init__.assert_called_once_with(path, BAUD_RATE, FREE_CHANNEL)  # Check member variables instead
    # assert SerialWrapper.__enter__.call_count == 1
    assert SerialWrapper.reset_buffers.call_count == 2
    assert SerialWrapper.write.call_count == 2
    SerialWrapper.read_until.assert_called_once_with(b"Echo")
