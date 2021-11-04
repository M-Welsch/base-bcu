import sys
from importlib import import_module
from pathlib import Path
from test.fake_libs.serial_mock import Serial
from typing import Generator

import pytest
from pytest_mock import MockFixture

from base.common.config import Config
from base.common.exceptions import SbuCommunicationTimeout

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")
sys.modules["serial"] = import_module("test.fake_libs.serial_mock")

from base.hardware.sbu.serial_wrapper import SerialWrapper


@pytest.fixture()
def serial_wrapper() -> Generator[SerialWrapper, None, None]:
    SerialWrapper._config = Config(
        {"sbu_response_timeout": 0.001, "wait_for_channel_free_timeout": 0.001, "serial_connection_timeout": 1}
    )
    yield SerialWrapper(port=Path(), automatically_free_channel=True, baud_rate=5678)


def test_setup_teardown(serial_wrapper: SerialWrapper, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.pin_interface.PinInterface.set_sbu_serial_path_to_communication")
    mocker.patch("base.hardware.pin_interface.PinInterface.enable_receiving_messages_from_sbu")
    mocker.patch("base.hardware.pin_interface.PinInterface.disable_receiving_messages_from_sbu")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper._wait_for_channel_free")
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.flush_sbu_channel")
    with serial_wrapper as wrapper:
        wrapper._wait_for_channel_free.assert_called_once_with()  # type: ignore
        wrapper._pin_interface.set_sbu_serial_path_to_communication.assert_called_once_with()  # type: ignore
        wrapper._pin_interface.enable_receiving_messages_from_sbu.assert_called_once_with()  # type: ignore
        wrapper.flush_sbu_channel.assert_called_once_with()  # type: ignore
    wrapper._pin_interface.disable_receiving_messages_from_sbu.assert_called_once_with()  # type: ignore
    assert wrapper.flush_sbu_channel.call_count == 2  # type: ignore


def test_send_message_to_sbu(serial_wrapper: SerialWrapper, mocker: MockFixture) -> None:
    mocker.patch("serial.Serial.write")
    with serial_wrapper as wrapper:
        assert isinstance(wrapper._serial_connection, Serial)
        wrapper._serial_connection.write.assert_called_once_with(b"\x00\x00")
        wrapper._serial_connection.write.reset_mock()
        wrapper.send_message_to_sbu("Message in a bottle?")
        wrapper._serial_connection.write.assert_called_once_with(b"Message in a bottle?\x00")


def test_wait_for_channel_free__n_busy_n_ready(serial_wrapper: SerialWrapper) -> None:
    SerialWrapper._channel_busy = False
    SerialWrapper._sbu_ready = False
    with pytest.raises(SbuCommunicationTimeout):
        serial_wrapper._wait_for_channel_free()


def test_wait_for_channel_free__n_busy_ready(serial_wrapper: SerialWrapper) -> None:
    SerialWrapper._channel_busy = False
    SerialWrapper._sbu_ready = True
    serial_wrapper._wait_for_channel_free()


def test_wait_for_channel_free__busy_n_ready(serial_wrapper: SerialWrapper) -> None:
    SerialWrapper._channel_busy = True
    SerialWrapper._sbu_ready = False
    with pytest.raises(SbuCommunicationTimeout):
        serial_wrapper._wait_for_channel_free()


def test_wait_for_channel_free__busy_ready(serial_wrapper: SerialWrapper) -> None:
    SerialWrapper._channel_busy = True
    SerialWrapper._sbu_ready = True
    with pytest.raises(SbuCommunicationTimeout):
        serial_wrapper._wait_for_channel_free()


def test_wait_for_response_timeout(serial_wrapper: SerialWrapper) -> None:
    with pytest.raises(SbuCommunicationTimeout):
        with serial_wrapper as wrapper:
            wrapper.wait_for_response("")


def test_wait_for_response(serial_wrapper: SerialWrapper) -> None:
    SerialWrapper._channel_busy = False
    SerialWrapper._sbu_ready = True
    response = "response"
    Serial.response = response
    with serial_wrapper as wrapper:
        wrapper.wait_for_response(response)


def test_await_acknowledge(serial_wrapper: SerialWrapper, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.wait_for_response")
    message_code = "message_code"
    with serial_wrapper as wrapper:
        wrapper.await_acknowledge(message_code)
        wrapper.wait_for_response.assert_called_once_with(f"ACK:{message_code}")  # type: ignore


def test_wait_for_sbu_ready(serial_wrapper: SerialWrapper, mocker: MockFixture) -> None:
    mocker.patch("base.hardware.sbu.serial_wrapper.SerialWrapper.wait_for_response")
    with serial_wrapper as wrapper:
        wrapper.wait_for_sbu_ready()
        wrapper.wait_for_response.assert_called_once_with("Ready")  # type: ignore
